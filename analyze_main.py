from scrape_functions import (
    fetch_json_response,
    return_OP,
    return_comments
)
from analyze_comments import deep_analysis_of_thread, prompts, send_llm_request_sync
from config import prompts
from helpers import json_schema_to_label_sets
import json

def analyze_reddit_thread(url):
    initial_system_message = prompts['initial_system_message']
    final_system_message = prompts['final_system_message']

    # Fetch the HTML response using Selenium
    json_response = fetch_json_response(url)
    title, original_post = return_OP(json_response)
    comments = return_comments(json_response)

    # Combine all scraped parts into a single variable with appropriate tags
    all_data = {
        "title": title,
        "original_post": original_post,
        "comments": comments  # list of dicts
    }

    # # 1st SECTION. GET JSON SCHEMA FROM LLM
    # chat_history = [initial_system_message]
    # user_message = {
    #     "role": "user", 
    #     "content": json.dumps(all_data, indent=4)  # Convert to JSON string for readability
    # }
    # chat_history.append(user_message)
    # result_json_schema = send_llm_request_sync(chat_history, create_json_schema=True)

    # label_sets = json_schema_to_label_sets(result_json_schema)

    # # # 2nd Section. Analyze each comment one by one with LLM and returned json_schema
    # final_info = deep_analysis_of_thread(label_sets, all_data)

    # # 3rd Section. Get overall summary. No parallelism is needed.
    chat_history = [final_system_message]
    user_message = {
        "role": "user", 
        "content": json.dumps(all_data, indent=4)  # Convert to JSON string for readability
    }
    chat_history.append(user_message)
    result = send_llm_request_sync(chat_history)

    return result
    



