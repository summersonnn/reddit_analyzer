from llm_interact import chat_completion, async_chat_completion, process_branches_async
from config import prompts
from typing import List, Dict
import json
import asyncio
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

def analyze_reddit_thread(url, summary_focus, summary_length, include_eli5):
    # Define the length-based sentence to add to the prompts
    if summary_length == "Short":
        length_sentence = "Your summary should be concise, ideally between 100 and 200 words, depending on the original thread's length."
    elif summary_length == "Medium":
        length_sentence = "Your summary will be medium sized, preferably in between 250 to 350 words, depending on the original thread's length."
    elif summary_length == "Long":
        length_sentence = "Your summary should be extensive, with a minimum of 400 words unless the original thread is shorter. In that case, match the length of the original thread."
    else:
        length_sentence = ""  # Default case if summary_length is not recognized

    # Construct system messages by merging template with length instructions
    system_message_normal_summary = {
        "role": prompts['summarize_raw_content']['role'],
        "content": prompts['summarize_raw_content']['content'].format(focus=summary_focus) + " " + length_sentence
    }

    system_message_eli5 = {
        "role": prompts['summarize_like_im_5']['role'],
        "content": prompts['summarize_like_im_5']['content'].format(focus=summary_focus) + " " + length_sentence
    }

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


    # 1 ---- Get effective-score weighted overall summary. 
    chat_history = [system_message_normal_summary]
    user_message = {
        "role": "user", 
        "content": json.dumps(all_data, indent=4)  # Convert to JSON string for readability
    }
    chat_history.append(user_message)
    result = chat_completion(chat_history)

    if include_eli5:
        # 2 ---- Get summary for 5 years old
        chat_history = [system_message_eli5]
        user_message = {
            "role": "user", 
            "content": json.dumps(all_data, indent=4)  # Convert to JSON string for readability
        }
        chat_history.append(user_message)
        result_for_5yo = chat_completion(chat_history)
    else:
        result_for_5yo = None

    # 3 --- some notable comments
    a,b,c,d = deep_analysis_of_thread(all_data)

    return result, result_for_5yo, [a,b,c,d]

def deep_analysis_of_thread(all_data):
    # First, non-LLM statistics
    a = get_comment_with_highest_score(all_data['comments'])
    b = get_root_comment_with_highest_score(all_data['comments'])
    c = get_comment_with_most_subcomments(all_data['comments'])
    d = get_comment_with_most_direct_subcomments(all_data['comments'])

    return (a,b,c,d)

def get_linear_branches(all_data):
    # Create the original post (OP) node
    op = {
        'author': all_data['original_post']['author'],
        'body': f"{all_data['title']}\n\n{all_data['original_post']['body']}",
        'score': all_data['original_post']['score'],
        'depth': -1  # Indicates it's the root
    }

    branches = []

    def traverse(current_branch, current_node):
        # Determine children based on current node
        if current_node == op:
            # Children of OP are comments with depth 0
            children = [comment for comment in all_data['comments'] if comment['depth'] == 0]
        else:
            # Children of other nodes are their replies
            children = current_node.get('replies', [])

        if not children:
            # Add the current branch if there are no more children
            branches.append(current_branch)
        else:
            for child in children:
                # Create a copy of the child to avoid modifying the original data
                new_child = child.copy()
                # Check if depth is 0 or higher (i.e., a comment, not OP)
                if new_child['depth'] >= 0:
                    # Calculate effective_score
                    new_child['effective_score'] = new_child['score'] * (new_child['depth'] + 1)
                # Create a new branch by appending the modified child
                new_branch = current_branch.copy()
                new_branch.append(new_child)
                # Recurse with the new_child as the current node
                traverse(new_branch, new_child)

    # Start traversal with the OP as the root
    traverse([op], op)

    # # Each branch contains dictionaries with this structure:
    # {
    # 'author': str,       # Author name (e.g., 'OP_USER' or 'User1')
    # 'body': str,         # Combined title + OP content (for root) or comment text
    # 'depth': int         # -1 for OP, 0+ for comments
    # 'score': int,        # Upvote score (optional)
    # # For comments, also contains:
    # 'replies': list      # Child comments (only in non-leaf nodes)
    # }

    return branches

# For verifying the linear structure
def print_branches_authors(branches):
    """Prints all conversation branches in an author-path format followed by effective scores."""
    for i, branch in enumerate(branches, 1):
        authors = [node['author'] for node in branch]
        # Extract effective scores for comments (depth >= 0)
        effective_scores = []
        for node in branch:
            if 'effective_score' in node:  # Check if the node has an effective score
                effective_scores.append(str(node['effective_score']))
        # Print branch authors and effective scores
        print(f"Branch {i}: {' -> '.join(authors)}")
        print(f"Effective Scores: {' -> '.join(effective_scores) if effective_scores else 'N/A'}")




