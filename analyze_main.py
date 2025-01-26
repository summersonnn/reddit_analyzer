from llm_interact import chat_completion
from config import prompts
import json
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

def analyze_reddit_thread(url):
    summarize_system_message = prompts['summarize_system_message']

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

    # Get overall summary. No parallelism is needed.
    chat_history = [summarize_system_message]
    user_message = {
        "role": "user", 
        "content": json.dumps(all_data, indent=4)  # Convert to JSON string for readability
    }
    chat_history.append(user_message)
    a,b,c,d = deep_analysis_of_thread(all_data)
    result = chat_completion(chat_history)

    return result

# This will create the final result after gathering all informations from comments and op
def deep_analysis_of_thread(all_data):
    # First, non-LLM statistics
    a = get_comment_with_highest_score(all_data['comments'])
    b = get_root_comment_with_highest_score(all_data['comments'])
    c = get_comment_with_most_subcomments(all_data['comments'])
    d = get_comment_with_most_direct_subcomments(all_data['comments'])

    return (a,b,c,d)


