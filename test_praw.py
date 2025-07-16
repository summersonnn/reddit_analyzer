#!/usr/bin/env python3
"""
Test script to verify PRAW functionality.
"""

import sys
sys.path.append('.')

from praw_functions import test_reddit_access_praw, fetch_thread_data_praw


def test_praw_setup():
    print("=== PRAW Setup Test ===")
    
    # Test Reddit API access
    print("Testing Reddit API access...")
    accessible = test_reddit_access_praw()
    
    if accessible:
        print("✅ Reddit API access working!")
        
        # Test with a real Reddit thread
        test_url = "https://www.reddit.com/r/htmx/comments/1lwsbvx/"
        print(f"\nTesting thread fetch with: {test_url}")
        
        try:
            result = fetch_thread_data_praw(test_url)
            
            if result.get("error"):
                print(f"❌ Error fetching thread: {result['error']}")
                return False
            
            print("✅ Thread fetch successful!")
            print(f"Title: {result.get('title', 'No title')}")
            print(f"Comments: {len(result.get('comments', []))}")
            print(f"Author: {result.get('original_post', {}).get('author', 'Unknown')}")
            
            return True
            
        except Exception as e:
            print(f"❌ Error testing thread fetch: {e}")
            return False
    else:
        print("❌ Reddit API access failed")
        print("Please check your REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET")
        return False

if __name__ == "__main__":
    success = test_praw_setup()
    if success:
        print("\n🎉 PRAW is working correctly!")
    else:
        print("\n❌ PRAW setup has issues.")


if __name__ == "__main__":
    success = test_praw_setup()
    if success:
        print("\n🎉 PRAW is working correctly!")
    else:
        print("\n❌ PRAW setup has issues.") 