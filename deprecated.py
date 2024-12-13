import requests

def fetch_html_response(url):
    """
    Fetches the HTML response from the given URL.
    """
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise an exception for HTTP errors
        return response.text
    except requests.exceptions.RequestException as e:
        return f"Error fetching the HTML response: {e}"


# Only depth 1 comments
def extract_comments(main_content):
    """
    Extract comments from the main_content div.
    """
    try:
        # Find the div with id starting with "comment-tree-content-anchor-"
        comment_tree_content_anchor = main_content.find('div', id=re.compile(r'^comment-tree-content-anchor-'))
        if not comment_tree_content_anchor:
            return "The comment-tree-content-anchor div was not found in the main content."
        
        faceplate_batch = comment_tree_content_anchor.find('faceplate-batch', target="#comment-tree")
        if not faceplate_batch:
            return "The faceplate-batch tag with target '#comment-tree' was not found in the main content."
        
        # Find the shreddit-comment-tree tag with the id value "comment-tree"
        comment_tree = faceplate_batch.find('shreddit-comment-tree', id="comment-tree")
        if not comment_tree:
            return "The shreddit-comment-tree tag with id 'comment-tree' was not found in the main content."
        
        # for child in comment_tree.children:
        #     if child.name:  # Check if the child is a tag
        #         print(f"<{child.name} {child.attrs}>")
        #print(comment_tree.prettify())

        # Find all shreddit-comment tags
        comments = []
        comment_ads = comment_tree.find_all('shreddit-comment', attrs={'author': lambda x: x != '[deleted]'}, recursive=False)
        for comment_ad in comment_ads:
            # Find the div with id ending in "-comment-rtjson-content"
            comment_rtjson_content = comment_ad.find('div', id=re.compile(r'-comment-rtjson-content$'))
            if not comment_rtjson_content:
                continue

            # Find the div with id ending in "-post-rtjson-content"
            post_rtjson_content = comment_rtjson_content.find('div', id=re.compile(r'-post-rtjson-content$'))
            if not post_rtjson_content:
                continue

            # Extract all <blockquote> and <p> tags and combine their text
            p_tags = post_rtjson_content.find_all('p')
            quote_block = post_rtjson_content.find('blockquote')
            quote_text = ''
            if quote_block:
                # Extract text from the blockquote and prepend it with "In response to: "
                quote_text = 'In response to: ' + ' '.join([p.get_text(strip=True) for p in quote_block.find_all('p')]) + '\n'
                p_tags = p_tags[1:]
            
            
            comment_text = ' '.join([p.get_text(strip=True) for p in p_tags])

            # Combine quote text and comment text
            if comment_text:
                comments.append(quote_text + comment_text)

        return comments

    except AttributeError:
        return "An error occurred while extracting comments."