from scrape_functions import fetch_html_response, extract_main_content, extract_shreddit_title_from_main_content, extract_op, extract_comments, fetch_html_response_with_selenium, extract_comments_with_tree

# Example usage
url = "https://www.reddit.com/r/LocalLLaMA/comments/1h12cmq/cheapest_hardware_go_run_32b_models/?rdt=57503"  # Replace with the desired URL
html_response = fetch_html_response_with_selenium(url)

main_content = extract_main_content(html_response)
# title = extract_shreddit_title_from_main_content(main_content)
# # print(title)

# original_post = extract_op(main_content)
# # print(original_post)

# comments = extract_comments(main_content)
# for comment in comments:
#     print(comment, end="\n\n")

comments = extract_comments_with_tree(main_content)
print(comments["pretty"])


# Account for nested comments (right now only the root comments are fetched)


# Bugfix:
# - When fetching comments, blockquotes are assumed to be always on the top which isn't the case. The context meaning might be affected due to this.
