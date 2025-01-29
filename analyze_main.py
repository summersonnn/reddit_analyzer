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

    # Get overall summary. 
    chat_history = [summarize_system_message]
    user_message = {
        "role": "user", 
        "content": json.dumps(all_data, indent=4)  # Convert to JSON string for readability
    }
    chat_history.append(user_message)
    result = chat_completion(chat_history)
    # a,b,c,d = deep_analysis_of_thread(all_data)

    # # Identify and extract linear branches within the tree structure. 
    # linear_branches = get_linear_branches(all_data)
    # print_branches_authors(linear_branches)
    # raise ValueError

    return result

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
        'body': f"{all_data['title']}\n\n{all_data['original_post']}",
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
                new_branch = current_branch.copy()
                new_branch.append(child)
                traverse(new_branch, child)

    # Start traversal with the OP as the root
    traverse([op], op)

    return branches

# For verifying the linear structure
def print_branches_authors(branches):
    """Prints all conversation branches in an author-path format"""
    for i, branch in enumerate(branches, 1):
        authors = [node['author'] for node in branch]
        print(f"Branch {i}: {' -> '.join(authors)}")




