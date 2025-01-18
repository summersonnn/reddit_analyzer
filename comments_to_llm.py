import os
import yaml
import json
import asyncio
import time
import jsonschema
from jsonschema import ValidationError
from typing import List, Dict, Any
from llm_common import chat_completion
from collections import defaultdict
from thread_analysis_functions import (
    get_comment_with_highest_score,
    get_root_comment_with_highest_score,
    get_comment_with_most_subcomments,  # this includes root comments as well as sub-comments
    get_comment_with_most_direct_subcomments, # this also includes root as well as sub-comments but only direct subcomments counted
)
from typing import Optional, Dict, List, Union

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
    chat_history: List[Dict[str, str]],
    json_schema: Optional[Dict] = None,
) -> str:
    """
    Sends a request to the appropriate LLM service based on environment configuration.
    
    Args:
        chat_history: List of message dictionaries with 'role' and 'content'
        json_schema: Optional JSON schema for structured output
    
    Returns:
        str: The model's response
    """
    # Use the unified chat completion function
    result = await chat_completion(
        chat_history=chat_history,
        json_schema=json_schema
    )
    return result

# Function to send LLM request and validate schema with (step 1) retries (also used in step 3, summarizing)
def send_llm_request_sync(chat_history, max_retries=3, create_json_schema=False):
    # If not for json_schema creation, simply redirect it to send_llm_request
    if not create_json_schema:
        return asyncio.run(send_llm_request(chat_history))

    # Otherwise, proceed with the retry mechanism and schema validation
    retries = 0
    while retries < max_retries:
        # Generate the JSON schema using the LLM
        result_json_schema_string = asyncio.run(send_llm_request(chat_history))
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
            result_json_schema = add_none_to_enum(result_json_schema)
            result_json_schema = remove_array_type_elements(result_json_schema) # will be removed in the future
            print("-----------Here is the json schema:")
            prettified_json = json.dumps(result_json_schema, indent=4)
            print(prettified_json)
            return result_json_schema  # Return the valid schema
        
        # If validation fails, increment retry count
        retries += 1
        print(f"Retry {retries} of {max_retries}...")

    print("-----------------")
    print(result_json_schema_string)
    # If max retries reached, raise an exception or return None
    raise ValueError("Failed to generate a valid JSON schema after maximum retries.")

# This will create the final result after gathering all informations.
def deep_analysis_of_thread(json_schema, all_data):
    # First, non-LLM statistics
    a = get_comment_with_highest_score(all_data['comments'])
    b = get_root_comment_with_highest_score(all_data['comments'])
    c = get_comment_with_most_subcomments(all_data['comments'])
    d = get_comment_with_most_direct_subcomments(all_data['comments'])

    # Run the asynchronous analysis in a synchronous context
    analysis_results = asyncio.run(analyze_comment_by_LLM(json_schema, all_data))

    # Print value counts before standardization
    print_dict_value_counts(analysis_results, "Before Standardization")
    
    # --- Standardization of analysis_results ---
    analysis_results = standardize_analysis_results(analysis_results)

    # Print value counts after standardization
    print_dict_value_counts(analysis_results, "After Standardization")

    # print(analysis_results[0])
    # print("--------")
    # print(analysis_results[1])

    # Scores are not taken into account
    raw_final_stats = aggregate_analysis_results(analysis_results)
    scored_final_stats = aggregate_analysis_results_with_scores(analysis_results)
    
    print(raw_final_stats)
    print()
    print(scored_final_stats)

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
            analysis_result_dict['comment'] = comment
            print(analysis_result_dict)
            print()
            
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

async def analyze_comment_by_LLM(json_schema, all_data):
    comments = all_data['comments']
    op = all_data['original_post']

    if asyncio.iscoroutine(json_schema):
        json_schema = await json_schema

    print("Starting to analyze comment by comment...")
    system_prompt = prompts['comment_analysis_system_prompt']  # Assuming you have this defined

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

    async def analyze_op(op_text):
      """Analyzes the original post (OP) using the same logic as comments."""
      result = await process_comment(system_prompt, json_schema, op)  # Treat OP as a comment with no replies for consistency
      return result

    # Process OP
    op_result = await analyze_op(op)
    if op_result:
        analysis_results = [op_result]
    else:
        analysis_results = []

    # Process all root comments in parallel
    all_results = await asyncio.gather(
        *[analyze_comment_tree(comment) for comment in comments]
    )

    # Flatten all results
    analysis_results.extend([item for sublist in all_results for item in sublist])

    print("Comment by comment and OP analysis is done.")
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

def add_none_to_enum(json_data):
    """
    Adds "None" to the enum property of keys in a JSON object if it's not already present.
    Correctly handles nested "properties" objects.

    Args:
        json_data: A dictionary representing the JSON data.

    Returns:
        A new dictionary with "None" added to the enum lists where appropriate.
    """

    if not isinstance(json_data, dict):
        return json_data

    new_json_data = json_data.copy()

    for key, value in new_json_data.items():
        if isinstance(value, dict):
            if "enum" in value:
                if "None" not in value["enum"]:
                    value["enum"].append("None")
            elif "properties" in value:  # Handle nested properties
                new_json_data[key]["properties"] = add_none_to_enum(value["properties"])
            else:
                new_json_data[key] = add_none_to_enum(value)  # Recurse for other nested dicts

    return new_json_data



def aggregate_analysis_results(analysis_results):
    """
    Aggregates the analysis results, calculating the frequency of each value for each key,
    while ensuring that values from the same author are counted only once.
    This version assumes no value can be a list.

    Args:
        analysis_results: A list of dictionaries, where each dictionary represents the
                          analysis of a single comment. Each dictionary is expected
                          to have a "comment" key, which is another dictionary containing
                          at least an "author" key.

    Returns:
        A dictionary where keys are the keys from the analysis results, and values are
        dictionaries mapping unique values to their frequencies, considering author uniqueness.
    """

    aggregated_stats = defaultdict(lambda: defaultdict(int))
    author_values = defaultdict(lambda: defaultdict(set))  # Track values seen per author per key

    for result in analysis_results:
        author = result['comment']['author']
        for key, value in result.items():
            if key == 'comment':  # Skip the 'comment' key itself
                continue

            # No need to check for list type anymore
            if value not in author_values[key][author]:
                aggregated_stats[key][value] += 1
                author_values[key][author].add(value)

    return aggregated_stats


def aggregate_analysis_results_with_scores(analysis_results):
    """
    Aggregates the analysis results, calculating a weighted frequency for each value,
    while considering comment scores and ensuring that only the highest-scoring value
    from the same author is counted for each key.

    The weighted frequency is calculated as:
        frequency * (comment_score / 2)

    Args:
        analysis_results: A list of dictionaries, where each dictionary represents the
                          analysis of a single comment. Each dictionary is expected
                          to have a "comment" key, which is another dictionary containing
                          at least "author" and "score" keys.

    Returns:
        A dictionary where keys are the keys from the analysis results, and values are
        dictionaries mapping unique values to their weighted frequencies, considering
        author uniqueness and comment scores.
    """

    aggregated_stats = defaultdict(lambda: defaultdict(float))  # Use float for weighted frequency
    author_values = defaultdict(lambda: defaultdict(dict))  # Track value and score per author per key

    for result in analysis_results:
        author = result['comment']['author']
        score = result['comment']['score']

        for key, value in result.items():
            if key == 'comment':
                continue

            # Check if value exists for author and key
            if value in author_values[key][author]:
                # Compare scores and update if current score is higher
                if score > author_values[key][author][value]:
                    # Decrement the old score's contribution (remove the previous count)
                    aggregated_stats[key][value] -= author_values[key][author][value]
                    # Add the new score's contribution
                    aggregated_stats[key][value] += score
                    # Update the tracked score for this author, key, and value
                    author_values[key][author][value] = score
            else:
                # New value for this author and key
                aggregated_stats[key][value] += score / 2
                author_values[key][author][value] = score

    return aggregated_stats

# Just for now. We will allow arrays in the json in the future.
def remove_array_type_elements(json_data):
    """
    Removes elements with a type of "array" from a JSON schema.

    Args:
        json_data: The JSON schema as a dictionary.

    Returns:
        A new dictionary with array-type elements removed.
    """

    if not isinstance(json_data, dict):
        return json_data

    new_json_data = {}
    for key, value in json_data.items():
        if isinstance(value, dict):
            if "type" in value and value["type"] == "array":
                continue  # Skip elements with type "array"
            else:
                new_json_data[key] = remove_array_type_elements(value)
        elif isinstance(value, list):
             new_json_data[key] = [remove_array_type_elements(item) for item in value]
        else:
            new_json_data[key] = value

    return new_json_data
