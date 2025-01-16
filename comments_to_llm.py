import os
import yaml
import json
import asyncio
import time
import jsonschema
from jsonschema import ValidationError
from typing import List, Dict, Any
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

# Function to send LLM request and validate schema with retries
def send_llm_request_sync(chat_history, json_schema, max_retries=3):
    retries = 0
    while retries < max_retries:
        # Generate the JSON schema using the LLM
        result_json_schema_string = asyncio.run(send_llm_request(chat_history, json_schema))
        result_json_schema_string = result_json_schema_string.replace("```json", "").replace("```", "").strip()

        try:
            # Convert the schema from string to dictionary
            result_json_schema = json.loads(result_json_schema_string)
        except json.JSONDecodeError as e:
            print(f"Failed to parse schema (invalid JSON): {e}")
            retries += 1
            print(f"Retry {retries} of {max_retries}...")
            continue  # Skip validation and retry
        
        # Validate the generated schema
        if validate_json_schema(result_json_schema):
            return result_json_schema  # Return the valid schema
        
        # If validation fails, increment retry count
        retries += 1
        print(f"Retry {retries} of {max_retries}...")

    print("-----------------")
    print(result_json_schema_string)
    # If max retries reached, raise an exception or return None
    raise ValueError("Failed to generate a valid JSON schema after maximum retries.")

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


    # Print value counts before standardization
    print_dict_value_counts(analysis_results, "Before Standardization")
    
    # --- Standardization of analysis_results ---
    analysis_results = standardize_analysis_results(analysis_results)

    # Print value counts after standardization
    print_dict_value_counts(analysis_results, "After Standardization")

    # Convert individual comment stats to meaningful collective stats here
    # TODO
    # print(analysis_results)
    # print_dict_keys_as_lists(analysis_results)
    raise ValueError

async def process_comment(system_prompt, json_schema, comment, max_tries=3):
    chat_history = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": comment['body']}
    ]
    
    retries = 0
    while retries < max_tries:
        try:
            # Send the request to the LLM
            analysis_result = await send_llm_request(chat_history, json_schema)
            
            # Try to parse the result as JSON
            analysis_result_dict = json.loads(analysis_result)
            
            # Add the comment body to the result
            analysis_result_dict['comment'] = comment['body']
            
            return analysis_result_dict
        
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON for comment: {comment['body'][:50]}... Error: {e}")
            retries += 1
            print(f"Retry {retries} of {max_tries}...")
        except Exception as e:
            print(f"Error processing comment: {comment['body'][:50]}... Error: {e}")
            retries += 1
            print(f"Retry {retries} of {max_tries}...")
    
    # If max retries reached, return None or raise an exception
    print(f"Max retries reached for comment: {comment['body'][:50]}...")
    return None

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

# Function to validate JSON schema after step 1
def validate_json_schema(json_schema):
    try:
        # Validate the schema itself
        jsonschema.Draft7Validator.check_schema(json_schema)
        print("JSON schema is valid.")
        return True
    except ValidationError as e:
        print(f"JSON schema is invalid: {e}")
        return False

def standardize_analysis_results(analysis_results: List[Dict[str, Any]], threshold: float = 0.5):
    """
    Standardizes analysis results by removing keys that are not present in a sufficient proportion of dictionaries.

    Args:
        analysis_results: A list of dictionaries.
        threshold: The minimum proportion of dictionaries that must contain a key for it to be considered common (default: 0.5).
    """
    if not analysis_results:
        return analysis_results

    num_dicts = len(analysis_results)
    key_counts = {}  # Dictionary to store the counts of each key

    # Count the occurrences of each key
    for result in analysis_results:
        for key in result:
            key_counts[key] = key_counts.get(key, 0) + 1

    # Identify keys to be removed
    keys_to_remove = [
        key for key, count in key_counts.items() if count / num_dicts < threshold
    ]

    # Remove the identified keys
    for result in analysis_results:
        for key in keys_to_remove:
            result.pop(key, None)

    return analysis_results

# just for functionality testing (used inside deep_analysis_of_thread)
def print_dict_value_counts(analysis_results: List[Dict[str, Any]], stage: str = "Before Standardization"):
    """
    Prints the number of values in each dictionary of a list and a descriptive message.

    Args:
        analysis_results: A list of dictionaries.
        stage: A string describing the stage (e.g., "Before Standardization", "After Standardization").
    """
    if not analysis_results:
        print(f"{stage}: The analysis_results list is empty.")
        return

    value_counts = [len(d.values()) for d in analysis_results]
    print(f"{stage}: Number of values in each dictionary: {value_counts}")
