import sys
import os

import streamlit as st
from analysis import analysis_page, dummy_analysis_page

# Add parent directory to path to allow importing scrape
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scrape import analyze_reddit_thread, dummy_analyze

# Configure the default settings
st.set_page_config(
    page_title="URL Analyzer",
    page_icon="🔍",
    layout="wide"
)

# Custom CSS for better styling
st.markdown("""
    <style>
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
        .stButton>button {
            width: 100%;
            background-color: #ff4b4b;
            color: white;
            font-weight: 500;
        }
        .stButton>button:hover {
            background-color: #ff3333;
            color: white;
        }
    </style>
""", unsafe_allow_html=True)

def home_page():
    # Header
    st.markdown("""
        <div class="main-header">
            <p class="header-text">🔍 URL Analyzer</p>
            <p class="subheader-text">Analyze any website with our powerful tool</p>
        </div>
    """, unsafe_allow_html=True)

    # Main content
    col1, col2 = st.columns([2, 1])
    
    with col1:
        url = st.text_input("Enter website URL", placeholder="https://example.com")
    
    with col2:
        st.write("")  # Add some spacing
        st.write("")  # Add some spacing
        if st.button("Analyze"):
            if url:
                # Call the analyze_reddit_thread function
                analysis_result = analyze_reddit_thread(url)
                # analysis_result = dummy_analyze(url)
                # Store the result in session state
                st.session_state.analysis_result = analysis_result
                # Navigate to the analysis page
                st.session_state.page = "analysis"
                st.rerun()

    # Example section
    st.markdown("### 📊 What you'll get")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
            🎯 **Traffic Analysis**
            - Visitor demographics
            - Traffic sources
            - User behavior
        """)
    
    with col2:
        st.markdown("""
            📱 **Technical Insights**
            - Mobile compatibility
            - Page load speed
            - SEO score
        """)
    
    with col3:
        st.markdown("""
            🔑 **Key Metrics**
            - Engagement rate
            - Bounce rate
            - Conversion rate
        """)

# Main app logic
def main():
    if 'page' not in st.session_state:
        st.session_state.page = "home"

    if st.session_state.page == "home":
        home_page()
    else:
        analysis_page(st.session_state.analysis_result)

if __name__ == "__main__":
    main()