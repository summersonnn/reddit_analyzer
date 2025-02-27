import streamlit as st
from streamlit.components.v1 import html
import pandas as pd

def analysis_page(analysis_result, sum_for_5yo, notable_comments):
    # Display cache information if available
    if 'cache_time' in st.session_state and st.session_state.cache_time is not None:
        st.markdown(
            f"""
            <div style="background-color:#e6ffe6;padding:10px;border-radius:5px;">
                <p style="color:black;font-size:14px;">
                    <strong>Analysis fetched from the cache.</strong> 
                    Time when the analysis was made: {st.session_state.cache_time}
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # Header
    st.markdown("""
        <div class="main-header">
            <p class="header-text">📊 Analysis Results</p>
            <p class="subheader-text">Detailed insights for: {}</p>
        </div>
    """.format(st.session_state.get('url', 'Unknown URL')), unsafe_allow_html=True)

    # Display the analysis result
    st.markdown("### 📝 Analysis Summary")
    st.markdown(analysis_result)

    # Horizontal line separator
    st.markdown("---")

    # Display summary for 5-year-olds (conditional)
    if sum_for_5yo is not None:
        st.markdown("### 📝 ELI5")
        st.markdown(sum_for_5yo)
        # Horizontal line separator
        st.markdown("---")

    st.markdown("### 📝 Notable comments")

    # Initialize session state for button toggling if not exists
    if 'active_button' not in st.session_state:
        st.session_state.active_button = 0  # Open "Best Comments" by default

    # Updated CSS for green buttons
    st.markdown(
        """
        <style>
        .stButton > button {
            background-color: #28a745;
            color: white;
            border: none;
            width: 100%;
        }
        .stButton > button:hover {
            background-color: #218838;
            color: white;
            border: none;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # Create buttons and handle display in columns
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Best Comments", key="button_0"):
            if st.session_state.active_button == 0:
                st.session_state.active_button = None
            else:
                st.session_state.active_button = 0

    with col2:
        if st.button("Important Comments", key="button_1"):
            if st.session_state.active_button == 1:
                st.session_state.active_button = None
            else:
                st.session_state.active_button = 1

    # Display content based on active button
    if st.session_state.active_button == 0:
        with st.expander("See Best Comments: These are ranked by the ef_score (score multiplied by the depth)", expanded=True):
            display_best_comments(notable_comments[0])
    elif st.session_state.active_button == 1:
        with st.expander("See Important Comments: These are ranked by the largest ef_score increase from parent to child.", expanded=True):
            display_important_comments(notable_comments[1])

    # Return to home button
    if st.button("⬅️ Analyze Another"):
        st.session_state.page = "home"
        st.rerun()



def display_best_comments(comments_group):
    """Display the top comments with their parent context"""
    if comments_group:
        for main_comment, parent_comment in comments_group:
            # Create two columns for icon and content with better proportions
            col1, col2 = st.columns([0.5, 10])
            
            with col1:
                st.markdown('<div style="font-size: 24px; text-align: center;">👤</div>', unsafe_allow_html=True)
            
            with col2:
                # Author name
                st.markdown(f"**u/{main_comment.get('author', '[deleted]')}**")
                
                # Main comment content
                st.markdown(main_comment.get('body', 'No content available'))
                
                # Score and effective score with tooltip
                score = main_comment.get('score', 'N/A')
                ef_score = main_comment.get('ef_score', 'N/A')
                st.markdown(f"""
                    <div style="display: flex; align-items: center; gap: 15px;">
                        <span>▲ {score} ▼</span>
                        <span title="This score is calculated by multiplying the score of the comment with its depth" 
                              style="display: flex; 
                                     align-items: center; 
                                     color: #1e88e5; 
                                     cursor: help;">
                            <span style="font-size: 16px; margin-right: 4px;">⚡</span> {ef_score}
                        </span>
                    </div>
                """, unsafe_allow_html=True)

                # Label indicating parent context
                if parent_comment:
                    st.markdown("""
                        <div style="margin-top: 15px; font-style: italic; color: #666;">
                            This was a reply to:
                        </div>
                    """, unsafe_allow_html=True)

                    # Parent comment box
                    st.markdown(f"""
                        <div style="
                            background-color: #f6f7f8;
                            border: 1px solid #e3e3e3;
                            border-radius: 4px;
                            padding: 10px;
                            margin-top: 5px;
                            font-size: 0.9em;">
                            <strong>u/{parent_comment.get('author', '[deleted]')}</strong><br>
                            {parent_comment.get('body', 'No content available')}<br>
                            <span style="color: #666;">▲ {parent_comment.get('score', 'N/A')} ▼</span>
                            <span style="color: #1e88e5; margin-left: 15px;" 
                                  title="This score is calculated by multiplying the score of the comment with its depth">
                                <span style="font-size: 16px;">⚡</span> {parent_comment.get('ef_score', 'N/A')}
                            </span>
                        </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown("""
                        <div style="margin-top: 15px; font-style: italic; color: #666;">
                            This was a root comment. No parent available.
                        </div>
                    """, unsafe_allow_html=True)
                
                # Separator between comments
                st.markdown("---")
    else:
        st.markdown("No comments found.")

def display_important_comments(comments_group):
    """Display the parent-child pairs where child outperforms parent"""
    if 'expanded_comments' not in st.session_state:
        st.session_state.expanded_comments = set()

    if comments_group:
        for comment_id, (parent_comment, child_comment) in enumerate(comments_group):
            # Child comment display
            col1, col2 = st.columns([0.5, 10])
            with col1:
                st.markdown(
                    '<div style="font-size: 24px; text-align: center;">👤</div>', 
                    unsafe_allow_html=True
                )
            with col2:
                # Child author and content
                st.markdown(f"**u/{child_comment.get('author', '[deleted]')}**")
                st.markdown(child_comment.get('body', 'No content available'))
                
                # Score details
                score = child_comment.get('score', 'N/A')
                ef_score = child_comment.get('ef_score', 'N/A')
                ef_score_diff = child_comment.get('ef_score', 0) - parent_comment.get('ef_score', 0)
                st.markdown(f"""
                    <div style="display: flex; align-items: center; gap: 15px;">
                        <span>▲ {score} ▼</span>
                        <span title="This score is calculated by multiplying the score of the comment with its depth" 
                              style="display: flex; align-items: center; color: #1e88e5; cursor: help;">
                            <span style="font-size: 16px; margin-right: 4px;">⚡</span> {ef_score}
                        </span>
                        <span title="This comment's effective score improved by this amount compared to its parent comment" 
                              style="color: #4CAF50; font-weight: bold; cursor: help;">
                            <span style="font-size: 16px;">📈</span> +{ef_score_diff:.2f}
                        </span>
                    </div>
                """, unsafe_allow_html=True)

                # Label indicating the parent context
                st.markdown("""
                    <div style="margin-top: 15px; font-style: italic; color: #666;">
                        This comment outperformed its parent below:
                    </div>
                """, unsafe_allow_html=True)

                # Parent comment box
                if 'parent_comment' in parent_comment and parent_comment.get('parent_comment'):
                    # Render the parent's comment box
                    st.markdown(f"""
                        <div style="
                            background-color: #f6f7f8;
                            border: 1px solid #e3e3e3;
                            border-radius: 4px;
                            padding: 10px;
                            margin-top: 5px;
                            font-size: 0.9em;">
                            <strong>u/{parent_comment.get('author', '[deleted]')}</strong><br>
                            {parent_comment.get('body', 'No content available')}<br>
                            <span style="color: #666;">▲ {parent_comment.get('score', 'N/A')} ▼</span>
                            <span style="color: #1e88e5; margin-left: 15px;" 
                                  title="This score is calculated by multiplying the score of the comment with its depth">
                                <span style="font-size: 16px;">⚡</span> {parent_comment.get('ef_score', 'N/A')}
                            </span>
                        </div>
                    """, unsafe_allow_html=True)
                    
                    # Toggle button to show/hide the grandparent
                    expand_key = f"expand_{comment_id}"
                    if st.button("💬 Click to see the grandparent comment 💬", key=expand_key):
                        if comment_id in st.session_state.expanded_comments:
                            st.session_state.expanded_comments.remove(comment_id)
                        else:
                            st.session_state.expanded_comments.add(comment_id)
                else:
                    st.markdown(f"""
                        <div style="
                            background-color: #f6f7f8;
                            border: 1px solid #e3e3e3; 
                            border-radius: 4px;
                            padding: 10px;
                            margin-top: 5px;
                            font-size: 0.9em;">
                            <strong>u/{parent_comment.get('author', '[deleted]')}</strong><br>
                            {parent_comment.get('body', 'No content available')}<br>
                            <span style="color: #666;">▲ {parent_comment.get('score', 'N/A')} ▼</span>
                            <span style="color: #1e88e5; margin-left: 15px;" 
                                  title="This score is calculated by multiplying the score of the comment with its depth">
                                <span style="font-size: 16px;">⚡</span> {parent_comment.get('ef_score', 'N/A')}
                            </span>
                        </div>
                    """, unsafe_allow_html=True)

                # Display grandparent only if the toggle is active
                if comment_id in st.session_state.expanded_comments:
                    # Add safety check for parent_comment key
                    if 'parent_comment' in parent_comment and parent_comment['parent_comment']:
                        grandparent = parent_comment['parent_comment']
                        st.markdown(f"""
                            <div style="
                                margin-top: 10px;
                                margin-left: 20px;
                                padding-left: 10px;
                                border-left: 2px dashed #ccc;">
                                <div style="
                                    background-color: #f0f0f0;
                                    border: 1px solid #e3e3e3;
                                    border-radius: 4px;
                                    padding: 10px;
                                    margin-top: 5px;
                                    font-size: 0.85em;">
                                    <div style="color: #666; margin-bottom: 5px;">Earlier in the thread:</div>
                                    <strong>u/{grandparent.get('author', '[deleted]')}</strong><br>
                                    {grandparent.get('body', 'No content available')}<br>
                                    <span style="color: #666;">▲ {grandparent.get('score', 'N/A')} ▼</span>
                                    <span style="color: #1e88e5; margin-left: 15px;" 
                                          title="This score is calculated by multiplying the score of the comment with its depth">
                                        <span style="font-size: 16px;">⚡</span> {grandparent.get('ef_score', 'N/A')}
                                    </span>
                                </div>
                            </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.info("No grandparent comment available")
                
                # Separator between comment pairs
                st.markdown("---")
    else:
        st.markdown("No important comment pairs found.")



          
