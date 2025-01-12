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
from llm_api import chat_with_deepinfra
from llm_local import send_vllm_request
import json
import os
import yaml

with open('../prompts.yaml', 'r') as file:
    prompts = yaml.safe_load(file)

initial_system_message = prompts['initial_system_message']
final_system_message = prompts['final_system_message']

def dummy_analyze(url):
    html_response = fetch_html_response_with_selenium(url)
    return html_response

def analyze_reddit_thread(url):
    # Fetch the HTML response using Selenium
    json_response = fetch_json_response(url)
    
    title, original_post = return_OP(json_response)
    comments = return_comments(json_response)
    USE_LOCAL_LLM = os.getenv('USE_LOCAL_LLM', 'false').lower() == 'true'

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
    all_data = {
        "title": title,
        "original_post": original_post,
        "comments": comments
    }

    # # 1st SECTION. GET JSON SCHEMA FROM LLM
    # chat_history = [initial_system_message]
    # user_message = {
    #     "role": "user", 
    #     "content": json.dumps(all_data, indent=4)  # Convert to JSON string for readability
    # }
    # chat_history.append(user_message)
    # result = send_llm_request(USE_LOCAL_LLM, chat_history, None)
    

    # 2nd Section. Analyze each comment one by one with LLM and returned json_schema
    # TO DO

    # 3rd Section. Get overall summary.
    chat_history = [final_system_message]
    user_message = {
        "role": "user", 
        "content": json.dumps(all_data, indent=4)  # Convert to JSON string for readability
    }
    chat_history.append(user_message)
    result = send_llm_request(USE_LOCAL_LLM, chat_history, None)

    return result
    

def send_llm_request(
    use_local_llm,
    chat_history,
    json_schema
):
    if use_local_llm:
        vllm_api_key = os.getenv("VLLM_API_KEY")
        if not vllm_api_key:
            raise ValueError("VLLM_API_KEY is not set.")
        result = send_vllm_request(chat_history, vllm_api_key, json_schema)
    else:
        try:
            cloud_llm_api_key = os.getenv("CLOUD_LLM_API_KEY")
        except:
            cloud_llm_api_key = st.secrets['CLOUD_LLM_API_KEY']
        if not cloud_llm_api_key:
            raise ValueError("Cloud LLM API key is not set.")
        result = chat_with_deepinfra(chat_history, cloud_llm_api_key, json_schema)
    return result

