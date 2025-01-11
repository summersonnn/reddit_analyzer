from scrape_functions import (
    fetch_json_response,
    return_OP,
    return_comments
)
from thread_analysis_functions import (
    get_comment_with_highest_score,
    get_root_comment_with_highest_score,
    get_comment_with_most_subcomments,  # this includes root comments as well as sub-comments
    get_comment_with_most_direct_subcomments, # this also includes root as well as sub-comments but only direct subcomments counted
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

    a = get_comment_with_highest_score(comments)
    b = get_root_comment_with_highest_score(comments)
    c = get_comment_with_most_subcomments(comments)
    d = get_comment_with_most_direct_subcomments(comments)

    # # This code block is just for testing on the fly
    # print(a)
    # print()  # Prints a blank line
    # print(b)
    # print()  # Prints a blank line
    # print(c)
    # print()  # Prints a blank line
    # print(d)
    # raise ValueError

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
        json_schema = {
        "type": "object",
            "properties": {
                "comprehensive_summary": {"type": "string"},
            },
            "required": ["comprehensive_summary"]
        }
        result = send_vllm_request(chat_history, api_key, json_schema, stream=False)
    else:
        try:
            api_key = os.getenv("CLOUD_LLM_API_KEY")
        except:
            api_key = st.secrets['CLOUD_LLM_API_KEY']
        result = chat_with_deepinfra(api_key, chat_history, stream=False)
    return result

