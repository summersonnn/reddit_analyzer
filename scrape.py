from scrape_functions import (
    fetch_json_response,
    return_OP,
    return_comments
)

# from llm_talk import chat_with_vllm
from llm_api import chat_with_deepinfra
import json
import os

def dummy_analyze(url):
    html_response = fetch_html_response_with_selenium(url)
    return html_response

def analyze_reddit_thread(url):
    # Fetch the HTML response using Selenium
    json_response = fetch_json_response(url)
    
    title, original_post = return_OP(json_response)
    comments = return_comments(json_response)
    
    # Combine all scraped parts into a single variable with appropriate tags
    scraped_data = {
        "title": title,
        "original_post": original_post,
        "comments": comments
    }
    
    # System prompt for the LLM
    system_message = {
        "role": "system", 
        "content": """Analyze the entire thread, including the title, original post, comments, and subcomments. Prioritize information from posts with the highest scores, as they indicate strong user agreement. Identify contradictions, biases, and emerging trends within the discussion. Summarize the key points and conclusions based on the most reliable information."""
    }
    
    # Initialize chat history with system message
    chat_history = [system_message]
    
    # Format scraped data as a user message
    user_message = {
        "role": "user", 
        "content": json.dumps(scraped_data, indent=4)  # Convert to JSON string for readability
    }
    
    chat_history.append(user_message)

    # # For local LLM (vLLM)
    # api_key = os.getenv("VLLM_API_KEY")
    # result = chat_with_deepinfra(api_key, chat_history, stream=False, prompt_user=False)

    try:
        api_key = os.getenv("DEEPINFRA_API_KEY")
    except:
        api_key = st.secrets['DEEPINFRA_API_KEY']

    result = chat_with_deepinfra(api_key, chat_history, stream=False, prompt_user=False)
    return result

test_links = [
    "https://www.reddit.com/r/LocalLLaMA/comments/1hdaytv/deepseekaideepseekvl2_hugging_face/",  # blockquotes, image comments
    "https://www.reddit.com/r/LocalLLaMA/comments/1he1rli/qwen_dev_new_stuff_very_soon/", # image post
    "https://www.reddit.com/r/LocalLLaMA/comments/1hdnm40/til_llama_33_can_do_multiple_tool_calls_and_tool/", # gif post
    "https://www.reddit.com/r/LocalLLaMA/comments/1heemer/the_absolute_best_coding_model_that_can_fit_on/", # short thread, fast test
    "https://www.reddit.com/r/LocalLLaMA/comments/1hegcl0/where_do_you_think_the_cutoff_is_for_a_model_to/", # short thread, fast test
    "https://www.reddit.com/r/LocalLLaMA/comments/1hefbq1/coheres_new_model_is_epic/"
]

if __name__ == "__main__":
    analyze_reddit_thread(test_links[-1])
