# Secrets are loaded from .streamlit/secrets.toml via st.secrets (Streamlit's built-in secret management)
import os
import re
import traceback

import streamlit as st
from analysis import analysis_page
from cache_helpers import perform_new_analysis
from analyze_main_praw import fetch_thread_data


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

        /* Login form styling */
        .login-container {
            max-width: 400px;
            margin: 0 auto;
            padding: 2rem;
            background-color: #f8f9fa;
            border-radius: 1rem;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
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


def login():
    """Simple login function"""
    
    # Add sidebar with information from markdown file
    with st.sidebar:
        try:
            with open("frontend/marketing_content/sidebar.md", "r", encoding="utf-8") as f:
                sidebar_content = f.read()
            
            # Extract login page sidebar content (everything before the first "---")
            login_sections = sidebar_content.split("---")
            if len(login_sections) >= 2:
                login_sidebar = login_sections[0] + "---" + login_sections[1]
                st.markdown(login_sidebar)
            else:
                st.markdown("Sidebar content not found.")
        except FileNotFoundError:
            st.error("Sidebar content file not found. Please ensure 'frontend/marketing_content/sidebar.md' exists.")
        except Exception as e:
            st.error(f"Error reading sidebar content: {e}")
    
    st.image("frontend/images/pose_4.png", width=200)
    st.title("Midori Reddit")
    st.write(
        "Please enter the password you received from Jesse Casman "
        "to access the application.")

    # Get password from secrets or environment variable
    password = st.secrets.get("APP_PASSWORD", os.getenv("APP_PASSWORD", "midori2025"))
    
    user_password = st.text_input("Enter password:", type="password")
    if user_password == password:
        st.session_state["authenticated"] = True
        st.success("Login successful!")
        st.rerun()
    elif user_password:
        st.error("Incorrect password")
    
    # Read and display marketing content from markdown file
    try:
        with open("frontend/marketing_content/main_page.md", "r", encoding="utf-8") as f:
            marketing_content = f.read()
        
        # Split content by image markers and process each part
        import re
        
        # Pattern to match markdown image syntax: ![alt text](path)
        image_pattern = r'!\[([^\]]*)\]\(([^)]+)\)'
        
        # Split the content by image markers
        parts = re.split(image_pattern, marketing_content)
        
        # Process each part
        for i, part in enumerate(parts):
            if i % 3 == 0:  # This is text content
                if part.strip():
                    st.markdown(part)
            elif i % 3 == 1:  # This is alt text
                continue  # Skip alt text, we'll handle it with the image
            elif i % 3 == 2:  # This is image path
                try:
                    # Extract alt text from the previous part
                    alt_text = parts[i-1] if i > 0 else "Image"
                    st.image(part, caption=alt_text, width=400)
                except Exception as img_error:
                    st.error(f"Error loading image {part}: {img_error}")
                    
    except FileNotFoundError:
        st.error("Marketing content file not found. Please ensure 'frontend/marketing_content/main_page.md' exists.")
    except Exception as e:
        st.error(f"Error reading marketing content: {e}")


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
        try:
            with open("frontend/marketing_content/sidebar.md", "r", encoding="utf-8") as f:
                sidebar_content = f.read()
            
            # Extract home page sidebar content (section after "Home Page Sidebar")
            sections = sidebar_content.split("---")
            for i, section in enumerate(sections):
                if "Home Page Sidebar" in section:
                    # Get the content after "Home Page Sidebar" header
                    home_content = section.split("Home Page Sidebar")[1].strip()
                    st.markdown(home_content)
                    break
            else:
                st.markdown("### 🎯 How Midori Reddit works")
                st.markdown("""
                1. **Paste** a Reddit URL
                2. **Choose** your analysis options
                3. **Get** AI-powered insights
                """)
        except FileNotFoundError:
            st.error("Sidebar content file not found. Please ensure 'frontend/marketing_content/sidebar.md' exists.")
        except Exception as e:
            st.error(f"Error reading sidebar content: {e}")

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
            ["General Summary", "Custom Summary", "YouTube Content"],
            index=0 if st.session_state.summary_focus == "General Summary" else (
                1 if st.session_state.summary_focus == "Custom Summary" else 2
            ),
            key="summary_focus_option"
        )

    with col2:
        # Text area for custom summary focus (allows longer input)
        if summary_focus_option == "Custom Summary":
            summary_focus = st.text_area(
                "Oppkey Reddit campaigns include strong reporting to show "
                "the quantifiable value of our client's spend. "
                "Custom instructions can produce reports for clients or "
                "internal strategy meetings. "
                "Examples: Technical breakdown of the main arguments, "
                "community sentiment and reactions, "
                "future predictions and implications, etc.):",
                value=st.session_state.summary_focus if (
                    st.session_state.summary_focus != "General Summary" and 
                    st.session_state.summary_focus != "YouTube Content"
                ) else "",
                max_chars=300,
                height=100,
                key="summary_focus_input"
            )
        elif summary_focus_option == "YouTube Content":
            youtube_focus = st.text_area(
                "Oppkey Reddit campaigns are often used with YouTube small influencer campaigns. "
                "After content is posted to Reddit, Oppkey engages and develops a strategy for more "
                "content. Midori will analyze Reddit comments and produce a recommendation for "
                "next steps in the influencer and content marketing campaigns.",
                value="Create 10 video topics from the comments with two points for each video topic.",
                max_chars=300,
                height=100,
                key="summary_focus_input",
                disabled=False
            )
            summary_focus = youtube_focus
        else:
            summary_focus = "General Summary"
            st.text(
                "Oppkey Reddit campaigns may start with posting content from our client "
                "or from the Oppkey Developer Network. "
                "A General Summary is a good starting point "
                "to understand the Reddit comments and prioritize with "
                "Midori's score. "
                "Use Custom Summary for deeper analysis."
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

            # Debug: Check environment and secrets
            print("Environment check:")
            print(f"  - LOCAL_RUN: {os.getenv('LOCAL_RUN', 'not set')}")
            print(f"  - Available secrets: {list(st.secrets.keys()) if hasattr(st.secrets, 'keys') else 'no secrets'}")
            print(f"  - Thread data fetched: {all_thread_data is not None}")
            if all_thread_data:
                print(f"  - Thread data keys: {list(all_thread_data.keys())}")

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
    st.markdown("""
                # Understanding Midori
                """)
    
    st.image("frontend/images/businessmidori.png", width=300, use_container_width=False)
    
    st.markdown("""
                In addition to a general summary, Midori can write custom reports,
                including analyzing the comments and post to recommend
                video topics and blog posts.

                ## Midori Score

                The Midori ef_score displayed on the analysis page is calculated by multiplying a
                comment's score by its depth, where depth = 1 indicates a root comment
                (one without a parent). This approach highlights comment quality
                more effectively than just using raw scores, as upvoting a deeply
                nested comment is somewhat less common.

                ## Comment Ranking System

                - **Best Comments Tab**: Ranks comments in **descending order** of
                    `ef_score`.

                - **Important Comments Tab**:
                    Also uses `ef_scores`, but ranks comments based on the **increase in
                    ef_score from parent to child**.
                    This highlights replies that introduce **significant new information**—
                    for example, when a reply corrects an error in the parent comment.


                ## Limitations

                - External links are searched for additional context only if the website
                    does not require JavaScript or has no strict protections. Links to
                    GitHub and Hugging Face work, but X links do not. PDF summaries are
                    also unavailable.

                - Images and GIFs in comments appear as links in the Best/Important
                    comments section, allowing users to click and view them. However,
                    they will not be displayed on the analysis page.

                """)


def main():
    try:
        # Initialize authentication state
        if "authenticated" not in st.session_state:
            st.session_state["authenticated"] = False

        # Check if user is authenticated
        if not st.session_state["authenticated"]:
            login()
        else:
            # Add logout button in sidebar
            with st.sidebar:
                if st.button("🚪 Logout"):
                    st.session_state["authenticated"] = False
                    st.session_state.pop("analysis_result", None)
                    st.session_state.pop("page", None)
                    st.rerun()

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