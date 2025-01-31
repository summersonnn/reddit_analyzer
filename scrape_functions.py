import requests
import os
import time
import random

def fetch_json_response(url, max_retries=4):
    """
    Fetches the JSON response from the given URL using the requests package.
    Implements a retry mechanism with a random delay if the response is not genuine.
    Uses proxy by default unless USE_LOCAL_LLM is True.
    """
    try:
        # Append .json to the URL if it's not already present
        if not url.endswith('.json'):
            url += '.json'

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
        }
        USE_LOCAL_LLM = os.getenv('USE_LOCAL_LLM', 'false').lower() == 'true'

        for attempt in range(max_retries):
            try:
                # Determine if proxy should be used
                # Use proxy if not using local LLM, or if using local LLM and it's the last attempt
                use_proxy = not USE_LOCAL_LLM or (USE_LOCAL_LLM and attempt == max_retries - 1)
                
                if use_proxy:
                    if USE_LOCAL_LLM and attempt == max_retries - 1:
                        print("Final attempt - trying with proxy...")
                    http_proxy = os.getenv("PROXY_HTTP") 
                    https_proxy = os.getenv("PROXY_HTTPS")
                    proxies = {
                        'http': http_proxy,
                        'https': https_proxy
                    }
                    response = requests.get(url, headers=headers, proxies=proxies)
                else:
                    response = requests.get(url, headers=headers)

                # Raise an exception if the request was unsuccessful
                response.raise_for_status()

                # Convert the response content to a string
                response_text = response.text

                # Check if the response contains the expected strings
                if all(keyword in response_text for keyword in ["author", "replies", "depth"]):
                    # Parse the JSON response only if it's genuine
                    json_data = response.json()
                    return json_data  # type: list
                else:
                    print(response_text)
                    print("Unable to fetch a genuine response...")
                    delay = random.randint(1, 15)
                    time.sleep(delay)
                    continue

            except requests.exceptions.RequestException as e:
                # If using proxy, don't retry after a proxy failure
                if use_proxy:
                    return f"Error: Proxy attempt failed with exception: {e}"
                # Only retry on exception if we're using local LLM and not yet at the proxy attempt
                delay = random.randint(1, 15)
                time.sleep(delay)
                continue

        # If all retries fail, return an error message
        return "Error: Max retries reached. Unable to fetch a genuine JSON response."

    except Exception as e:
        return f"Error fetching the JSON response: {e}"


def return_OP(json_data):
    """
    Extracts the title and content of the original post from the JSON response.
    Formats the content similar to a comment structure.

    Args:
        json_data (dict): The JSON response from the API.

    Returns:
        tuple: A tuple containing (title, content_dict).
               content_dict is a dictionary representing the original post's content in a format similar to comments.
    """
    try:
        # Navigate through the JSON structure (same as before)
        first_element = json_data[0]
        first_child = first_element['data']['children'][0]
        data = first_child['data']

        # Extract title and content (same as before)
        title = data.get('title', '')
        content = data.get('selftext', '')

        # Create the content dictionary (similar to comment structure)
        content_dict = {
            'author': data.get('author', ''),  # Author of the post
            'score': data.get('score', 0),    # Score of the post
            'ef_score': data.get('score', 0)/2, 
            'body': content,                      # Content of the post
            'type': data.get('link_flair_text', '')	,
            'image_link': data.get('url', ''),  # only if it's image post (check the extension)
        }

        return (title, content_dict)

    except (KeyError, IndexError, TypeError) as e:
        return (None, None)

def return_comments(json_data):
    """
    Scrapes the comments section from the JSON response, preserving the hierarchy (nesting).
    Uses a helper function to extract and format quoted parts in the comment body.

    Args:
        json_data (list): The JSON response from the API.

    Returns:
        list: A list of dictionaries, each representing a comment with its author, score, body, depth, and replies.
    """
    def extract_quotes(body):
        """
        Extracts and formats quoted parts in the comment body.

        Args:
            body (str): The comment body.

        Returns:
            str: The formatted comment body with quoted parts marked.
        """
        if "&gt;" not in body:
            return body  # Return the body as is if there are no quotes

        # Split the body into lines
        lines = body.split("\n")
        formatted_body = ""
        for line in lines:
            if line.strip().startswith("&gt;"):
                # Extract the quoted part (remove "&gt;" and leading/trailing spaces)
                quoted_part = line.strip()[4:].strip()
                formatted_body += f"Quoted Part: '{quoted_part}'\n"
            else:
                # Add normal lines as they are
                formatted_body += f"{line}\n"
        return formatted_body.strip()  # Remove trailing newline

    def scrape_comment(comment_data, depth=0):
        """
        Recursively scrapes a comment and its replies.

        Args:
            comment_data (dict): The comment data dictionary.
            depth (int): The depth of the comment in the hierarchy.

        Returns:
            dict: A dictionary representing the comment and its replies.
        """
        # Extract the comment's data
        comment = comment_data.get('data', {})
        if not comment:  # Skip if no data is found
            return None

        # Format the comment body (extract quotes if any)
        body = extract_quotes(comment.get('body', ''))

        # Create the comment dictionary
        comment_dict = {
            'author': comment.get('author', ''),  # Author of the comment
            'score': comment.get('score', 0),     # Score of the comment
            'ef_score': comment.get('score', 0) * (depth+1),
            'body': body,                         # Formatted content of the comment
            'depth': depth,                       # Depth of the comment in the hierarchy
            'replies': []                         # Initialize an empty list for replies
        }

        # Check if the comment has replies
        if 'replies' in comment and comment['replies']:  # 'replies' contains subcomments
            replies_data = comment['replies']['data']['children']
            for reply in replies_data:
                # Recursively scrape the reply
                reply_dict = scrape_comment(reply, depth + 1)
                if reply_dict:  # Add the reply if it exists
                    comment_dict['replies'].append(reply_dict)

        return comment_dict

    # Get the comments section (2nd element in the JSON response)
    sec_element = json_data[1]
    comments_section = sec_element['data']['children']
    comments = []

    # Iterate through each root comment
    for comment in comments_section:
        # Scrape the root comment and its replies
        comment_dict = scrape_comment(comment, depth=0)
        if comment_dict:  # Add the comment if it exists
            comments.append(comment_dict)

    return comments

def prettify_comments(comments):
    """
    Formats the comments in a tree-like structure, using separators and arrows to show the hierarchy.

    Args:
        comments (list): A list of dictionaries representing comments and their replies.

    Returns:
        str: A formatted string representing the comments in a tree-like structure.
    """
    def format_comment(comment, indent=0, is_reply=False):
        """
        Recursively formats a comment and its replies in a tree-like structure.

        Args:
            comment (dict): The comment dictionary.
            indent (int): The current indentation level.
            is_reply (bool): Whether the comment is a reply.

        Returns:
            str: A formatted string representing the comment and its replies.
        """
        # Add a separator for top-level comments
        output = ""
        if not is_reply:
            output += "=" * 50 + "\n"

        # Add indentation and arrow prefix for replies
        prefix = "    " * indent  # 4 spaces for each level of indentation
        arrow = "└─► " if is_reply else ""  # Arrow for replies

        # Format the comment
        output += f"{prefix}{arrow}{comment['author']} | {comment['body']} | Score: {comment['score']}\n"

        # Format the replies (if any)
        if comment['replies']:
            for reply in comment['replies']:
                output += format_comment(reply, indent + 1, is_reply=True)

        return output

    # Format all comments
    formatted_comments = ""
    for comment in comments:
        formatted_comments += format_comment(comment)

    return formatted_comments


