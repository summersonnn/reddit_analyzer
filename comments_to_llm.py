import os
import yaml
import json
import asyncio
import time
from llm_api import chat_with_deepinfra
from llm_local import send_vllm_request
from thread_analysis_functions import (
    get_comment_with_highest_score,
    get_root_comment_with_highest_score,
    get_comment_with_most_subcomments,  # this includes root comments as well as sub-comments
    get_comment_with_most_direct_subcomments, # this also includes root as well as sub-comments but only direct subcomments counted
)

async def send_llm_request(
    chat_history,
    json_schema
):
    use_local_llm = os.getenv('USE_LOCAL_LLM', 'false').lower() == 'true'
    if use_local_llm:
        vllm_api_key = os.getenv("VLLM_API_KEY")
        if not vllm_api_key:
            raise ValueError("VLLM_API_KEY is not set.")
        result = await send_vllm_request(chat_history, vllm_api_key, json_schema)
    else:
        try:
            cloud_llm_api_key = os.getenv("CLOUD_LLM_API_KEY")
        except:
            cloud_llm_api_key = st.secrets['CLOUD_LLM_API_KEY']
        if not cloud_llm_api_key:
            raise ValueError("Cloud LLM API key is not set.")
        result = await chat_with_deepinfra(chat_history, cloud_llm_api_key, json_schema)
    return result

# This will create the final result after gathering all informations.
def deep_analysis_of_thread(json_schema, comments):
    # First, non-LLM statistics
    a = get_comment_with_highest_score(comments)
    b = get_root_comment_with_highest_score(comments)
    c = get_comment_with_most_subcomments(comments)
    d = get_comment_with_most_direct_subcomments(comments)
    
    # Create new event loop if there isn't one
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    start = time.time()
    analysis_results = loop.run_until_complete(analyze_comment_by_LLM(json_schema, comments))
    end = time.time()
    print(end-start)

    # Convert individual comment stats to meaningful collective stats here
    # TODO
    print(analysis_results)
    raise ValueError



# This will return comment stats in a list. Each object is a dict. 
async def analyze_comment_by_LLM(json_schema, comments):
    # Resolve json_schema once at the beginning if it's a coroutine
    if asyncio.iscoroutine(json_schema):
        json_schema = await json_schema
        
    # Load the system prompt from the YAML file
    with open('prompts.yaml', 'r') as file:
        prompts = yaml.safe_load(file)
    print("Starting to analyze comment by comment...")
    
    # Extract the system prompt for comment analysis
    system_prompt = prompts['comment_analysis_system_prompt']

    # List to store the analysis results
    analysis_results = []

    async def process_comment(chat_history, schema, comment):
        # Send the request to the LLM
        analysis_result = await send_llm_request(chat_history, schema)
        
        # Convert the analysis_result (JSON string) to a Python dictionary
        try:
            analysis_result_dict = json.loads(analysis_result)
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON: {e}")
            analysis_result_dict = {"error": "Invalid JSON response from LLM"}

        # Add the original comment to the analysis result
        analysis_result_dict['comment'] = comment
        analysis_results.append(analysis_result_dict)

    async def analyze_comment(comment, parent_comment=None):
        current_chat_history = [{"role": "system", "content": system_prompt}]

        # If this is a sub-comment, include the parent comment in the chat history
        if parent_comment:
            parent_context = f"- Parent comment: {parent_comment['body']}\n- Child Comment to analyze: {comment['body']}"
            current_chat_history.append({"role": "user", "content": parent_context})
        else:
            current_chat_history.append({"role": "user", "content": comment['body']})

        # Process the current comment
        await process_comment(current_chat_history, json_schema, comment)

        # Process all replies in parallel
        if comment['replies']:
            await asyncio.gather(*[analyze_comment(reply, parent_comment=comment) for reply in comment['replies']])

    # Analyze all root comments in parallel
    await asyncio.gather(*[analyze_comment(comment) for comment in comments])

    print("Comment by comment analysis is done.")
    return analysis_results

