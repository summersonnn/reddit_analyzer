from llm_interact import chat_completion, async_chat_completion
from config import prompts
from typing import List, Dict
import json
import asyncio
from scrape_functions import (
    fetch_json_response,
    return_OP,
    return_comments
)
from thread_analysis_functions import (
    get_top_three_comments_by_ef_score,
    get_important_comments
)


def analyze_reddit_thread(url, summary_focus, summary_length, include_eli5, tone):
    """
    Synchronous function that:
      1. Performs preliminary steps sequentially.
      2. Runs individual image API calls concurrently and aggregates the responses.
      3. Inserts the aggregated image analysis into original_post["body"].
      4. Runs the normal text-based API calls (normal summary and optional ELI5) concurrently.
      5. Continues processing synchronously after gathering the results.
    """
    # --- Preliminary sequential work ---
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

    # Assume prompts is defined globally (or passed in)
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

    # --- Fetch thread data ---
    json_response = fetch_json_response(url)
    title, original_post = return_OP(json_response)
    comments = return_comments(json_response)

    # --- Run image API calls (one per image) ---
    image_links = original_post.get("image_link", [])
    if image_links:
        async def run_image_api_calls():
            tasks = []
            for link in image_links:
                # Prepare a separate chat history for each image
                chat_history_image = [{
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {"url": link}
                        },
                        {
                            "type": "text",
                            "text": "Describe what's on this image:"
                        }
                    ]
                }]
                tasks.append(async_chat_completion(chat_history_image, is_image=True))
            return await asyncio.gather(*tasks)

        image_responses = asyncio.run(run_image_api_calls())

        # Combine the image responses into a single analysis string.
        combined_image_analysis = f"There are {len(image_responses)} image(s) in this post. Here are the analyses of these images:\n"
        for idx, resp in enumerate(image_responses, start=1):
            combined_image_analysis += f"\nImage {idx} analysis: {resp}"
        print(combined_image_analysis)
        print("\n")

        # Insert the combined analysis into original_post's "body"
        original_post["body"] = combined_image_analysis
    else:
        image_responses = None

    # --- Update all_data with the updated original_post ---
    all_data = {
        "title": title,
        "original_post": original_post,
        "comments": comments  # list of dicts
    }

    # --- Prepare chat histories for text-based API calls ---
    chat_history_normal = [
        system_message_normal_summary,
        {"role": "user", "content": json.dumps(all_data, indent=4)}
    ]

    if include_eli5:
        chat_history_eli5 = [
            system_message_eli5,
            {"role": "user", "content": json.dumps(all_data, indent=4)}
        ]
    else:
        chat_history_eli5 = None

    # --- Run text-based API calls (normal and ELI5) concurrently ---
    async def run_parallel_text_api_calls():
        tasks = [async_chat_completion(chat_history_normal)]
        if include_eli5 and chat_history_eli5:
            tasks.append(async_chat_completion(chat_history_eli5))
        else:
            tasks.append(asyncio.sleep(0, result=None))
        results = await asyncio.gather(*tasks)
        return results

    result_normal, result_for_5yo = asyncio.run(run_parallel_text_api_calls())

    # --- Further analysis (sequential) ---
    best_comments, important_comments = deep_analysis_of_thread(all_data)

    return result_normal, result_for_5yo, [best_comments, important_comments]

def deep_analysis_of_thread(all_data):
    # First, non-LLM statistics
    a = get_top_three_comments_by_ef_score(all_data['comments'])
    b = get_important_comments(all_data['comments'])

    return (a,b)




