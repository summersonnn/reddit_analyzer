import sys
import os
import pandas as pd
import json
from datetime import datetime

# # Add parent directory to path to allow importing analyze_main
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from analyze_main import analyze_reddit_thread

def find_best_match(all_analyses, url, summary_focus, summary_length, tone, image, external):
    """
    Finds a matching analysis in the cache based on core parameters.
    Returns the matching row and its index, or (None, None) if no match found.
    """
    matching_base = all_analyses[
        (all_analyses['url'] == url) & 
        (all_analyses['summary_focus'] == summary_focus) &
        (all_analyses['summary_length'] == summary_length) &
        (all_analyses['tone'] == tone)
    ]
    
    print(f"INSIDE FIND_BEST_MATCH:Found {len(matching_base)} potential matches based on URL, focus, length, and tone.")
    
    if not matching_base.empty:
        # If only one match, return it
        if len(matching_base) == 1:
            best_match = matching_base.iloc[0]
            match_index = matching_base.index[0]
        # If multiple matches, further filter based on image and external params
        else:
            # Further filter based on image and external params
            best_matches = matching_base[
                (matching_base['analyze_image'] == image) &
                (matching_base['search_external'] == external)
            ]
            
            if not best_matches.empty:
                best_match = best_matches.iloc[0] 
                match_index = best_matches.index[0]
            else:
                # If no exact match with image/external, use first base match
                best_match = matching_base.iloc[0]
                match_index = matching_base.index[0]
                
        print(f"Found a match with index {match_index}.")
        return best_match, match_index
    else:
        print("INSIDE FIND_BEST_MATCH: No potential matches found.") 
        return None, None


def generate_eli5_summary(url, summary_focus, summary_length, tone):
    """
    Generates only the ELI5 summary.
    """

    _, sum_for_5yo, _ = analyze_reddit_thread(
        url, summary_focus, summary_length, tone,
        include_eli5=True, analyze_image=False, search_external=False, include_normal_summary=False
    )
    return sum_for_5yo

def perform_new_analysis(conn, url, summary_focus, summary_length, tone, include_eli5, analyze_image, search_external, 
                        all_analyses):
    """
    Performs a new analysis and stores it in the cache.
    Can either add a new entry or replace an existing one based on parameters.
    """
    # Perform the analysis
    analysis_result, sum_for_5yo, notable_comments = analyze_reddit_thread(
        url, summary_focus, summary_length, tone,
        include_eli5, analyze_image, search_external
    )

    # Create new analysis entry
    new_analysis = {
        'url': url,
        'timestamp': datetime.now().isoformat(),
        'summary_focus': summary_focus,
        'summary_length': summary_length,
        'tone': tone,
        'include_eli5': include_eli5,
        'analyze_image': analyze_image,
        'search_external': search_external,
        'analysis_result': analysis_result,
        'eli5_summary': sum_for_5yo if sum_for_5yo else "",
        'notable_comments': json.dumps(notable_comments)
    }

    print("Adding new...")
    # Create DataFrame from new analysis and append to existing analyses
    new_df = pd.DataFrame([new_analysis])
    updated_df = pd.concat([all_analyses, new_df], ignore_index=True)

    # Write the updated DataFrame to S3
    with conn.open("reddit-links-bucket/analyses.csv", "w") as f:
        updated_df.to_csv(f, index=False)

    return analysis_result, sum_for_5yo, notable_comments

def update_eli5_in_cache(conn, all_analyses, best_match, sum_for_5yo):
    print("----------UPDATE ONLY ELI5-----------")
    """Updates the eli5_summary in the cache."""
    best_match['eli5_summary'] = sum_for_5yo
    best_match['include_eli5'] = True
    updated_row_df = pd.DataFrame([best_match])

    # Correctly identify the row using the same key as find_best_match
    update_mask = (all_analyses['url'] == best_match['url']) & \
                  (all_analyses['summary_focus'] == best_match['summary_focus']) & \
                  (all_analyses['summary_length'] == best_match['summary_length']) & \
                  (all_analyses['tone'] == best_match['tone'])

    all_analyses.loc[update_mask] = updated_row_df.iloc[0] # Update using the correct mask

    # Use conn.open() to get a file-like object, and pandas to_csv to write
    with conn.open("reddit-links-bucket/analyses.csv", "w") as f:
        all_analyses.to_csv(f, index=False)