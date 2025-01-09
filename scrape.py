from scrape_functions import (
    fetch_json_response,
    return_OP,
    return_comments
)

# from llm_talk import chat_with_vllm
from llm_api import chat_with_deepinfra
from llm_talk import send_vllm_request
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


    USE_LOCAL_LLM = os.getenv('USE_LOCAL_LLM', 'false').lower() == 'true'

    if USE_LOCAL_LLM:
        api_key = os.getenv("VLLM_API_KEY")
        result = send_vllm_request(chat_history, api_key, stream=False)
    else:
        try:
            api_key = os.getenv("CLOUD_LLM_API_KEY")
        except:
            api_key = st.secrets['CLOUD_LLM_API_KEY']
        result = chat_with_deepinfra(api_key, chat_history, stream=False)
    return result

