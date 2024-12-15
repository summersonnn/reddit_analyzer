from scrape_functions import extract_main_content, extract_shreddit_title_from_main_content, extract_op, fetch_html_response_with_selenium, extract_comments_with_tree
from llm_talk import chat_with_vllm
import json

test_links = [
    "https://www.reddit.com/r/LocalLLaMA/comments/1hdaytv/deepseekaideepseekvl2_hugging_face/",  # blockquotes, image comments
    "https://www.reddit.com/r/LocalLLaMA/comments/1he1rli/qwen_dev_new_stuff_very_soon/", # image post
    "https://www.reddit.com/r/LocalLLaMA/comments/1hdnm40/til_llama_33_can_do_multiple_tool_calls_and_tool/", # gif post
    "https://www.reddit.com/r/LocalLLaMA/comments/1heemer/the_absolute_best_coding_model_that_can_fit_on/", # short thread, fast test
    "https://www.reddit.com/r/LocalLLaMA/comments/1hegcl0/where_do_you_think_the_cutoff_is_for_a_model_to/", # short thread, fast test
    "https://www.reddit.com/r/LocalLLaMA/comments/1hefbq1/coheres_new_model_is_epic/"
]

# Example usage
url = test_links[-1] # Replace with the desired URL
html_response = fetch_html_response_with_selenium(url)

main_content = extract_main_content(html_response)
title = extract_shreddit_title_from_main_content(main_content)
# print(title)

original_post = extract_op(main_content)
# print(original_post)

comments = extract_comments_with_tree(main_content)
# print(comments["pretty"])

# Combine all scraped parts into a single variable with appropriate tags
scraped_data = {
    "title": title,
    "original_post": original_post,
    "comments": comments
}

# -------------------------------LLM section-------------------------------
api_key = "token-abc123"

# Add system prompt
system_message = {
    "role": "system", 
    "content": """Analyze the entire thread, including the title, original post, comments, and subcomments. Prioritize information from posts with the highest scores, as they indicate strong user agreement. Identify contradictions, biases, and emerging trends within the discussion. Summarize the key points and conclusions based on the most reliable information."""
}

chat_history = []
chat_history.append(system_message)
# Format scraped data as a user message
user_message = {
    "role": "user", 
    "content": json.dumps(scraped_data, indent=4)  # Convert to JSON string for readability
}

chat_history.append(user_message)

chat_with_vllm(api_key, chat_history, stream=True, prompt_user=False)
