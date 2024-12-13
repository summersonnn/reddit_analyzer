from scrape_functions import extract_main_content, extract_shreddit_title_from_main_content, extract_op, fetch_html_response_with_selenium, extract_comments_with_tree

# Example usage
url = "https://www.reddit.com/r/LocalLLaMA/comments/1hd16ev/bro_wtf/"  # Replace with the desired URL
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

# TODO: Block comments are problematic and needs a fix (original comment does not show)


