import os
import requests
from bs4 import BeautifulSoup
# import time
from dotenv import load_dotenv
from urllib.parse import urlparse
from llm_interact import chat_completion

load_dotenv()

# Define your proxies directly here
PROXY_HTTP = os.getenv("PROXY_HTTP")
PROXY_HTTPS = os.getenv("PROXY_HTTPS")
PROXIES = {
    'http': PROXY_HTTP,
    'https': PROXY_HTTPS
}

def extract_main_content(html: str, url: str) -> str:
    """
    Extracts and cleans the main textual content from HTML, removing ads, sidebars, etc.
    For GitHub URLs, extracts content from the specific <article> tag.
    """
    parsed_url = urlparse(url)
    domain = parsed_url.netloc.lower()

    # Check if the domain is exactly 'github.com' or starts with 'www.github.com'
    if domain == 'github.com' or domain == 'www.github.com':
        soup = BeautifulSoup(html, 'html.parser')
        article = soup.find('article', class_='markdown-body entry-content container-lg')
        if article:
            text = ' '.join(article.get_text(separator=' ').split())
            return text
        else:
            raise ValueError("Could not find the specified <article> tag in GitHub URL.")
    else:
        soup = BeautifulSoup(html, 'html.parser')
        # Get text and replace multiple whitespaces with single space
        text = ' '.join(soup.get_text(separator=' ').split())
        return text

def fetch_html(url: str) -> tuple[str, bool]:
    """
    Fetches HTML content from the specified URL, conditionally using proxies.
    Returns tuple of (html_content, requires_js_flag)
    """
    headers = {
        'User-Agent': (
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
            'AppleWebKit/537.36 (KHTML, like Gecko) ' 
            'Chrome/58.0.3029.110 Safari/537.3'
        )
    }

    is_local = os.getenv("LOCAL_RUN", "false").lower() == "true"
    request_kwargs = {
        'headers': headers,
        'timeout': 10
    }

    if not is_local:
        request_kwargs['proxies'] = PROXIES
    
    try:
        response = requests.get(url, **request_kwargs)
        response.raise_for_status()
        content = response.text
        
        # Check if page requires JavaScript
        requires_js = any(phrase in content.lower() for phrase in [
            'enable javascript',
            'javascript is required',
            'please enable javascript',
            'javascript must be enabled'
        ])
        
        return content, requires_js
        
    except requests.exceptions.RequestException as e:
        print(f"Failed to fetch HTML content: {e}")
        return None, True

def generate_summary(url: str, word_count: int = 200) -> str:
    """
    Generates a summary for the main content of the given URL.
    
    Parameters:
    *   url: The URL of the webpage to summarize.
    *   word_count: Desired word count for the summary (default is 100).
    
    Returns:
    *   A summary string.
    """
    # print("Time at the start of the generate_summary: ", time.time())

    # Check for unsupported URLs
    if "x.com" in url or url.endswith(".pdf"):
        return "No summary available. Ignore this and continue."

    html, problem = fetch_html(url)
    if problem:
        return "No summary available. Ignore this and continue."

    main_content = extract_main_content(html, url)

    # print(html)
    # print(main_content[:4096])
    # print("\n\n")
    
    # Prepare the chat history
    chat_history = [
        {"role": "system", "content": (
            "You are a focused web content summarization assistant. "
            "Your goal is to extract and summarize the main theme of a web page. "
            "For GitHub repositories, prioritize summarizing the README file. "
            "Ignore any error messages or unrelated content that might be displayed alongside the main content such as navbar text, about us information etc. "
            "Be concise, clear, and structured in your summaries, ensuring that key information is retained while filtering out noise."
        )},
        {"role": "user", "content": (
            f"Please provide a concise summary (100 to {word_count} words) of the following content, "
            "focusing on the main theme and ignoring sidebars, ads, and other irrelevant information.\n\n"
            f"{main_content[:4096]}"
        )}
    ]
    
    # Call the chat_completion function
    summary = chat_completion(chat_history, temperature=0.5)
    # print("Time at the end of the generate_summary: ", time.time())
    # print(summary)
    return summary

if __name__ == "__main__":
    # Example usage
    test_url = "https://www.anthropic.com/research/building-effective-agents"

    try:
        summary = generate_summary(test_url, word_count=200)
        print("Summary:")
        print(summary)
    except Exception as e:
        print(f"An error occurred while generating the summary: {e}")