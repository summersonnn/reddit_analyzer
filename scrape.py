from scrape_functions import (
    fetch_json_response,
    return_OP,
    return_comments
)
from comments_to_llm import deep_analysis_of_thread, send_llm_request
import json
import yaml

with open('prompts.yaml', 'r') as file:
    prompts = yaml.safe_load(file)

initial_system_message = prompts['initial_system_message']
final_system_message = prompts['final_system_message']

def dummy_analyze(url):
    html_response = fetch_html_response_with_selenium(url)
    return html_response

async def analyze_reddit_thread(url):
    # Fetch the HTML response using Selenium
    json_response = fetch_json_response(url)
    
    title, original_post = return_OP(json_response)
    comments = return_comments(json_response)

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
    # result_json_schema = send_llm_request(chat_history, None)

    # # 2nd Section. Analyze each comment one by one with LLM and returned json_schema
    # # This does not call send_llm_request directly because there is a preprocessing step first.
    # final_info = deep_analysis_of_thread(result_json_schema, comments)

    # # 3rd Section. Get overall summary.
    chat_history = [final_system_message]
    user_message = {
        "role": "user", 
        "content": json.dumps(all_data, indent=4)  # Convert to JSON string for readability
    }
    chat_history.append(user_message)
    result = await send_llm_request(chat_history, None)

    return result
    



