from scrape_functions import extract_main_content, extract_shreddit_title_from_main_content, extract_op, fetch_html_response_with_selenium, extract_comments_with_tree

test_links = [
    "https://www.reddit.com/r/LocalLLaMA/comments/1hdaytv/deepseekaideepseekvl2_hugging_face/",  # blockquotes, image comments
    "https://www.reddit.com/r/LocalLLaMA/comments/1he1rli/qwen_dev_new_stuff_very_soon/", # image post
    "https://www.reddit.com/r/LocalLLaMA/comments/1hdnm40/til_llama_33_can_do_multiple_tool_calls_and_tool/", # gif post
    "https://www.reddit.com/r/LocalLLaMA/comments/1heemer/the_absolute_best_coding_model_that_can_fit_on/"
]

# Example usage
url = test_links[3]  # Replace with the desired URL
html_response = fetch_html_response_with_selenium(url)

main_content = extract_main_content(html_response)
# title = extract_shreddit_title_from_main_content(main_content)
# # print(title)

original_post = extract_op(main_content)
print(original_post)

comments = extract_comments_with_tree(main_content)
print(comments["pretty"])


