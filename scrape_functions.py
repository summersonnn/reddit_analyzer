import requests
import re
import os

def fetch_json_response(url: str, use_proxy: bool = False) -> dict or str:
    """
    Fetches the JSON response from the given URL using the requests package.
    Uses proxy if specified.
    """
    if not url.endswith('.json'):
        url += '.json'

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
    }

    proxies = None
    if use_proxy:
        http_proxy = os.getenv("PROXY_HTTP")
        https_proxy = os.getenv("PROXY_HTTPS")
        proxies = {
            'http': http_proxy,
            'https': https_proxy
        }

    try:
        response = requests.get(url, headers=headers, proxies=proxies)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return f"Error: Request failed with exception: {e}"
    except Exception as e:
        return f"Error fetching JSON response: {e}"


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
        if not isinstance(json_data, list) or not json_data: # check if json_data is a list and not empty
            return (None, None)

        first_element = json_data[0]
        if not isinstance(first_element, dict) or 'data' not in first_element: # check if first_element is a dict and has 'data' key
            return (None, None)

        if not isinstance(first_element['data'], dict) or 'children' not in first_element['data'] or not isinstance(first_element['data']['children'], list) or not first_element['data']['children']: # check nested structure
            return (None, None)

        first_child = first_element['data']['children'][0]
        if not isinstance(first_child, dict) or 'data' not in first_child: # check if first_child is dict and has data key
            return (None, None)
        data = first_child['data']

        # Extract title and content (same as before)
        title = data.get('title', '')
        content = data.get('selftext', '')

        url = ''
        if "reddit.com" in data.get('url', '') or "v.redd.it" in data.get('url', ''):
            url = data.get('url', '')
        else:
            url = f"https://www.reddit.com{data.get('permalink', '')}"

        # Create the content dictionary (similar to comment structure)
        content_dict = {
            'url': url, # thread link
            'author': data.get('author', ''),
            'score': data.get('score', 0),
            'ef_score': data.get('score', 0)/2 if isinstance(data.get('score', 0), (int, float)) else 0, # safe division
            'body': content,
            'type': data.get('link_flair_text', ''),
            'image_link': [],
            'extra_content_link': [],
        }

        # Extract image links from gallery posts
        if data.get('is_gallery', False):
            media_metadata = data.get('media_metadata', {})
            if isinstance(media_metadata, dict): # check if media_metadata is a dict before iterating
                for img_id, img_info in media_metadata.items():
                    if isinstance(img_info, dict) and 's' in img_info and isinstance(img_info.get('s'), dict) and 'u' in img_info['s']:  # check nested dict structure
                        # Get URL and fix HTML-encoded ampersands
                        image_url = img_info['s']['u'].replace('&', '&')
                        content_dict['image_link'].append(image_url)
        else:
            # Fallback to URL if it's a direct image link
            url_overridden_by_dest = data.get('url_overridden_by_dest', False)
            if url_overridden_by_dest:
                if isinstance(url_overridden_by_dest, str) and any(url_overridden_by_dest.lower().endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp']):
                    content_dict['image_link'].append(url_overridden_by_dest)
                elif isinstance(url_overridden_by_dest, str): # only append if url_overridden_by_dest is a string
                    # This is for non-image content (e.g., articles)
                    content_dict['extra_content_link'].append(url_overridden_by_dest)

        new_content, image_links = extract_links_from_selftext(content)
        if isinstance(new_content, list): # check if new_content is list before extending
            content_dict["extra_content_link"] += new_content
        if isinstance(image_links, list): # check if image_links is list before extending
            content_dict["image_link"] += image_links
        content_dict["extra_content_link"] = filter_links(content_dict["extra_content_link"])

        # print("Content dict: ", content_dict)
        return (title, content_dict)

    except (KeyError, IndexError, TypeError) as e:
        # raise ValueError
        print(e)
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


def extract_links_from_selftext(text):
    """
    Extracts all URLs from the given selftext string and separates those containing '&amp'.
    
    Args:
        text (str): The input text containing URLs.
    
    Returns:
        tuple:
            - image_links (list): URLs that include '&amp'.
            - extra_content_links (list): All other extracted URLs.
    """
    # Regular expression pattern to match URLs
    url_pattern = r'https?://[^\s\)]+'
    
    # Find all matching URLs in the text
    links = re.findall(url_pattern, text)
    
    # Initialize lists to store separated links
    image_links = []
    extra_content_links = []
    
    # Iterate through all extracted links
    for link in links:
        if '&amp' in link:
            link = link.replace('&amp;', '&')
            image_links.append(link)
        else:
            extra_content_links.append(link)
    
    return extra_content_links, image_links

# can't scrape x or pdf content now. look at this in the future.
def filter_links(links):
    """
    Removes links that contain 'x.com' or '.pdf' (case-insensitive).

    Parameters:
        links (list of str): The list of URLs to be filtered.

    Returns:
        list of str: A new list with the unwanted links removed.
    """
    return [
        link for link in links
        if "x.com" not in link.lower() and ".pdf" not in link.lower()
    ]
    
