def get_top_comments_by_ef_score(comments, limit=5):
    """
    Finds the top X comments in the entire comment tree based on their ef_score
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


def get_important_comments(comments, limit=5):
    """
    Identifies important comment pairs from the comment hierarchy.
    Modified to also include the parent's parent (grandparent) information when available.
    
    Args:
        comments (list): A list of comment dictionaries representing the comment hierarchy
        limit (int): Maximum number of pairs to return
        
    Returns:
        list: A list of tuples (parent, child), where parent includes its own parent information
        if available, sorted by ef_score difference in descending order.
    """
    important_pairs = []
    
    def traverse(parent, grandparent=None):
        for child in parent.get('replies', []):
            if child.get('ef_score', 0) > parent.get('ef_score', 0) and child.get('score', 0) != 1:
                # Create parent copy without replies but with its parent info
                parent_no_replies = {k: v for k, v in parent.items() if k != "replies"}
                if grandparent:
                    grandparent_no_replies = {k: v for k, v in grandparent.items() if k != "replies"}
                    parent_no_replies['parent_comment'] = grandparent_no_replies
                
                # Create child copy without replies
                child_no_replies = {k: v for k, v in child.items() if k != "replies"}
                
                important_pairs.append((parent_no_replies, child_no_replies))
            
            # Continue traversing with current child as parent
            traverse(child, parent)

    # Start traversal from each root comment
    for root_comment in comments:
        traverse(root_comment)

    # Sort by ef_score difference
    important_pairs.sort(key=lambda pair: pair[1].get('ef_score', 0) - pair[0].get('ef_score', 0), reverse=True)
    return important_pairs[:limit]

