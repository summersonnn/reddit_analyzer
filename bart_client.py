import asyncio
import aiohttp
import os


async def analyze_comments_by_bart(label_sets, all_data):
    """
    Analyzes comments and the original post using a local BART model server.

    Args:
        label_sets: A dictionary of label sets.
        all_data: A dictionary containing all thread data, including comments and original_post.

    Returns:
        A dictionary where keys are categories from label_sets and values are lists
        containing the analysis results for each comment, including original post info.
    """
    comments = all_data['comments']
    comment_texts = [comment['body'] for comment in comments]
    original_post = all_data['original_post']
    original_post_text = original_post['body']

    # Combine original post text with comment texts
    all_texts = [original_post_text] + comment_texts

    async with aiohttp.ClientSession() as session:
        results = await analyze_comments_batch(session, all_texts, label_sets)

    if results:  # Check if the results dictionary is not empty
        for category, category_results in results.items():
            print(f"Category: {category}")
            for i, result in enumerate(category_results):
                print(f"  Comment {i+1} analysis:")
                if isinstance(result, dict):  # Handle cases where result might be a dictionary (e.g., with scores for each label)
                    for label, score in result.items():
                        print(f"    {label}: {score}")
                elif isinstance(result, list):  # Handle cases where result might be a list of labels
                    print(f"    Labels: {', '.join(result)}")
                else:
                    print(f"    Result: {result}") # Handle other cases, if any
            print("-" * 20)  # Separator between categories
    else:
        print("No results to display.")
    print("----------------")

    # Add original post info and full comment information to the results
    results_with_full_comments = add_full_comment_info_to_results(results, all_data)

    # Post-process results (treating original post as a comment)
    processed_results = post_process_results(results_with_full_comments)

    if processed_results:
        for category, comments in processed_results.items():
            print(f"Category: {category}")
            for comment in comments:
                print(f"  Comment: {comment['text'][:50]}...")  # Print first 50 chars of comment
                print(f"    Assigned Label: {comment['label']}")
                print(f"    Original Post Author: {comment['original_post_author']}")
                print(f"    Original Post Score: {comment['original_post_score']}")
                # Print other relevant fields from the comment dictionary as needed
                # For example:
                # if 'field_name' in comment:
                #     print(f"    Field Name: {comment['field_name']}")
            print("-" * 20)
    else:
        print("No processed results to display.")
    print("-----------------")

    return processed_results

def add_full_comment_info_to_results(results, all_data):
    """
    Adds the full comment information (excluding replies) and the original post's author and score
    to the analysis results.

    Args:
        results: The results dictionary from analyze_comments_batch.
        all_data: The original dictionary containing all thread data.

    Returns:
        A new dictionary with the same structure as 'results', but with added 'full_comment'
        and 'original_post' keys for each comment.
    """
    results_with_full_comments = {}
    comments = all_data['comments']
    original_post = all_data['original_post']
    original_post_author = original_post['author']
    original_post_score = original_post['score']

    # Treat the original post as the first "comment"
    all_comments = [
        {
            'author': original_post_author,
            'score': original_post_score,
            'body': original_post['body'],
            'depth': 0,  # You can set depth as needed for the original post
            'is_original_post': True  # Flag to indicate the original post
        }
    ] + comments

    for category, category_results in results.items():
        results_with_full_comments[category] = []
        for i, result in enumerate(category_results):
            full_comment = all_comments[i]

            # Create a new dictionary without the 'replies' key
            comment_without_replies = {
                k: v for k, v in full_comment.items() if k != "replies"
            }

            results_with_full_comments[category].append({
                "text": result["text"],
                "classification": result["classification"],
                "full_comment": comment_without_replies,
                "original_post_author": original_post_author,
                "original_post_score": original_post_score
            })

    return results_with_full_comments

def post_process_results(results):
    """
    Post-processes the analysis results, selecting the highest-confidence label for each comment
    (>= 60% confidence) and adding it to the comment data.

    Args:
        results: The dictionary of analysis results, including full comment information and
                 original post info.

    Returns:
        A dictionary with the same structure as the input 'results', but with an added
        'label' key for each comment containing the assigned label.
    """
    processed_results = {}

    for category, comment_results in results.items():
        processed_results[category] = []
        for comment_result in comment_results:
            text = comment_result["text"]
            classifications = comment_result["classification"]
            full_comment = comment_result["full_comment"]
            original_post_author = comment_result["original_post_author"]
            original_post_score = comment_result["original_post_score"]

            highest_confidence = 0
            top_label = "None"

            for classification in classifications:
                label = classification["label"]
                confidence = classification["confidence"]
                if confidence > highest_confidence:
                    highest_confidence = confidence
                    top_label = label

            if highest_confidence >= 60:
                final_label = top_label
            else:
                final_label = "None"

            # Add the final label and original post info to the comment data
            processed_comment = full_comment.copy()
            processed_comment["label"] = final_label
            processed_comment["text"] = text
            processed_comment["original_post_author"] = original_post_author
            processed_comment["original_post_score"] = original_post_score

            processed_results[category].append(processed_comment)

    return processed_results



async def analyze_comments_batch(session, comment_texts, label_sets):
    """
    Sends a batch of comments to the BART server for analysis.

    Args:
        session: The aiohttp ClientSession.
        comment_texts: A list of comment texts.
        label_sets: The label sets to use for analysis.

    Returns:
        A dictionary where keys are categories and values are lists of analysis results,
        in the same order as the input comment_texts.
    """

    # Edit here when you have bart cloud endpoint
    is_local = os.getenv("USE_LOCAL_LLM", "false").lower() == "true"
    base_url = os.getenv("BART_LOCAL_ENDPOINT_URL" if is_local else "BART_LOCAL_ENDPOINT_URL").rstrip('/')
    url = base_url  # The correct endpoint for your server

    payload = {
        "texts": comment_texts,
        "label_sets": label_sets,
    }

    try:
        async with session.post(url, json=payload) as response:
            if response.status == 200:
                all_results = await response.json()

                # Validate the structure of the response
                if not isinstance(all_results, dict):
                    print("Error: Server returned an invalid response (not a dictionary).")
                    return {}

                for category, results in all_results.items():
                    if not isinstance(results, list):
                        print(f"Error: Results for category '{category}' are not a list.")
                        return {}
                    if len(results) != len(comment_texts):
                        print(f"Error: Number of results for category '{category}' does not match the number of comments.")
                        return {}

                return all_results
            else:
                print(f"Error analyzing comments: {response.status}")
                return {}  # Return an empty dictionary on error
    except aiohttp.ClientConnectorError as e:
        print(f"Connection error: {e}")
        return {}
