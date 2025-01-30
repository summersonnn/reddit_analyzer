import streamlit as st
import plotly.express as px
import pandas as pd

def analysis_page(analysis_result_old, analysis_result, sum_for_5yo, notable_comments):
    # Header
    st.markdown("""
        <div class="main-header">
            <p class="header-text">📊 Analysis Results</p>
            <p class="subheader-text">Detailed insights for: {}</p>
        </div>
    """.format(st.session_state.get('url', 'Unknown URL')), unsafe_allow_html=True)

    # Display the previous analysis result
    st.markdown("### 📝 Previous Analysis Summary") 
    st.markdown(f"<p style='font-size: 16px;'>{analysis_result_old}</p>", unsafe_allow_html=True)

    # Horizontal line separator
    st.markdown("---")

    # Display the new analysis result
    st.markdown("### 📝 Latest Analysis Summary")
    st.markdown(f"<p style='font-size: 16px;'>{analysis_result}</p>", unsafe_allow_html=True)

    # Display summary for 5-years old
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

    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("SEO Score", "87%", "+12%")
    with col2:
        st.metric("Load Time", "1.2s", "-0.3s")
    with col3:
        st.metric("Mobile Score", "92%", "+5%")
    with col4:
        st.metric("Security Score", "95%", "+2%")

    # Traffic Sources Chart
    st.markdown("### 📈 Traffic Sources")
    traffic_data = pd.DataFrame({
        'Source': ['Organic', 'Direct', 'Social', 'Referral', 'Email'],
        'Percentage': [45, 25, 15, 10, 5]
    })
    fig = px.pie(traffic_data, values='Percentage', names='Source', hole=0.4)
    st.plotly_chart(fig, use_container_width=True)

    # User Demographics
    st.markdown("### 👥 User Demographics")
    col1, col2 = st.columns(2)
    
    with col1:
        demographics_data = pd.DataFrame({
            'Age': ['18-24', '25-34', '35-44', '45-54', '55+'],
            'Users': [250, 380, 420, 280, 170]
        })
        fig = px.bar(demographics_data, x='Age', y='Users')
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        locations_data = pd.DataFrame({
            'Country': ['USA', 'UK', 'Canada', 'Australia', 'Others'],
            'Users': [450, 280, 180, 120, 170]
        })
        fig = px.bar(locations_data, x='Country', y='Users')
        st.plotly_chart(fig, use_container_width=True)

    # Return to home button
    if st.button("⬅️ Analyze Another URL"):
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