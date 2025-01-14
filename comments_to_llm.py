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

try:
    # Try to load from the current directory
    with open('prompts.yaml', 'r') as file:
        prompts = yaml.safe_load(file)
except FileNotFoundError:
    try:
        # If the first attempt fails, try to load from the parent directory
        with open('../prompts.yaml', 'r') as file:
            prompts = yaml.safe_load(file)
    except FileNotFoundError:
        # If both attempts fail, raise a custom error or handle it as needed
        raise FileNotFoundError("The prompts.yaml file was not found in the current directory or the parent directory.")

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
        result = await chat_with_deepinfra(chat_history, cloud_llm_api_key, prompts, json_schema)
    return result

def send_llm_request_sync(chat_history, json_schema):
    return asyncio.run(send_llm_request(chat_history, json_schema))

# This will create the final result after gathering all informations.
def deep_analysis_of_thread(json_schema, comments):
    # First, non-LLM statistics
    a = get_comment_with_highest_score(comments)
    b = get_root_comment_with_highest_score(comments)
    c = get_comment_with_most_subcomments(comments)
    d = get_comment_with_most_direct_subcomments(comments)

    # Run the asynchronous analysis in a synchronous context
    start = time.time()
    analysis_results = asyncio.run(analyze_comment_by_LLM(json_schema, comments))
    end = time.time()
    print(f"Analysis took {end - start} seconds")

    # Convert individual comment stats to meaningful collective stats here
    # TODO
    # print(analysis_results)
    # print_dict_keys_as_lists(analysis_results)
    raise ValueError

async def process_comment(system_prompt, json_schema, comment):
    chat_history = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": comment['body']}
    ]
    
    try:
        analysis_result = await send_llm_request(chat_history, json_schema)
        analysis_result_dict = json.loads(analysis_result)
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON for comment: {comment['body'][:50]}... Error: {e}")
        return None
    except Exception as e:
        print(f"Error processing comment: {comment['body'][:50]}... Error: {e}")
        return None

    analysis_result_dict['comment'] = comment['body']
    return analysis_result_dict

async def analyze_comment_by_LLM(json_schema, comments):
    if asyncio.iscoroutine(json_schema):
        json_schema = await json_schema

    print("Starting to analyze comment by comment...")
    system_prompt = prompts['comment_analysis_system_prompt']
    
    async def analyze_comment_tree(comment):
        results = []
        
        # Process current comment
        result = await process_comment(system_prompt, json_schema, comment)
        if result:
            results.append(result)
        
        # Process replies
        if comment['replies']:
            reply_results = await asyncio.gather(
                *[analyze_comment_tree(reply) for reply in comment['replies']]
            )
            results.extend([item for sublist in reply_results for item in sublist])
            
        return results

    # Process all root comments in parallel
    all_results = await asyncio.gather(
        *[analyze_comment_tree(comment) for comment in comments]
    )
    
    # Flatten results
    analysis_results = [item for sublist in all_results for item in sublist]
    
    print("Comment by comment analysis is done.")
    return analysis_results

# This is just for testing purposes. To make sure every dict in the list have same keys. If not, spot the faulty dict.
def print_dict_keys_as_lists(list_of_dicts):
    # Create a list of lists containing the keys of each dictionary
    list_of_keys = [list(dictionary.keys()) for dictionary in list_of_dicts]
    
    # Print each inner list on a separate line
    for keys in list_of_keys:
        print(keys)
