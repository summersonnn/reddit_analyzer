def get_top_three_comments_by_ef_score(comments, limit=3):
    """
    Finds the top three comments in the entire comment tree based on their ef_score
    and returns them in descending order along with their parent comments.

    Args:
        comments (list): List of comment dictionaries. Each comment contains keys such as
                         'author', 'score', 'ef_score', 'body', 'depth', and 'replies'.

    Returns:
        list: A list of at most three tuples. Each tuple contains two dictionaries:
              (main_comment, parent_comment)
              Comments are ordered by ef_score in descending order.
              If a comment has no parent (top-level), parent_comment will be None.
    """
    all_comments = []
    parent_map = {}  # Maps comment to its parent

    def traverse(comment, parent=None):
        # Store reference to parent
        parent_map[id(comment)] = parent
        
        all_comments.append(comment)
        for reply in comment.get('replies', []):
            traverse(reply, comment)

    # Traverse the entire comment tree
    for comment in comments:
        traverse(comment)

    # Sort all comments by ef_score in descending order and pick the top three
    top_three = sorted(all_comments, key=lambda c: c.get('ef_score', 0), reverse=True)[:limit]

    # For each comment, create tuple with cleaned comment and its parent
    result = []
    for comment in top_three:
        main_comment = {k: v for k, v in comment.items() if k != "replies"}
        parent = parent_map[id(comment)]
        parent_comment = {k: v for k, v in parent.items() if k != "replies"} if parent else None
        result.append((main_comment, parent_comment))
    
    return result


# A comment is imported if its ef_score is bigger than its parent's ef_score
# When you find such comment pairs (parent and child), put them in a list as a tuple.
# You must order the list by the difference between the child's ef_score and the parent's ef_score in descending order.
def get_important_comments(comments, limit=3):
    """
    Identifies important comment pairs from the comment hierarchy.

    A comment pair (parent, child) is considered important if the child's ef_score
    is greater than the parent's ef_score, and the child's score is not equal to 1.
    The function recursively traverses the comment tree to collect such pairs.
    When a pair is found, the 'replies' key is removed from both the parent and child
    comments before adding them to the list. Finally, the pairs are sorted in descending
    order based on the difference between the child's ef_score and the parent's ef_score.

    Args:
        comments (list): A list of comment dictionaries. Each dictionary represents a comment
                         and includes keys such as 'author', 'score', 'ef_score', 'body', 'depth',
                         and 'replies' (which is a list of sub-comments).

    Returns:
        list: A list of tuples, where each tuple contains a parent comment and its child comment
              (both without the 'replies' key), sorted by the difference
              (child's ef_score - parent's ef_score) in descending order.
    """
    important_pairs = []

    def traverse(parent):
        for child in parent.get('replies', []):
            if child.get('ef_score', 0) > parent.get('ef_score', 0) and child.get('score', 0) != 1:
                parent_no_replies = {k: v for k, v in parent.items() if k != "replies"}
                child_no_replies = {k: v for k, v in child.items() if k != "replies"}
                important_pairs.append((parent_no_replies, child_no_replies))
            traverse(child)

    for root_comment in comments:
        traverse(root_comment)

    important_pairs.sort(key=lambda pair: pair[1].get('ef_score', 0) - pair[0].get('ef_score', 0), reverse=True)
    return important_pairs[:limit]

