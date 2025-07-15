# Secrets are loaded from .streamlit/secrets.toml via st.secrets (Streamlit's built-in secret management)
import os
import re
import traceback

import streamlit as st
from analysis import analysis_page
from cache_helpers import perform_new_analysis
from analyze_main import fetch_thread_data


REDDIT_URL_PATTERN = r"^https?://(www\.)?reddit\.com/r/.*/comments/.*"

# Configure the default settings
st.set_page_config(
    page_title="Midori Reddit",
    page_icon="frontend/images/favicon.ico",
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
            font-size: 3.5rem;
            font-weight: 700;
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

# # Check if we're running in local mode
# is_local = os.getenv("LOCAL_RUN", "false").lower() == "true"

# Set the cache CSV path accordingly
# Disable caching for Streamlit Cloud deployment
is_local = False  # Force cloud mode to avoid file system issues
if is_local:
    CACHE_CSV_PATH = st.secrets.get("LOCAL_CACHE_CSV_PATH", os.getenv("LOCAL_CACHE_CSV_PATH"))
else:
    CACHE_CSV_PATH = st.secrets.get("CLOUD_CACHE_CSV_PATH", os.getenv("CLOUD_CACHE_CSV_PATH"))


def home_page():
    # Header with logo
    col1, col2 = st.columns([1, 3])

    with col1:
        st.image("frontend/images/pose_1.png", width=150)

    with col2:
        st.markdown("""
            <div class="main-header">
                <p class="header-text">💬 Midori Reddit</p>
                <p class="subheader-text">Analyze a Reddit thread with an LLM</p>
            </div>
        """, unsafe_allow_html=True)

    # Sidebar with graphics (optional)
    with st.sidebar:
        st.markdown("### 🎯 How Midori Reddit works")
        # Example: st.image("frontend/graphics/process-flow.png", use_column_width=True)
        st.markdown("""
        1. **Paste** a Reddit URL
        2. **Choose** your analysis options
        3. **Get** AI-powered insights
        """)

    if "summary_focus" not in st.session_state:
        st.session_state.summary_focus = "General Summary"  # Default value

    if "summary_length" not in st.session_state:
        st.session_state.summary_length = "Medium"  # Default value

    if "url" not in st.session_state:
        st.session_state.url = ""

    # Main content
    st.markdown("---")  # Horizontal line for separation

    # URL Input - Added key and value for persistence and on_change removal
    url = st.text_input(
        "Enter Reddit Thread URL",
        placeholder="https://www.reddit.com/r/example/comments/...",
        value=st.session_state.url,
        key="url_input",
        on_change=on_url_change
    )
    st.session_state.url = url

    st.markdown("---")  # Horizontal line for separation

    # Summary Focus and Summary Length Section
    st.markdown("---")
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
            "Summary Length:",
            ["Short", "Medium", "Long"],
            index=1  # Default to "Medium"
        )
        st.session_state.summary_length = summary_length

    with col4:
        # Dropdown for tone selection
        tone = st.selectbox(
            "Summary Tone:",
            [
                "Teacher", "Foulmouthed", "Cut the Bullshit", "Clickbaiter Youtuber",
                "Chill Bro", "Valley Girl", "Motivational Speaker", "Pirate",
                "Time Traveler", "Zen Master"
            ],
            index=0,  # Default to "Teacher"
            key="tone_selector"
        )

    # Single small column for Advanced Settings
    small_col = st.columns([0.25, 0.75])[0]  # Only get the first column

    with small_col:
        # Advanced Settings section using expander with arrow icon
        with st.expander("⚙️ Advanced"):
            # Pre-ticked checkbox for "Explain like I'm 5" section
            include_eli5 = st.checkbox(
                "Include an 'Explain like I'm 5' section",
                value=False,
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

            # Maximum number of important comments selection
            max_comments = st.selectbox(
                "Maximum number of best/important comments to show in the analysis page",
                options=range(3, 11),
                index=2,  # Default to 5 (index 2 corresponds to value 5)
                key="max_comments"
            )

    st.markdown("---")  # Horizontal line for separation

    if st.button("Put Midori to work!", key="analyze_button"):
        # Add status message container at the start
        status_container = st.container()

        def add_status(message, icon="ℹ️"):
            with status_container:
                status_container.empty()
                st.text(f"{icon} {message}")

        is_valid_url = bool(re.match(REDDIT_URL_PATTERN, url))
        if not is_valid_url:
            st.error("Please enter a valid Reddit thread URL")
        else:
            # Update session state
            st.session_state.url = url
            st.session_state.summary_focus = summary_focus
            st.session_state.summary_length = summary_length
            st.session_state.tone = tone

            all_thread_data = fetch_thread_data(url)

            # Always perform fresh analysis for Streamlit Cloud
            add_status("Performing fresh analysis...", "🔄")
            analysis_result, sum_for_5yo, notable_comments = perform_new_analysis(
                None,  # No cache connection
                all_thread_data, summary_focus, summary_length, tone, include_eli5,
                analyze_image, search_external, max_comments, None
            )

            # Update session state
            st.session_state.analysis_result = analysis_result
            st.session_state.sum_for_5yo = sum_for_5yo
            st.session_state.notable_comments = notable_comments
            st.session_state.cache_time = None  # No cache time for fresh analysis
            st.session_state.page = "analysis"
            st.rerun()


def main():
    try:
        if 'page' not in st.session_state:
            st.session_state.page = "home"

        if st.session_state.page == "home":
            home_page()
        elif ('analysis_result' in st.session_state and
               st.session_state.analysis_result is not None):  # Check for analysis result
            analysis_page(
                st.session_state.analysis_result,
                st.session_state.sum_for_5yo,
                st.session_state.notable_comments
            )
        else:  # Handle case of opening /analysis directly
            st.error("No analysis to display. Please go to the Home page and enter a URL.")
            if st.button("Go to Home"):
                st.session_state.page = 'home'
                st.rerun()

    except Exception:  # Remove unused variable 'e'
        # 1. Log the error (VERY IMPORTANT!)
        st.error("An unexpected error occurred.  Please try again later. ")  # User-friendly message
        traceback.print_exc()  # Log the FULL traceback to console (or file)
        # Stop further execution.  Essential to prevent the default Streamlit error handler from showing the code.
        st.stop()


# Clear previous results when URL changes (keep this, but outside the try block)
def on_url_change():
    st.session_state.pop("analysis_result", None)


if __name__ == "__main__":
    main()