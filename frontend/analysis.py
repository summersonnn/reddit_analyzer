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
        st.markdown("### 📝 ELI5")
        st.markdown(f"<p style='font-size: 16px;'>{sum_for_5yo}</p>", unsafe_allow_html=True)
        # Horizontal line separator
        st.markdown("---")

    st.markdown("### 📝 Notable comments")
 
    # Initialize session state for button toggling if not exists
    if 'active_button' not in st.session_state:
        st.session_state.active_button = None

    # Create buttons and handle display
    if st.button("Best Comments", key="button_0"):
        if st.session_state.active_button == 0:
            st.session_state.active_button = None
        else:
            st.session_state.active_button = 0

    if st.button("Important Comments", key="button_1"):
        if st.session_state.active_button == 1:
            st.session_state.active_button = None
        else:
            st.session_state.active_button = 1

    # Display content based on active button
    if st.session_state.active_button == 0:
        with st.expander("See Best Comments", expanded=True):
            display_best_comments(notable_comments[0])
    elif st.session_state.active_button == 1:
        with st.expander("See Important Comments", expanded=True):
            display_important_comments(notable_comments[1])

    # Return to home button
    if st.button("⬅️ Analyze Another"):
        st.session_state.page = "home"
        st.rerun()


def display_best_comments(comments_group):
    """Display the top comments with their parent context"""
    if comments_group:
        for idx, (main_comment, parent_comment) in enumerate(comments_group, start=1):
            st.markdown(f"**Comment {idx}:**")
            
            # Display parent comment if it exists (provides context)
            if parent_comment:
                st.markdown("*Context:*")
                st.markdown(f"{parent_comment.get('body', 'No content available')}")
                st.markdown(f"- Score: {parent_comment.get('score', 'N/A')}")
                st.markdown(f"- ef_score: {parent_comment.get('ef_score', 'N/A')}")
                st.markdown("*Top Comment:*")
            
            # Display main comment
            st.markdown(f"{main_comment.get('body', 'No content available')}")
            st.markdown(f"- Score: {main_comment.get('score', 'N/A')}")
            st.markdown(f"- ef_score: {main_comment.get('ef_score', 'N/A')}")
            st.markdown("---")
    else:
        st.markdown("- No top comments found.")

def display_important_comments(comments_group):
    """Display the parent-child pairs where child outperforms parent"""
    if comments_group:
        for idx, (parent_comment, child_comment) in enumerate(comments_group, start=1):
            st.markdown(f"**Important Comment Pair {idx}:**")
            
            # Display parent comment
            st.markdown("*Parent Comment:*")
            st.markdown(f"{parent_comment.get('body', 'No content available')}")
            st.markdown(f"- Score: {parent_comment.get('score', 'N/A')}")
            st.markdown(f"- ef_score: {parent_comment.get('ef_score', 'N/A')}")
            
            # Display child comment that outperformed parent
            st.markdown("*Reply that Outperformed Parent:*")
            st.markdown(f"{child_comment.get('body', 'No content available')}")
            st.markdown(f"- Score: {child_comment.get('score', 'N/A')}")
            st.markdown(f"- ef_score: {child_comment.get('ef_score', 'N/A')}")
            
            # Show the improvement
            ef_score_diff = child_comment.get('ef_score', 0) - parent_comment.get('ef_score', 0)
            st.markdown(f"*Improvement in ef_score: +{ef_score_diff:.2f}*")
            st.markdown("---")
    else:
        st.markdown("- No important comment pairs found.")