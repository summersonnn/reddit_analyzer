import praw
import os
import streamlit as st
from typing import Dict, Optional
import re
import html


def get_reddit_client():
    """
    Creates and returns a PRAW Reddit client instance.
    Uses environment variables or Streamlit secrets for configuration.
    """
    try:
        # Try to get credentials from Streamlit secrets first
        client_id = st.secrets.get("REDDIT_CLIENT_ID")
        client_secret = st.secrets.get("REDDIT_CLIENT_SECRET")
        user_agent = st.secrets.get("REDDIT_USER_AGENT", "MidoriRedditAnalyzer/1.0")
    except (ImportError, AttributeError):
        # Fallback to environment variables
        client_id = os.getenv("REDDIT_CLIENT_ID")
        client_secret = os.getenv("REDDIT_CLIENT_SECRET")
        user_agent = os.getenv("REDDIT_USER_AGENT", "MidoriRedditAnalyzer/1.0")
    
    if not client_id or not client_secret:
        raise ValueError("Reddit API credentials not found. Please set REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET")
    
    return praw.Reddit(
        client_id=client_id,
        client_secret=client_secret,
        user_agent=user_agent
    )


def extract_submission_id_from_url(url: str) -> Optional[str]:
    """
    Extracts the submission ID from a Reddit URL.
    
    Args:
        url (str): Reddit URL
        
    Returns:
        Optional[str]: Submission ID or None if not found
    """
    # Handle various Reddit URL formats
    patterns = [
        r'/comments/([a-zA-Z0-9]+)/',  # /r/subreddit/comments/abc123/
        r'/comments/([a-zA-Z0-9]+)$',  # /r/subreddit/comments/abc123
        r'/comments/([a-zA-Z0-9]+)/[^/]+$',  # /r/subreddit/comments/abc123/title
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    
    return None


def fetch_thread_data_praw(url: str) -> Dict:
    """
    Fetches Reddit thread data using PRAW.
    
    Args:
        url (str): Reddit thread URL
        
    Returns:
        Dict: Thread data with title, original_post, comments, and url
    """
    try:
        reddit = get_reddit_client()
        submission_id = extract_submission_id_from_url(url)
        
        if not submission_id:
            return {
                "title": None,
                "original_post": None,
                "comments": None,
                "url": url,
                "error": "Could not extract submission ID from URL"
            }
        
        # Get the submission
        submission = reddit.submission(id=submission_id)
        
        # Extract original post data
        title = submission.title
        content = submission.selftext
        
        # Create content dictionary similar to scraping version
        content_dict = {
            'url': url,
            'author': str(submission.author) if submission.author else '[deleted]',
            'score': submission.score,
            'ef_score': submission.score / 2,  # Safe division
            'body': content,
            'type': submission.link_flair_text or '',
            'image_link': [],
            'extra_content_link': [],
        }
        
        # Extract image links from gallery posts
        if hasattr(submission, 'is_gallery') and submission.is_gallery:
            if hasattr(submission, 'media_metadata') and submission.media_metadata:
                for img_id, img_info in submission.media_metadata.items():
                    if 's' in img_info and 'u' in img_info['s']:
                        image_url = img_info['s']['u'].replace('&amp;', '&')
                        content_dict['image_link'].append(image_url)
        else:
            # Check if submission has media
            if hasattr(submission, 'url') and submission.url:
                if any(submission.url.lower().endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp']):
                    content_dict['image_link'].append(submission.url)
                else:
                    content_dict['extra_content_link'].append(submission.url)
        
        # Extract links from selftext
        new_content, image_links = extract_links_from_selftext(content)
        if isinstance(new_content, list):
            content_dict["extra_content_link"] += new_content
        if isinstance(image_links, list):
            content_dict["image_link"] += image_links
        content_dict["extra_content_link"] = filter_links(content_dict["extra_content_link"])
        
        # Get comments
        submission.comment_sort = 'top'  # Sort by top comments
        submission.comments.replace_more(limit=0)  # Remove "load more comments" links
        
        comments = []
        for comment in submission.comments.list():
            comment_dict = scrape_comment_praw(comment)
            if comment_dict:
                comments.append(comment_dict)
        
        return {
            "title": title,
            "original_post": content_dict,
            "comments": comments,
            "url": url
        }
        
    except Exception as e:
        print(f"Error fetching thread data with PRAW: {e}")
        return {
            "title": None,
            "original_post": None,
            "comments": None,
            "url": url,
            "error": str(e)
        }


def scrape_comment_praw(comment, depth=0):
    """
    Recursively scrapes a comment and its replies using PRAW.
    
    Args:
        comment: PRAW comment object
        depth (int): The depth of the comment in the hierarchy
        
    Returns:
        dict: A dictionary representing the comment and its replies
    """
    try:
        # Skip deleted comments
        if comment.author is None:
            return None
        
        # Format the comment body
        body = extract_quotes(comment.body)
        body = process_image_links(body)
        
        # Create the comment dictionary
        comment_dict = {
            'author': str(comment.author),
            'score': comment.score,
            'ef_score': comment.score * (depth + 1),
            'body': body,
            'depth': depth,
            'replies': []
        }
        
        # Get replies
        comment.replies.replace_more(limit=0)  # Remove "load more replies" links
        for reply in comment.replies:
            reply_dict = scrape_comment_praw(reply, depth + 1)
            if reply_dict:
                comment_dict['replies'].append(reply_dict)
        
        return comment_dict
        
    except Exception as e:
        print(f"Error scraping comment: {e}")
        return None


def extract_quotes(body):
    """
    Extracts and formats quoted parts in the comment body.
    
    Args:
        body (str): The comment body.
        
    Returns:
        str: The formatted comment body with quoted parts marked.
    """
    if "&gt;" not in body:
        return body
    
    lines = body.split("\n")
    formatted_body = ""
    for line in lines:
        if line.strip().startswith("&gt;"):
            quoted_part = line.strip()[4:].strip()
            formatted_body += f"Quoted Part: '{quoted_part}'\n"
        else:
            formatted_body += f"{line}\n"
    return formatted_body.strip()


def process_image_links(text, html_body=None):
    """
    Processes image links in text.
    
    Args:
        text (str): The text to process
        html_body (str, optional): HTML body for additional processing
        
    Returns:
        str: Processed text
    """
    def replacer(match):
        url = match.group(0)
        if '&amp;' in url:
            url = url.replace('&amp;', '&')
        return url
    
    processed_text = re.sub(r'https?://[^\s\)]+', replacer, text)
    
    if html_body:
        unescaped_html = html.unescape(html_body)
        img_match = re.search(r'<img\s+[^>]*src="([^"]+)"', unescaped_html)
        if img_match:
            gif_url = img_match.group(1)
            gif_url = gif_url.replace('&amp;', '&')
            processed_text += f"\nGIF: {gif_url}"
    
    return processed_text


def extract_links_from_selftext(text):
    """
    Extracts links from selftext.
    
    Args:
        text (str): The text to extract links from
        
    Returns:
        tuple: (content_links, image_links)
    """
    if not text:
        return [], []
    
    # Find all URLs
    url_pattern = r'https?://[^\s\)]+'
    urls = re.findall(url_pattern, text)
    
    content_links = []
    image_links = []
    
    for url in urls:
        # Fix HTML-encoded ampersands
        url = url.replace('&amp;', '&')
        
        # Check if it's an image
        if any(url.lower().endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp']):
            image_links.append(url)
        else:
            content_links.append(url)
    
    return content_links, image_links


def filter_links(links):
    """
    Filters links to remove duplicates and invalid ones.
    
    Args:
        links (list): List of links to filter
        
    Returns:
        list: Filtered list of links
    """
    if not links:
        return []
    
    # Remove duplicates while preserving order
    seen = set()
    filtered = []
    for link in links:
        if link not in seen:
            seen.add(link)
            filtered.append(link)
    
    return filtered


def test_reddit_access_praw() -> bool:
    """
    Tests if Reddit API access is working.
    
    Returns:
        bool: True if accessible, False otherwise
    """
    try:
        reddit = get_reddit_client()
        # Try to access a simple subreddit
        reddit.subreddit("test")
        # This should work without any issues
        return True
    except Exception as e:
        print(f"Reddit API access test failed: {e}")
        return False 