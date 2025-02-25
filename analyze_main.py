import os
import random
import time
import json
import asyncio
from typing import List, Dict

from config import prompts
from llm_interact import async_chat_completion
from scrape_functions import (
    fetch_json_response,
    return_OP,
    return_comments
)
from thread_analysis_functions import (
    get_top_comments_by_ef_score,
    get_important_comments
)
from try_html_summary import generate_summary

def fetch_thread_data(url: str) -> Dict:
    max_retries = 3
    is_local = os.getenv('LOCAL_RUN', 'false').lower() == 'true'

    for attempt in range(max_retries):
        try:
            use_proxy = not is_local or (is_local and attempt == max_retries - 1)
            if is_local and attempt == max_retries - 1:
                print("Final attempt - trying with proxy...")

            json_response = fetch_json_response(url, use_proxy=use_proxy)

            # Check if the response is an error message
            if isinstance(json_response, str):
                raise Exception(json_response)

            title, original_post = return_OP(json_response)
            # print(title)
            comments = return_comments(json_response)

            all_data = {
                "title": title,
                "original_post": original_post,
                "comments": comments,
                'url': None
            }
            return all_data

        except Exception as e:
            print(f"Error on attempt {attempt + 1}: {e}")
            if attempt < max_retries - 1:
                delay = random.randint(1, 15)
                time.sleep(delay)
    
    all_data = {
        "title": None,
        "original_post": None,
        "comments": None,
        "url:": url
    }
    return all_data


def analyze_reddit_thread(all_data, summary_focus, summary_length, tone, include_eli5, analyze_image, search_external, max_comments, include_normal_summary=True):
    """
    Analyzes a Reddit thread.

    Args:
        all_data: Content of the Reddit thread.
        summary_focus: Focus of the summary.
        summary_length: Length of the summary.
        tone: Tone of the summary.
        include_eli5: Whether to include an ELI5 summary.
        analyze_image: Whether to analyze images.
        search_external: Whether to search external links.
        include_normal_summary: Whether to include a normal summary (default: True).
    """
    if summary_length == "Short":
        length_sentence = ("Your summary should be concise, ideally between 100 and 200 words, "
                           "depending on the original thread's length.")
    elif summary_length == "Medium":
        length_sentence = ("Your summary will be medium sized, preferably between 250 to 350 words, "
                           "depending on the original thread's length.")
    elif summary_length == "Long":
        length_sentence = ("Your summary should be extensive, with a minimum of 400 words unless the "
                           "original thread is shorter. In that case, match the length of the original thread.")
    else:
        length_sentence = ""

    tone_prompt = prompts[tone]['content'] if tone in prompts else ""

    system_message_normal_summary = {
        "role": prompts['summarize_raw_content']['role'],
        "content": prompts['summarize_raw_content']['content'].format(focus=summary_focus) +
                   " " + length_sentence + "\nConform to the following tone and imitate it: " + tone_prompt
    }

    system_message_eli5 = {
        "role": prompts['summarize_like_im_5']['role'],
        "content": prompts['summarize_like_im_5']['content'].format(focus=summary_focus) +
                   " " + length_sentence
    }

    OP = all_data['original_post']
    image_links = OP.get("image_link", [])
    extra_links = OP.get("extra_content_link", [])
    image_responses, link_summaries = process_media_content(image_links, extra_links, analyze_image, search_external)

    media_analysis = ""
    if image_responses:
        media_analysis += f"\nThere are {len(image_responses)} image(s) in this post. Here are the analyses of these images:\n"
        for idx, resp in enumerate(image_responses, start=1):
            media_analysis += f"\nImage {idx} analysis: {resp}"
    if link_summaries:
        media_analysis += f"\n\nThere are {len(link_summaries)} external link(s) in this post. Here are their summaries:\n"
        for idx, summary in enumerate(link_summaries, start=1):
            media_analysis += f"\nLink {idx} summary: {summary}"
    if media_analysis:
        OP["body"] += "\n" + media_analysis

    # --- Prepare chat histories - based on include_normal_summary and include_eli5 ---
    chat_history_normal = None
    chat_history_eli5 = None

    if include_normal_summary:
        chat_history_normal = [
            system_message_normal_summary,
            {"role": "user", "content": json.dumps(all_data, indent=4)}
        ]
    if include_eli5:
        chat_history_eli5 = [
            system_message_eli5,
            {"role": "user", "content": json.dumps(all_data, indent=4)}
        ]

    async def run_parallel_text_api_calls():
        tasks = []
        if chat_history_normal:
            tasks.append(async_chat_completion(chat_history_normal))
        else:
             tasks.append(asyncio.sleep(0, result=None))
        if chat_history_eli5:
            tasks.append(async_chat_completion(chat_history_eli5))
        else:
            tasks.append(asyncio.sleep(0, result=None))

        results = await asyncio.gather(*tasks)
        return results

    result_normal, result_for_5yo = asyncio.run(run_parallel_text_api_calls())

    result_normal = result_normal if result_normal is not None else ""  # Ensure string return
    result_for_5yo = result_for_5yo if result_for_5yo is not None else None

    best_comments, important_comments = deep_analysis_of_thread(all_data, max_comments)
    return result_normal, result_for_5yo, [best_comments, important_comments]

def deep_analysis_of_thread(all_data, max_comments):
    # First, non-LLM statistics
    a = get_top_comments_by_ef_score(all_data['comments'], limit=max_comments)
    b = get_important_comments(all_data['comments'], limit=max_comments)

    return (a,b)

def process_media_content(image_links, extra_content_links, analyze_image=True, search_external=True):
    """Process images and extra content links concurrently and return aggregated responses"""
    async def run_media_api_calls(img_links, content_links):
        tasks = []      
        # Add image analysis tasks
        if img_links and analyze_image:
            for link in img_links:
                chat_history_image = [{
                    "role": "user", 
                    "content": [
                        {"type": "image_url", "image_url": {"url": link}},
                        {"type": "text", "text": "Describe what's on this image:"}
                    ]
                }]
                tasks.append(async_chat_completion(chat_history_image, is_image=True))
        
        # Add link summary tasks  
        if content_links and search_external:
            for link in content_links:
                tasks.append(asyncio.create_task(
                    generate_summary_async(link, word_count=200)
                ))
                
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Split results into image and link summaries
        num_images = len(img_links) if img_links else 0
        image_results = results[:num_images]
        link_results = results[num_images:]
        
        return image_results, link_results

    if not image_links and not extra_content_links:
        return None, None
        
    image_responses, link_summaries = asyncio.run(
        run_media_api_calls(image_links, extra_content_links)
    )
    
    return image_responses, link_summaries

async def generate_summary_async(url: str, word_count: int = 200) -> str:
    try:
        return await asyncio.to_thread(generate_summary, url, word_count)
    except Exception as e:
        print(f"Error generating summary for {url}: {e}")
        return f"Failed to generate summary: {str(e)}"







