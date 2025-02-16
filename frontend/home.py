from dotenv import load_dotenv
import os
import re
import json

import streamlit as st
from st_files_connection import FilesConnection
from analysis import analysis_page
from cache_helpers import pre_filter_analyses, filter_by_params, find_best_match, update_eli5_in_cache, generate_eli5_summary, perform_new_analysis

try:
    from analyze_main import fetch_thread_data
except:
    import importlib.util
    import os
    
    # Get the absolute path to analyze_main.py
    module_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'analyze_main.py')
    
    # Load the module dynamically
    spec = importlib.util.spec_from_file_location("analyze_main", module_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    
    # Get the function
    fetch_thread_data = module.fetch_thread_data


load_dotenv()
REDDIT_URL_PATTERN = r"^https?://(www\.)?reddit\.com/r/.*/comments/.*"

# Configure the default settings
st.set_page_config(
    page_title="URL Analyzer",
    page_icon="🔍",
    layout="wide"
)

# Custom CSS for better styling
st.markdown("""
    <style>
        /* Main header styling */
        .main-header {
            background-color: #f0f2f6;
            padding: 1.5rem;
            border-radius: 0.7rem;
            margin-bottom: 2rem;
        }
        .header-text {
            color: #1f1f1f;
            font-size: 2.3rem;
            font-weight: 600;
            margin-bottom: 0.8rem;
        }
        .subheader-text {
            color: #4f4f4f;
            font-size: 1.1rem;
        }

        /* Button styling */
        .stButton>button {
            background-color: #ff4b4b;
            color: white;
            font-weight: 500;
            border-radius: 0.5rem;
            padding: 0.5rem 1rem;
            width: 100%;
        }
        .stButton>button:hover {
            background-color: #ff3333;
            color: white;
        }

        /* Input field styling */
        .stTextInput>div>div>input {
            border-radius: 0.5rem;
            padding: 0.5rem;
        }

        /* Radio button styling */
        .stRadio>div {
            flex-direction: row;
            gap: 1rem;
        }
        .stRadio>div>label {
            margin-bottom: 0;
        }

        /* Dropdown styling */
        .stSelectbox>div>div>select {
            border-radius: 0.5rem;
            padding: 0.5rem;
        }
    </style>
""", unsafe_allow_html=True)

def home_page():
    # Header
    st.markdown("""
        <div class="main-header">
            <p class="header-text">🔍 URL Analyzer</p>
            <p class="subheader-text">Analyze a Reddit thread with an LLM</p>
        </div>
    """, unsafe_allow_html=True)

    if "summary_focus" not in st.session_state:
        st.session_state.summary_focus = "General Summary"  # Default value

    if "summary_length" not in st.session_state:
        st.session_state.summary_length = "Medium"  # Default value

    # Main content
    st.markdown("---")  # Horizontal line for separation

    # URL Input
    url = st.text_input("Enter Reddit Thread URL", placeholder="https://www.reddit.com/r/example/comments/...", on_change=on_url_change)

    is_valid_url = bool(re.match(REDDIT_URL_PATTERN, url))
    if not is_valid_url:
        st.error("Please enter a valid Reddit thread URL")

    st.markdown("---")  # Horizontal line for separation

    # Summary Focus and Summary Length Section
    st.markdown("### Summary Options")
    col1, col2, col3, col4 = st.columns([1, 2, 1, 1])  # Adjusted column widths to accommodate new column

    with col1:
        # Radio button for summary focus (stacked vertically)
        summary_focus_option = st.radio(
            "Choose Summary Type:",
            ["General Summary", "Custom Summary"],
            index=0 if st.session_state.summary_focus == "General Summary" else 1,
            key="summary_focus_option"
        )

    with col2:
        # Text box for custom summary focus (fatter but shorter)
        if summary_focus_option == "Custom Summary":
            summary_focus = st.text_input(
                "What the summary should focus on: (Max 50 characters. Examples: Technical breakdown, community sentiment, future predictions, etc.):",
                value=st.session_state.summary_focus if st.session_state.summary_focus != "General Summary" else "",
                max_chars=50,
                key="summary_focus_input"
            )
        else:
            summary_focus = "General Summary"
            st.text_input(
                "What the summary should focus on: (Max 50 characters. Examples: Technical breakdown, community sentiment, future predictions, etc.):",
                value="General Summary",
                max_chars=50,
                key="summary_focus_input",
                disabled=True
            )

    with col3:
        # Dropdown for summary length
        summary_length = st.selectbox(
            "Summary Length (proportional to original thread's length):",
            ["Short", "Medium", "Long"],
            index=1 # Default to "Medium"
        )
        st.session_state.summary_length = summary_length

    with col4:
        # Dropdown for tone selection
        tone = st.selectbox(
            "Summary Tone:",
            ["Teacher", "Pompous", "Foulmouthed", "Clickbaiter_Youtuber"],
            index=0,  # Default to "Normal"
            key="tone_selector"
        )

    # Single small column for Advanced Settings
    small_col = st.columns([0.25, 0.75])[0]  # Only get the first column
    
    with small_col:
        # Advanced Settings section using expander with arrow icon
        with st.expander("⚙️ Advanced"):
            # Pre-ticked checkbox for "Explain like I'm 5" section
            include_eli5 = st.checkbox(
                "Include an Explain like I'm 5 section",
                value=True,
                key="include_eli5"
            )
            
            # Checkbox for analyzing images in the main post
            analyze_image = st.checkbox(
                "Run image analysis on the main post", 
                value=True,
                key="analyze_image"
            )

            # Checkbox for searching external links
            search_external = st.checkbox(
                "Search external links", 
                value=False,
                key="search_external"
            )

    st.markdown("---")  # Horizontal line for separation

    if st.button("Analyze", key="analyze_button"):
        if not url:
            st.warning("Please enter a Reddit thread URL.")
        elif not is_valid_url:
            st.warning("Please enter a valid Reddit thread URL.")
        else:
            st.session_state.url = url
            st.session_state.summary_focus = summary_focus
            st.session_state.summary_length = summary_length
            st.session_state.tone = tone

            with st.spinner("Checking for existing analysis..."):
                conn = st.connection('s3', type=FilesConnection)

                # Initialize variables to avoid UnboundLocalError
                analysis_result = None
                sum_for_5yo = None
                notable_comments = None
                all_thread_data = fetch_thread_data(url)

                try:
                    # Use a try-except block to handle potential file reading errors
                    try:
                        all_analyses = conn.read("reddit-links-bucket/analyses.csv", input_format="csv", ttl=0)
                        print(f"Read {len(all_analyses)} existing analyses from cache.")
                    except Exception as e:  # Catch broader exceptions during read
                        print(f"Error reading existing analyses: {e}")
                        all_analyses = None # Set to None so we perform new analysis

                    # 1. Pre-filter on core params (big 4)
                    filtered_analyses, core_indices = pre_filter_analyses(all_analyses, all_thread_data, summary_focus, summary_length, tone)

                    if filtered_analyses.empty:
                        # No matches for core params - perform new analysis and append to cache
                        print("home.py: No matches for core parameters. Performing new analysis to append to cache.")
                        analysis_result, sum_for_5yo, notable_comments = perform_new_analysis(
                            conn, all_thread_data, summary_focus, summary_length, tone, include_eli5,
                            analyze_image, search_external, all_analyses)
                    else:
                        # 2. Filter by image/external parameters
                        param_filtered, param_indices = filter_by_params(filtered_analyses, core_indices, image=analyze_image, external=search_external)
                        
                        if param_filtered.empty:
                            # Core params matched but image/external didn't - replace cache entry
                            print("home.py: Core parameters matched but image/external didn't. Performing new analysis to replace cache entry.")
                            cache_index = core_indices[0]  # Get first match's index from main cache
                            analysis_result, sum_for_5yo, notable_comments = perform_new_analysis(
                                conn, all_thread_data, summary_focus, summary_length, tone, include_eli5,
                                analyze_image, search_external, all_analyses, cache_index)
                        else:
                            # 3. Find best match within tolerances
                            best_match, cache_index = find_best_match(param_filtered, param_indices, all_thread_data)
                            
                            if best_match is not None:
                                # Good match found within tolerances - use cache
                                print("home.py: Using existing analysis from cache.")
                                # Convert named tuple to dictionary with _asdict()
                                best_match_dict = best_match._asdict()
                                analysis_result = best_match_dict['analysis_result']
                                notable_comments = json.loads(best_match_dict['notable_comments'])
                                sum_for_5yo = best_match_dict.get('eli5_summary')

                                if include_eli5 and not best_match_dict.get('include_eli5'):
                                    print("home.py: Generating ELI5 summary (requested but not in cache).")
                                    sum_for_5yo = generate_eli5_summary(url, summary_focus, summary_length, tone, analyze_image, search_external)
                                    update_eli5_in_cache(conn, all_analyses, best_match, sum_for_5yo)
                                    st.success("Retrieved existing analysis and generated ELI5 summary!")
                                else:
                                    st.success("Retrieved existing analysis!")
                            else:
                                # Matches exist but exceed tolerance - replace cache entry
                                print("home.py: Matches found but exceed tolerance. Performing new analysis to replace cache entry.") 
                                cache_index = param_indices[0]  # Get first match's index from main cache
                                analysis_result, sum_for_5yo, notable_comments = perform_new_analysis(
                                    conn, all_thread_data, summary_focus, summary_length, tone, include_eli5,
                                    analyze_image, search_external, all_analyses, cache_index)

                except FileNotFoundError:
                    print("No existing analyses file. Performing new analysis.")
                    analysis_result, sum_for_5yo, notable_comments = perform_new_analysis(
                        conn, all_thread_data, summary_focus, summary_length, tone, include_eli5,
                        analyze_image, search_external, all_analyses)

                st.session_state.analysis_result = analysis_result
                st.session_state.sum_for_5yo = sum_for_5yo
                st.session_state.notable_comments = notable_comments
                st.session_state.page = "analysis"
                st.rerun()

# Main app logic
def main():
    if 'page' not in st.session_state:
        st.session_state.page = "home"

    if st.session_state.page == "home":
        home_page()
    else:
        analysis_page(st.session_state.analysis_result, st.session_state.sum_for_5yo, st.session_state.notable_comments)

# Clear previous results when URL changes
def on_url_change():
    st.session_state.pop("analysis_result", None)


if __name__ == "__main__":
    main()