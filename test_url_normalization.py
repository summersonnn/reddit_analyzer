#!/usr/bin/env python3
"""
Test URL normalization for Reddit URLs.
"""

import sys
sys.path.append('.')

from scrape_functions import normalize_reddit_url

def test_url_normalization():
    test_urls = [
        "https://www.reddit.com/r/htmx/comments/1lwsbvx/comment/n2znus6/",
        "https://www.reddit.com/r/htmx/comments/1lwsbvx/",
        "https://www.reddit.com/r/htmx/comments/1lwsbvx/assessment_of_htmx_with_fastapi_llm_sse_jinja/",
        "https://www.reddit.com/r/htmx/comments/1lwsbvx/assessment_of_htmx_with_fastapi_llm_sse_jinja/comment/n2znus6/"
    ]
    
    print("=== URL Normalization Test ===")
    for url in test_urls:
        normalized = normalize_reddit_url(url)
        print(f"\nOriginal: {url}")
        print(f"Normalized: {normalized}")
        print(f"Changed: {url != normalized}")

if __name__ == "__main__":
    test_url_normalization() 