import sys
import os
import pandas as pd
import json
from datetime import datetime, timezone

# Add parent directory to path to allow importing analyze_main
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from analyze_main import analyze_reddit_thread, fetch_thread_data

# Check if we're running in local mode
is_local = os.getenv("LOCAL_RUN", "false").lower() == "true"

# Set the cache CSV path accordingly
if is_local:
    CACHE_CSV_PATH = os.getenv("LOCAL_CACHE_CSV_PATH", "local_analyses.csv")
else:
    CACHE_CSV_PATH = os.getenv("CLOUD_CACHE_CSV_PATH", "reddit-links-bucket/analyses.csv")

# When reading the CSV:
dtype_mapping = {
    'url': str,
    'summary_focus': str, 
    'summary_length': str,
    'tone': str,
    'include_eli5': bool,
    'analyze_image': bool,
    'search_external': bool,
    'number_of_comments': int,
    'total_score': int,
    'total_ef_score': int,
    'analysis_result': str,
    'eli5_summary': str
    # notable_comments and timestamp will be handled automatically
}

def pre_filter_analyses(all_analyses, all_thread_data, summary_focus, summary_length, tone):
    """
    Pre-filters analyses based on URL, focus, length and tone.
    Returns empty DataFrame and empty indices list if no matches.
    Returns:
    Tuple of (Filtered DataFrame of potential matches, list of indices in original DataFrame)
    """
    # Ensure correct types in the DataFrame
    for col, dtype in dtype_mapping.items():
        if col in all_analyses.columns:
            all_analyses[col] = all_analyses[col].astype(dtype)
    
    if all_thread_data['original_post']:
        url = all_thread_data['original_post']['url']
    else:
        url = all_thread_data['url']
        
    filtered_analyses = all_analyses[
        (all_analyses['url'] == url) &
        (all_analyses['summary_focus'] == summary_focus) &
        (all_analyses['summary_length'] == summary_length) &
        (all_analyses['tone'] == tone)
    ]
    
    original_indices = filtered_analyses.index.tolist()
    print(f"Pre-filtered {len(filtered_analyses)} potential matches based on URL, focus, length, and tone.")
    return filtered_analyses, original_indices

def filter_by_params(filtered_analyses, original_indices, image, external):
    """
    Filters analyses based on image and external search parameters.
    Allows cached entries with more analysis than requested, but rejects those with less.
    
    Returns:
    Tuple of (DataFrame of analyses matching parameters, list of indices in original DataFrame)
    """
    if filtered_analyses.empty:
        print("No pre-filtered analyses to check parameters against")
        return filtered_analyses, []
        
    # If user wants image analysis, cached entry must have it
    # If user wants external search, cached entry must have it
    param_matches = filtered_analyses[
        filtered_analyses.apply(lambda row: 
            (not image or row['analyze_image']) and 
            (not external or row['search_external']), 
            axis=1
    )]
    
    # Get indices from original dataframe that match with param_matches
    # Use the position in filtered_analyses to lookup the correct index
    matched_indices = [original_indices[filtered_analyses.index.get_loc(idx)] 
                      for idx in param_matches.index]
    
    print(f"Found {len(param_matches)} matches with compatible image/external parameters")
    return param_matches, matched_indices

def find_best_match(param_filtered, param_indices, all_thread_data):
    """
    Finds best match from parameter-filtered analyses based on tolerances.
    Returns None and None if no match within tolerances.
    Returns:
    Tuple of (The matching row, original index) or (None, None) if no match.
    """
    if param_filtered.empty:
        print("No parameter matches to check tolerances against")
        return None, None
        
    comment_count, total_score, total_ef_score = count_all_comments(all_thread_data['comments'])
    
    # Check tolerances
    for i, row in enumerate(param_filtered.itertuples()):
        if check_all_tolerances(
            comment_count, total_score,
            row.number_of_comments, row.total_score
        ):
            return row, param_indices[i]
            
    print("No matches found within tolerances")
    return None, None

def generate_eli5_summary(all_thread_data, summary_focus, summary_length, tone, analyze_image, search_external, max_comments):
    """
    Generates only the ELI5 summary.
    """
    _, sum_for_5yo, _ = analyze_reddit_thread(
        all_thread_data, summary_focus, summary_length, tone,
        include_eli5=True, analyze_image=analyze_image, search_external=search_external, max_comments=max_comments, include_normal_summary=False
    )
    return sum_for_5yo

def perform_new_analysis(conn, all_thread_data, summary_focus, summary_length, tone, include_eli5, analyze_image, search_external, 
                         max_comments, all_analyses, replaceIndex=None):
    """
    Performs a new analysis and stores it in the cache.
    """
    # Check fetching one last time
    if not all_thread_data['original_post']:
        all_thread_data = fetch_thread_data(all_thread_data['url'])
        if all_thread_data['original_post'] is None:
            return "Failed to fetch thread data. Please try again later.", None, None
    
    # Perform the analysis
    analysis_result, sum_for_5yo, notable_comments = analyze_reddit_thread(
        all_thread_data, summary_focus, summary_length, tone,
        include_eli5, analyze_image, search_external, max_comments=max_comments
    )
    comment_count, total_score, total_ef_score = count_all_comments(all_thread_data['comments'])
    
    # Create new analysis entry
    new_analysis = {
        'url': all_thread_data['original_post']['url'],
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'summary_focus': summary_focus,
        'summary_length': summary_length,
        'tone': tone,
        'include_eli5': include_eli5,
        'analyze_image': analyze_image,
        'search_external': search_external,
        'number_of_comments': comment_count,
        'total_score': total_score,
        'total_ef_score': total_ef_score,
        'analysis_result': analysis_result,
        'eli5_summary': sum_for_5yo if sum_for_5yo else "",
        'notable_comments': json.dumps(notable_comments),
    }
    print("Adding new...")
    
    # Create DataFrame and enforce types
    new_df = pd.DataFrame([new_analysis])
    for col, dtype in dtype_mapping.items():
        if col in new_df.columns:
            new_df[col] = new_df[col].astype(dtype)
            
    if replaceIndex is not None:
        all_analyses.iloc[replaceIndex] = new_df.iloc[0]
        updated_df = all_analyses
    else:
        updated_df = pd.concat([all_analyses, new_df], ignore_index=True)
    
    # Ensure types are correct in the final DataFrame
    for col, dtype in dtype_mapping.items():
        if col in updated_df.columns:
            updated_df[col] = updated_df[col].astype(dtype)
    
    # Write to CSV
    if conn is None:
        # Local mode: write to local CSV file
        updated_df.to_csv(CACHE_CSV_PATH, index=False)
    else:
        # Cloud mode: write to S3 bucket
        with conn.open(CACHE_CSV_PATH, "w") as f:
            updated_df.to_csv(f, index=False)
    
    return analysis_result, sum_for_5yo, notable_comments

def update_eli5_in_cache(conn, all_analyses, sum_for_5yo, replaceIndex):
    print("----------UPDATE ONLY ELI5-----------")
    """Updates the eli5_summary in the cache."""
    
    # Create a dictionary with updated values, using iloc to access the row
    updated_row = all_analyses.iloc[replaceIndex].to_dict()  # Convert row to dictionary
    updated_row['eli5_summary'] = sum_for_5yo
    updated_row['include_eli5'] = True
    # Create a DataFrame from the updated dictionary
    updated_row_df = pd.DataFrame([updated_row])
    
    # Replace the row at the specified index
    all_analyses.iloc[replaceIndex] = updated_row_df.iloc[0]

    # Write to CSV
    if conn is None:
        # Local mode: write to local CSV file
        all_analyses.to_csv(CACHE_CSV_PATH, index=False)
    else:
        # Cloud mode: write to S3 bucket
        with conn.open(CACHE_CSV_PATH, "w") as f:
            all_analyses.to_csv(f, index=False)

def count_all_comments(comments):
    """
    Counts the total number of comments and replies in a nested comment structure,
    along with the sum of their scores and ef_scores.
    Args:
        comments: A list of comment dictionaries, where each dictionary has a 'replies' key
                  containing a list of sub-comment dictionaries.  Each dictionary
                  must have 'score' and 'ef_score' keys.
    Returns:
        A tuple containing:
          - The total number of comments and replies.
          - The total sum of 'score' values.
          - The total sum of 'ef_score' values.
    """
    count = 0
    total_score = 0
    total_ef_score = 0
    for comment in comments:
        count += 1  # Count the current comment
        total_score += comment['score']
        total_ef_score += comment['ef_score']
        if 'replies' in comment and comment['replies']:
            # Recursively count replies and their scores
            sub_count, sub_score, sub_ef_score = count_all_comments(comment['replies'])
            count += sub_count
            total_score += sub_score
            total_ef_score += sub_ef_score
    return count, total_score, total_ef_score

def check_all_tolerances(current_count, current_score,
                         cached_count, cached_score,
                         tp_comment=0.10, tp_score=0.30): # tp being tolerance percentage
    """
    Checks tolerances for count, score, and ef_score.  All inputs are now numbers.
    """
    # Comment tolerance check
    lower_bound_comment = cached_count * (1 - tp_comment)
    upper_bound_comment = cached_count * (1 + tp_comment)
    comment_passed = lower_bound_comment <= current_count <= upper_bound_comment
    # Score tolerance check
    lower_bound_score = cached_score * (1 - tp_score)
    upper_bound_score = cached_score * (1 + tp_score)
    score_passed = lower_bound_score <= current_score <= upper_bound_score
    return comment_passed and score_passed