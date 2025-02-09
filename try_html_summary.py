import os
from typing import List, Dict
import requests
from bs4 import BeautifulSoup
from readability import Document
import random
import time
from dotenv import load_dotenv
from urllib.parse import urlparse
from openai import OpenAI

load_dotenv()

# Define your proxies directly here
PROXY_HTTP = os.getenv("PROXY_HTTP")
PROXY_HTTPS = os.getenv("PROXY_HTTPS")
PROXIES = {
    'http': PROXY_HTTP,
    'https': PROXY_HTTPS
}

def chat_completion(
    chat_history: List[Dict[str, str]],
    temperature: float = 0.2,
    is_image=False
) -> str:
    """
    Unified chat completion function for both local and cloud LLMs using OpenAI-compatible API.
    """
    # Determine if we're using local or cloud based on environment
    is_local = os.getenv("USE_LOCAL_LLM", "false").lower() == "true"
    base_url = os.getenv("BASE_URL" if is_local else "CLOUD_BASE_URL").rstrip('/')
    api_key = os.getenv("VLLM_API_KEY" if is_local else "CLOUD_LLM_API_KEY").rstrip('/')
    
    if not is_image:
        model = os.getenv("MODEL_PATH" if is_local else "CLOUD_MODEL_NAME")
    else: # image
        model = os.getenv("MODEL_PATH" if is_local else "CLOUD_VMODEL_NAME")


    # Create OpenAI client
    client = OpenAI(
        api_key=api_key,
        base_url=base_url,
    )

    # Prepare request parameters
    request_params = {
        "model": model,
        "messages": chat_history.copy(),
        "temperature": temperature,
    }

    try:
        response = client.chat.completions.create(**request_params)
        return response.choices[0].message.content
    except Exception as e:
        print(f"Full base URL: {base_url}")
        print(f"Request params: {request_params}")
        raise

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
        doc = Document(html)
        summary_html = doc.summary()
        soup = BeautifulSoup(summary_html, 'html.parser')
        # Get text and replace multiple whitespaces with single space
        text = ' '.join(soup.get_text(separator=' ').split())
        return text

def fetch_html(url: str) -> str:
    """
    Fetches HTML content from the specified URL using proxies.
    Implements a retry mechanism with random delays.
    """
    headers = {
        'User-Agent': (
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
            'AppleWebKit/537.36 (KHTML, like Gecko) '
            'Chrome/58.0.3029.110 Safari/537.3'
        )
    }
    max_retries = 4
    for attempt in range(max_retries):
        try:
            response = requests.get(url, headers=headers, proxies=PROXIES, timeout=10)
            response.raise_for_status()
            return response.text
        except requests.exceptions.RequestException as e:
            print(f"Attempt {attempt + 1} failed with error: {e}")
            if attempt < max_retries - 1:
                delay = random.randint(1, 15)
                print(f"Retrying after {delay} seconds...")
                time.sleep(delay)
            else:
                print("Max retries reached. Unable to fetch HTML content.")
                raise

def generate_summary(url: str, word_count: int = 200) -> str:
    """
    Generates a summary for the main content of the given URL.
    
    Parameters:
    *   url: The URL of the webpage to summarize.
    *   word_count: Desired word count for the summary (default is 100).
    
    Returns:
    *   A summary string.
    """
    html = fetch_html(url)
    main_content = extract_main_content(html, url)

    print(html)
    print(main_content)
    print("\n\n")
    
    # Prepare the chat history
    chat_history = [
        {"role": "system", "content": (
            "You are a focused web content summarization assistant. "
            "Your goal is to extract and summarize the main theme of a web page. "
            "For GitHub repositories, prioritize summarizing the README file. "
            "Ignore any error messages or unrelated content that might be displayed alongside the main content. "
            "Be concise, clear, and structured in your summaries, ensuring that key information is retained while filtering out noise."
        )},
        {"role": "user", "content": (
            f"Please provide a concise summary (100 to {word_count} words) of the following content, "
            "focusing on the main theme and ignoring sidebars, ads, and other irrelevant information.\n\n"
            f"{main_content[:4096]}"
        )}
    ]
    
    # Call the chat_completion function
    summary = chat_completion(chat_history, temperature=0.2)
    return summary

if __name__ == "__main__":
    # Example usage
    test_url = "https://www.hawley.senate.gov/wp-content/uploads/2025/01/Hawley-Decoupling-Americas-Artificial-Intelligence-Capabilities-from-China-Act.pdf"

    try:
        summary = generate_summary(test_url, word_count=200)
        print("Summary:")
        print(summary)
    except Exception as e:
        print(f"An error occurred while generating the summary: {e}")