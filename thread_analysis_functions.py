def get_comment_with_highest_score(comments):
    """
    Finds the comment with the highest score in the entire comment tree and returns it along with its score and whether it's a root comment.

    Args:
        comments (list): List of comment dictionaries.

    Returns:
        tuple: (comment, score, is_root) where:
            - `comment` is the comment with the highest score.
            - `score` is its score.
            - `is_root` is a boolean indicating whether the comment is a root comment.
    """
    highest_score_comment = None
    max_score = -float('inf')

    def traverse(comment, is_root):
        nonlocal highest_score_comment, max_score
        if comment['score'] > max_score:
            max_score = comment['score']
            highest_score_comment = (comment, is_root)
        for reply in comment['replies']:
            traverse(reply, False)  # Replies are not root comments

    for comment in comments:
        traverse(comment, True)  # Root comments are at depth 0

    if highest_score_comment:
        comment, is_root = highest_score_comment
        return (comment['body'], max_score, is_root)
    return (None, -1, False)  # Fallback if no comments exist

def get_root_comment_with_highest_score(comments):
    """
    Finds the root comment with the highest score and returns it along with its score and whether it's a root comment.

    Args:
        comments (list): List of comment dictionaries.

    Returns:
        tuple: (comment, score, is_root) where:
            - `comment` is the root comment with the highest score.
            - `score` is its score.
            - `is_root` is a boolean indicating whether the comment is a root comment (always True here).
    """
    highest_score_comment = None
    max_score = -float('inf')

    for comment in comments:
        if comment['depth'] == 0 and comment['score'] > max_score:
            max_score = comment['score']
            highest_score_comment = comment

    if highest_score_comment:
        return (highest_score_comment['body'], max_score, True)
    return (None, -1, False)  # Fallback if no root comments exist

def get_comment_with_most_subcomments(comments):
    """
    Finds the comment (root or sub-comment) with the most sub-comments (recursively counted) and returns it along with the count and whether it's a root comment.

    Args:
        comments (list): List of comment dictionaries.

    Returns:
        tuple: (comment, count, is_root) where:
            - `comment` is the comment with the most sub-comments.
            - `count` is the total number of sub-comments.
            - `is_root` is a boolean indicating whether the comment is a root comment.
    """
    most_subcomments_comment = None
    max_subcomments = -1

    def count_subcomments(comment):
        count = 0
        for reply in comment['replies']:
            count += 1 + count_subcomments(reply)
        return count

    def traverse(comment, is_root):
        nonlocal most_subcomments_comment, max_subcomments
        subcomment_count = count_subcomments(comment)
        if subcomment_count > max_subcomments:
            max_subcomments = subcomment_count
            most_subcomments_comment = (comment, is_root)
        for reply in comment['replies']:
            traverse(reply, False)  # Replies are not root comments

    for comment in comments:
        traverse(comment, True)  # Root comments are at depth 0

    if most_subcomments_comment:
        comment, is_root = most_subcomments_comment
        return (comment['body'], max_subcomments, is_root)
    return (None, -1, False)  # Fallback if no comments exist

def get_comment_with_most_direct_subcomments(comments):
    """
    Finds the comment (root or sub-comment) with the most direct sub-comments and returns it along with the count and whether it's a root comment.

    Args:
        comments (list): List of comment dictionaries.

    Returns:
        tuple: (comment, count, is_root) where:
            - `comment` is the comment with the most direct sub-comments.
            - `count` is the number of direct sub-comments.
            - `is_root` is a boolean indicating whether the comment is a root comment.
    """
    most_direct_subcomments_comment = None
    max_direct_subcomments = -1

    def traverse(comment, is_root):
        nonlocal most_direct_subcomments_comment, max_direct_subcomments
        direct_subcomments = len(comment['replies'])
        if direct_subcomments > max_direct_subcomments:
            max_direct_subcomments = direct_subcomments
            most_direct_subcomments_comment = (comment, is_root)
        for reply in comment['replies']:
            traverse(reply, False)  # Replies are not root comments

    for comment in comments:
        traverse(comment, True)  # Root comments are at depth 0

    if most_direct_subcomments_comment:
        comment, is_root = most_direct_subcomments_comment
        return (comment['body'], max_direct_subcomments, is_root)
    return (None, -1, False)  # Fallback if no comments exist