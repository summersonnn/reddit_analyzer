import os
import json
import asyncio
from typing import List, Dict, Any
from llm_common import chat_completion
from collections import defaultdict
from thread_analysis_functions import (
    get_comment_with_highest_score,
    get_root_comment_with_highest_score,
    get_comment_with_most_subcomments,  # this includes root comments as well as sub-comments
    get_comment_with_most_direct_subcomments, # this also includes root as well as sub-comments but only direct subcomments counted
)
from helpers import print_dict_keys_as_lists, validate_json_schema, print_dict_value_counts, add_none_to_enum, remove_array_type_elements
from config import prompts
from bart_client import analyze_comments_by_bart

# Function to send LLM request and validate schema with (step 1) retries (also used in step 3, summarizing)
def send_llm_request_sync(chat_history, max_retries=3, create_json_schema=False):
    # If not for json_schema creation, simply redirect it to chat_completion
    if not create_json_schema:
        return asyncio.run(chat_completion(chat_history))

    # Otherwise, proceed with the retry mechanism and schema validation
    retries = 0
    while retries < max_retries:
        # Generate the JSON schema using the LLM
        result_json_schema_string = asyncio.run(chat_completion(chat_history))
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

# This will create the final result after gathering all informations from comments and op
def deep_analysis_of_thread(label_sets, all_data):
    # First, non-LLM statistics
    a = get_comment_with_highest_score(all_data['comments'])
    b = get_root_comment_with_highest_score(all_data['comments'])
    c = get_comment_with_most_subcomments(all_data['comments'])
    d = get_comment_with_most_direct_subcomments(all_data['comments'])

    # Run the asynchronous analysis in a synchronous context
    analysis_results = asyncio.run(analyze_comments_by_bart(label_sets, all_data))

    # Scores are not taken into account
    raw_final_stats = aggregate_analysis_results(analysis_results)
    scored_final_stats = aggregate_analysis_results_with_scores(analysis_results)
    
    print(raw_final_stats)
    print()
    print(scored_final_stats)

    raise ValueError

def aggregate_analysis_results(processed_results):
    """
    Aggregates the analysis results, calculating the frequency of each label for each category,
    while ensuring that labels from the same author are counted only once within each category.

    Args:
        processed_results: A dictionary where keys are categories and values are lists of
                           dictionaries, each representing a comment with its assigned label
                           and author information.

    Returns:
        A dictionary where keys are categories, and values are dictionaries mapping
        unique labels to their frequencies within that category, considering author uniqueness.
    """

    aggregated_stats = defaultdict(lambda: defaultdict(int))
    author_labels = defaultdict(lambda: defaultdict(set))  # Track labels seen per author per category

    for category, comments in processed_results.items():
        for comment in comments:
            author = comment['author']
            label = comment['label']

            if label not in author_labels[category][author]:
                aggregated_stats[category][label] += 1
                author_labels[category][author].add(label)

    return aggregated_stats

def aggregate_analysis_results_with_scores(processed_results):
    """
    Aggregates the analysis results, calculating a weighted frequency for each label within each category,
    while considering comment scores and ensuring that only the highest-scoring label
    from the same author is counted for each category.

    The weighted frequency is calculated as:
        frequency * (comment_score / 2)

    Args:
        processed_results: A dictionary where keys are categories and values are lists of
                           dictionaries, each representing a comment with its assigned label,
                           author, and score information.

    Returns:
        A dictionary where keys are categories, and values are dictionaries mapping unique
        labels to their weighted frequencies within that category, considering author
        uniqueness and comment scores.
    """

    aggregated_stats = defaultdict(lambda: defaultdict(float))  # Use float for weighted frequency
    author_labels = defaultdict(lambda: defaultdict(dict))  # Track label and score per author per category

    for category, comments in processed_results.items():
        for comment in comments:
            author = comment['author']
            score = comment['score']
            label = comment['label']

            if label in author_labels[category][author]:
                if score > author_labels[category][author][label]:
                    aggregated_stats[category][label] -= author_labels[category][author][label] / 2
                    aggregated_stats[category][label] += score / 2
                    author_labels[category][author][label] = score
            else:
                aggregated_stats[category][label] += score / 2
                author_labels[category][author][label] = score

    return aggregated_stats
