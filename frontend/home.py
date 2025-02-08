import sys
from dotenv import load_dotenv
import os

import streamlit as st
from analysis import analysis_page

# Add parent directory to path to allow importing analyze_main
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from analyze_main import analyze_reddit_thread

load_dotenv()

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
    url = st.text_input("Enter Reddit Thread URL", placeholder="https://www.reddit.com/r/example/comments/...")

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
            index=1  # Default to "Medium"
        )
        st.session_state.summary_length = summary_length

        # Pre-ticked checkbox for "Explain like I'm 5" section
        include_eli5 = st.checkbox(
            "Include a Explain like I'm 5 section",
            value=True,
            key="include_eli5"
        )

    with col4:
        # Dropdown for tone selection
        tone = st.selectbox(
            "Summary Tone:",
            ["Teacher", "Pompous", "Foulmouthed", "Clickbaiter_Youtuber"],
            index=0,  # Default to "Normal"
            key="tone_selector"
        )

    st.markdown("---")  # Horizontal line for separation

    # Analyze Button
    if st.button("Analyze", key="analyze_button"):
        if url:
            # Store the URL, summary focus, and summary length in session state
            st.session_state.url = url
            st.session_state.summary_focus = summary_focus
            st.session_state.summary_length = summary_length
            st.session_state.tone = tone

            # Run analysis
            analysis_result, sum_for_5yo, notable_comments = analyze_reddit_thread(url, summary_focus, summary_length, include_eli5, tone)

            # Store the results in session state
            st.session_state.analysis_result = analysis_result
            st.session_state.sum_for_5yo = sum_for_5yo
            st.session_state.notable_comments = notable_comments

            # Navigate to the analysis page
            st.session_state.page = "analysis"
            st.rerun()
        else:
            st.warning("Please enter a valid Reddit thread URL.")

# Main app logic
def main():
    if 'page' not in st.session_state:
        st.session_state.page = "home"

    if st.session_state.page == "home":
        home_page()
    else:
        analysis_page(st.session_state.analysis_result, st.session_state.sum_for_5yo, st.session_state.notable_comments)

if __name__ == "__main__":
    main()