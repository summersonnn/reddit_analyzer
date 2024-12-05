import requests
import re
import time

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import WebDriverException, NoSuchElementException, ElementClickInterceptedException
from selenium.webdriver.common.action_chains import ActionChains

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
    

# Still not perfect but works ~95% of the time. Some deleted inner comments are still problematic.
# Plus, some comments where the "+" button must be clicked in order to see the comment tree.
# These will be fixed at later stages. For now, we need to catch the loop, break and continue operations.
# TODO: Detect the loop and break it in "Load X more replies" while loop
def fetch_html_response_with_selenium(url):
    """
    Fetches the HTML response from the given URL using Selenium with Chrome.
    """
    # Set up Chrome options
    chrome_options = Options()
    # chrome_options.add_argument("--headless")  # Run Chrome in headless mode
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    # Path to the ChromeDriver (update this path as necessary)
    chromedriver_path = '/home/kubilay/Downloads/chromedriver-linux64/chromedriver'

    # Initialize the Chrome WebDriver
    service = Service(chromedriver_path)
    driver = webdriver.Chrome(service=service, options=chrome_options)

    try:
        # Open the URL
        driver.get(url)

        # Scroll down the page to load all content
        last_height = driver.execute_script("return document.body.scrollHeight")
        while True:
            # Scroll down to the bottom
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            # Wait for the page to load more content
            time.sleep(1)  # Adjust the sleep time as necessary
            # Calculate new scroll height and compare with last scroll height
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                # Check for the button and click it if it exists
                try:
                    button = driver.find_element(By.XPATH, "/html/body/shreddit-app/div/div[1]/div/main/div/faceplate-batch/shreddit-comment-tree/faceplate-partial/div[1]/faceplate-tracker/button/span/span[2]")
                    button.click()
                    # Wait for the page to load more content after clicking the button
                    time.sleep(2)  # Adjust the sleep time as necessary
                    move_cursor_to_center_of_viewport(driver)
                    # Update the new height after clicking the button
                    new_height = driver.execute_script("return document.body.scrollHeight")
                except NoSuchElementException:
                    # Button not found, exit the loop
                    break
            last_height = new_height

        # Initial fetch of the page source
        page_source = driver.page_source

        # XPATH for "Load X more replies" buttons
        all_generic_xpath = "//shreddit-comment//a[starts-with(@id, 'comments-permalink-')]/span[@class='text-secondary-weak font-normal'] | //shreddit-comment//faceplate-partial/div[@class='inline-block ml-px']/button[@class='text-tone-2 text-12 no-underline hover:underline px-xs py-xs flex ml-[3px] xs:ml-0 !bg-transparent !border-0']/span[@class='text-secondary-weak font-normal']"

        # For now, we won't be using all_generic_xpath but shallow_generic_xpath
        # The difference: The latter scrapes only up to depth 4 which is the comment depth limit. Beyond that, clicking on "X more replies" will change the whole page source.
        shallow_generic_xpath = "//shreddit-comment//faceplate-partial/div[@class='inline-block ml-px']/button[@class='text-tone-2 text-12 no-underline hover:underline px-xs py-xs flex ml-[3px] xs:ml-0 !bg-transparent !border-0']/span[@class='text-secondary-weak font-normal']"

        # The diff from above is that this one doesn't capture buttons inside a deleted comment (in any depth)
        shallow_generic_xpath2 = """
            //shreddit-comment[not(@author='[deleted]') and not(ancestor::shreddit-comment[@author='[deleted]'])]
            //faceplate-partial/div[@class='inline-block ml-px']
            /button[@class='text-tone-2 text-12 no-underline hover:underline px-xs py-xs flex ml-[3px] xs:ml-0 !bg-transparent !border-0']
            /span[@class='text-secondary-weak font-normal']
        """

        # Dictionary to keep track of consecutive failures for each button
        button_failures = {}

        # Initialize the flag to track if any button was clicked
        at_least_one_clicked = True

        while at_least_one_clicked:
            # Find all "Load X more replies" buttons only if at least one button was clicked in the previous iteration
            try:
                buttons = driver.find_elements(By.XPATH, shallow_generic_xpath2)
                if not buttons:
                    print("No 'Load X more replies' buttons found. Exiting loop.")
                    break

                at_least_one_clicked = False
                for button in buttons:
                    button_id = button.id  # Use button's unique ID as a key

                    try:
                        # Print the button's text if it exists
                        button_text = button.text
                        print(f"Clicking button with text: {button_text}")

                        # Scroll the button into view with offset to avoid header overlaps
                        driver.execute_script("""
                            arguments[0].scrollIntoView({
                                behavior: 'smooth',
                                block: 'center'
                            });
                        """, button)
                        time.sleep(1)

                        # Click the button
                        button.click()
                        # Reset the failure count for this button
                        button_failures[button_id] = 0
                        at_least_one_clicked = True

                    except ElementClickInterceptedException:
                        print(f"Element click intercepted for button with text: {button_text}")
                        # Increment the failure count for this button
                        button_failures[button_id] = button_failures.get(button_id, 0) + 1
                        if button_failures[button_id] >= 3:
                            print(f"Button with text: {button_text} failed to click 3 times. Removing from candidates.")
                            # Remove the button from the list
                            buttons.remove(button)

                    except Exception as e:
                        print(f"Failed to click button: {e}")
                        # Increment the failure count for this button
                        button_failures[button_id] = button_failures.get(button_id, 0) + 1
                        if button_failures[button_id] >= 3:
                            print(f"Button with text: {button_text} failed to click 3 times. Removing from candidates.")
                            # Remove the button from the list
                            buttons.remove(button)

                if at_least_one_clicked:
                    # Re-fetch the page source only if at least one button was clicked
                    page_source = driver.page_source

            except NoSuchElementException:
                print("No 'Load X more replies' buttons found. Exiting loop.")
                break

        # Final fetch of the page source after all checks
        page_source = driver.page_source
        return page_source

    except WebDriverException as e:
        return f"Error fetching the HTML response with Selenium: {e}"
    finally:
        driver.quit()
    
def extract_main_content(html_response):
    """
    Extract the main content (main tag with id 'main-content')
    from the specified hierarchy in the HTML response.
    """
    try:
        # Parse the HTML content
        soup = BeautifulSoup(html_response, 'html.parser')

        # Navigate to the shreddit-title tag based on the hierarchy
        main_content = (
            soup.body
                .find('shreddit-app')
                .find('div', class_="grid-container")
                .find('div', class_="subgrid-container")
                .find('div', class_="main-container")
                .find('main', id="main-content")
        )
        return main_content
    except AttributeError:
        return "The specified structure was not found in the HTML."
    
def extract_shreddit_title_from_main_content(main_content):
    """
    Extract the title attribute from the shreddit-title tag
    inside the main content, returning the substring from the
    beginning up to the last semicolon.
    """
    try:
        shreddit_title_tag = main_content.find('shreddit-title')

        # Extract the title attribute
        if shreddit_title_tag and 'title' in shreddit_title_tag.attrs:
            full_title = shreddit_title_tag['title']
            # Find the last semicolon and slice the string
            last_semicolon_index = full_title.rfind(':')
            return full_title[:last_semicolon_index-1] if last_semicolon_index != -1 else full_title
        else:
            return "shreddit-title tag or title attribute not found."
    except AttributeError:
        return "Invalid input: main_content is None or not a valid tag."
    
def extract_op(main_content):
    """
    Extracts and combines all text from <p>, <li>, and other relevant tags
    inside the specified structure within main_content.
    """
    try:
        # Navigate to the shreddit-post tag based on the hierarchy
        shreddit_post = main_content.find('shreddit-post')
        if not shreddit_post:
            return "The 'shreddit-post' tag was not found in the main content."

        text_neutral_content = shreddit_post.find('div', class_="text-neutral-content", slot="text-body")
        if not text_neutral_content:
            return "The 'div' with class 'text-neutral-content' and slot 'text-body' was not found in the 'shreddit-post' tag."

        mb_sm_div = text_neutral_content.find('div', class_="mb-sm mb-xs px-md xs:px-0 overflow-hidden")
        if not mb_sm_div:
            return "The 'div' with class 'mb-sm mb-xs px-md xs:px-0 overflow-hidden' was not found in the 'text-neutral-content' div."

        # Find the div with id starting with "t3_"
        t3_div = mb_sm_div.find('div', id=re.compile(r'^t3_'))
        if not t3_div:
            return "The 'div' with id 't3_*' was not found in the specified div."

        # List of tags that may contain text
        text_tags = ['p', 'li', 'ol', 'ul', 'span', 'strong', 'em', 'a', 'br', 'i', 'b', 'div', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6']

        # Recursive function to extract text from all relevant tags
        def extract_text_from_tag(tag):
            text_parts = []
            for child in tag.children:
                # If the child is a tag in text_tags, it extracts the text
                if child.name in text_tags:
                    text = child.get_text(strip=True)
                    if text:  # Check if the text is not empty
                        text_parts.append(text + '\n')
                # If the child has a string content (child.string), it strips the string and appends it 
                elif child.string:
                    text = child.string.strip()
                    if text:  # Check if the text is not empty
                        text_parts.append(text + '\n')
                elif child.name:  # Recursively extract text from nested tags
                    text = extract_text_from_tag(child)
                    if text:  # Check if the text is not empty
                        text_parts.append(text + '\n')
            return ' '.join(part for part in text_parts if part)

        combined_text = extract_text_from_tag(t3_div)
        
        return combined_text
    except AttributeError:
        return "An unexpected error occurred while navigating the HTML structure."
    
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
    
# Full comment tree
def extract_comments_with_tree(main_content):
    """
    Extract comments from the main_content div, including nested comments.
    Returns comments in a tree structure using a single dictionary.
    """
    def pretty_print_comments(comments_dict, indent=0):
        """
        Helper function to print comments in a tree-like structure
        """
        output = ""
        for key, value in comments_dict.items():
            if key.startswith('comment_'):
                output += "="*50 + "\n"  # Separator for top-level comments
            
            prefix = "    " * indent  # 4 spaces for each level of indentation
            
            if value["comment"]:
                # Add arrow prefix for replies
                arrow = "└─► " if key.startswith('reply_') else ""
                output += f"{prefix}{arrow}{value['comment']}\n"
            
            if value["replies"]:
                output += pretty_print_comments(value["replies"], indent + 1)
        return output

    def extract_comment_and_children(comment_ad):
        comment_data = {"comment": "", "replies": {}}
        
        # Extract the current comment's content
        comment_rtjson_content = comment_ad.find('div', id=re.compile(r'-comment-rtjson-content$'))
        if comment_rtjson_content:
            post_rtjson_content = comment_rtjson_content.find('div', id=re.compile(r'-post-rtjson-content$'))
            if post_rtjson_content:
                # Extract quotes and paragraphs
                p_tags = post_rtjson_content.find_all('p')
                quote_block = post_rtjson_content.find('blockquote')
                quote_text = ''
                if quote_block:
                    quote_text = 'In response to: ' + ' '.join([p.get_text(strip=True) for p in quote_block.find_all('p')]) + '\n'
                    p_tags = p_tags[1:]
                
                comment_text = ' '.join([p.get_text(strip=True) for p in p_tags])
                if comment_text:
                    comment_data["comment"] = quote_text + comment_text

        # Recursively extract child comments
        child_comments = comment_ad.find_all('shreddit-comment', attrs={'author': lambda x: x != '[deleted]'}, recursive=False)
        for i, child in enumerate(child_comments):
            child_data = extract_comment_and_children(child)
            if child_data["comment"] or child_data["replies"]:
                comment_data["replies"][f"reply_{i+1}"] = child_data
                
        return comment_data

    try:
        # Find the div with id starting with "comment-tree-content-anchor-"
        comment_tree_content_anchor = main_content.find('div', id=re.compile(r'^comment-tree-content-anchor-'))
        if not comment_tree_content_anchor:
            return "The comment-tree-content-anchor div was not found in the main content."
        
        faceplate_batch = comment_tree_content_anchor.find('faceplate-batch', target="#comment-tree")
        if not faceplate_batch:
            return "The faceplate-batch tag with target '#comment-tree' was not found in the main content."
        
        comment_tree = faceplate_batch.find('shreddit-comment-tree', id="comment-tree")
        if not comment_tree:
            return "The shreddit-comment-tree tag with id 'comment-tree' was not found in the main content."

        # Find all top-level comments and their replies
        comments_dict = {}
        comment_ads = comment_tree.find_all('shreddit-comment', attrs={'author': lambda x: x != '[deleted]'}, recursive=False)
        for i, comment_ad in enumerate(comment_ads):
            comment_data = extract_comment_and_children(comment_ad)
            if comment_data["comment"] or comment_data["replies"]:
                comments_dict[f"comment_{i+1}"] = comment_data

        # Return both the dictionary and its pretty-printed version
        return {
            "raw": comments_dict,
            "pretty": pretty_print_comments(comments_dict),
        }

    except AttributeError:
        return "An error occurred while extracting comments."
    

def move_cursor_to_center_of_viewport(driver):
    # Get the size of the viewport
    viewport_width = driver.execute_script("return document.documentElement.clientWidth")
    viewport_height = driver.execute_script("return document.documentElement.clientHeight")

    # Calculate the center of the viewport
    center_x = viewport_width // 2
    center_y = viewport_height // 2

    # Move the cursor to the center of the viewport
    actions = ActionChains(driver)
    actions.move_by_offset(center_x, center_y).perform()


