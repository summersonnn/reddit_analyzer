import os
import yaml
from llm_api import chat_with_deepinfra
from llm_local import send_vllm_request
from thread_analysis_functions import (
    get_comment_with_highest_score,
    get_root_comment_with_highest_score,
    get_comment_with_most_subcomments,  # this includes root comments as well as sub-comments
    get_comment_with_most_direct_subcomments, # this also includes root as well as sub-comments but only direct subcomments counted
)

def send_llm_request(
    chat_history,
    json_schema
):
    use_local_llm = os.getenv('USE_LOCAL_LLM', 'false').lower() == 'true'
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

# This will create the final result after gathering all informations.
def deep_analysis_of_thread(chat_history, json_schema, comments):
    # First, non-LLM statistics
    a = get_comment_with_highest_score(comments)
    b = get_root_comment_with_highest_score(comments)
    c = get_comment_with_most_subcomments(comments)
    d = get_comment_with_most_direct_subcomments(comments)

    # This will return comment stats in a list. Each object is a dict.
    analysis_results = analyze_comment_by_LLM(chat_history, json_schema, comments)

    # Convert individual comment stats to meaningful collective stats here
    # TODO



# This will return comment stats in a list. Each object is a dict. 
def analyze_comment_by_LLM(chat_history, json_schema, comments):
    # Load the system prompt from the YAML file
    with open('../prompts.yaml', 'r') as file:
        prompts = yaml.safe_load(file)
    
    # Extract the system prompt for comment analysis
    system_prompt = prompts['comment_analysis_system_prompt']

    # Initialize chat history with the system prompt
    chat_history = [{"role": "system", "content": system_prompt}]

    # List to store the analysis results
    analysis_results = []

    # Recursive function to analyze comments and their replies
    def analyze_comment(comment, parent_comment=None):
        # Prepare the chat history for the current comment
        current_chat_history = chat_history.copy()

        # If this is a sub-comment, include the parent comment in the chat history
        if parent_comment:
            parent_context = f"- Parent comment: {parent_comment['body']}\n- Child Comment to analyze: {comment['body']}"
            current_chat_history.append({"role": "user", "content": parent_context})
        else:
            current_chat_history.append({"role": "user", "content": comment['body']})

        # Send the request to the LLM
        analysis_result = send_llm_request(current_chat_history, json_schema)

        # Add the original comment to the analysis result
        analysis_result['comment'] = comment

        # Append the result to the analysis_results list
        analysis_results.append(analysis_result)

        # Recursively analyze replies (sub-comments)
        for reply in comment['replies']:
            analyze_comment(reply, parent_comment=comment)

    # Start analyzing each root comment in the comments list
    for comment in comments:
        analyze_comment(comment)

    return analysis_results

