import streamlit as st
import plotly.express as px
import pandas as pd

def analysis_page(analysis_result, sum_for_5yo, notable_comments):
    # Header
    st.markdown("""
        <div class="main-header">
            <p class="header-text">📊 Analysis Results</p>
            <p class="subheader-text">Detailed insights for: {}</p>
        </div>
    """.format(st.session_state.get('url', 'Unknown URL')), unsafe_allow_html=True)

    # Display the  analysis result
    st.markdown("### 📝 Analysis Summary") 
    st.markdown(f"<p style='font-size: 16px;'>{analysis_result}</p>", unsafe_allow_html=True)

    # Horizontal line separator
    st.markdown("---")

    # Display summary for 5-years old (conditional)
    if sum_for_5yo is not None:
        st.markdown("### 📝 Summary for 5-years old")
        st.markdown(f"<p style='font-size: 16px;'>{sum_for_5yo}</p>", unsafe_allow_html=True)
        # Horizontal line separator
        st.markdown("---")

    st.markdown("### 📝 Notable comments")

    # --- Button and expander section ---
    comment_types = [
        "Comment with Highest Score",
        "Root Comment with Highest Score",
        "Comment with Most Subcomments",
        "Comment with Most Direct Subcomments"
    ]

    for i, (comment_body, value, is_root) in enumerate(notable_comments):
        if st.button(comment_types[i]):
            with st.expander(f"See {comment_types[i]}", expanded=True):
                if comment_body:
                    st.markdown(f"- Comment: {comment_body}")
                    if comment_types[i] in ["Comment with Highest Score", "Root Comment with Highest Score"]:
                        st.markdown(f"- Score: {value}")
                    elif comment_types[i] == "Comment with Most Subcomments":
                        st.markdown(f"- Total Subcomments: {value}")
                    elif comment_types[i] == "Comment with Most Direct Subcomments":
                        st.markdown(f"- Direct Subcomments: {value}")
                    st.markdown(f"- Is Root Comment: {is_root}")
                else:
                    st.markdown("- No comment found for this criteria.")

    # Return to home button
    if st.button("⬅️ Analyze Another"):
        st.session_state.page = "home"
        st.rerun()

def dummy_analysis_page(analysis_result):
    # Header
    st.markdown("""
        <div class="main-header">
            <p class="header-text">📊 Analysis Results</p>
            <p class="subheader-text">Detailed insights for: {}</p>
        </div>
    """.format(st.session_state.get('url', 'Unknown URL')), unsafe_allow_html=True)

    # Display the analysis result as a paragraph
    st.markdown("### 📝 Analysis Summary")
    st.markdown(f"<p style='font-size: 16px;'>{analysis_result}</p>", unsafe_allow_html=True)