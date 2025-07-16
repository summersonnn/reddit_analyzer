# Midori Reddit Analyzer 🔍

This is a fork of [Reddit Analyzer](https://github.com/summersonnn/reddit_analyzer) by Summersonnn

This project leverages LLMs to analyze Reddit threads, offering concise summaries and key insights. It helps users grasp lengthy discussions quickly. For an entertaining learning experience, try selecting one of the humorous tones! This project is intended purely for educational purposes, with the main goal of avoiding the need to spend half an hour reading an entire thread.

The original project is also hosted free [here](https://reddit-thread-analyzer.streamlit.app) which you can try. It uses LLama 3.3-70B-instruct as the LLM and llama-3.2-11b-vision-instruct as VLM.

[Watch the video](https://www.youtube.com/watch?v=ukPT68vi4m4)

## 📝 Editing Marketing Content (For Marketing Team)

**Non-developers can easily edit the application's marketing content without touching any code!**

### What Can Be Edited

The following content can be modified by editing simple markdown files:

- **Main marketing content** (login page)
- **Sidebar content** (both login and home pages)
- **Images** (using standard markdown image syntax)

### File Locations

All marketing content is located in the `frontend/marketing_content/` folder:

```
frontend/marketing_content/
├── main_page.md    # Main marketing content (login page)
└── sidebar.md      # Sidebar content for all pages
```

### How to Edit

1. **Main Content**: Edit `frontend/marketing_content/main_page.md`
   - Use standard markdown syntax
   - Add images with: `![Alt text](frontend/images/image_name.png)`
   - Available images: `businessmidori.png`, `pose_1.png` through `pose_5.png`, `ai-human.png`, etc.

2. **Sidebar Content**: Edit `frontend/marketing_content/sidebar.md`
   - Content is organized by page sections
   - Use `---` to separate different sections

### Example Edits

**Adding an image:**
```markdown
![Midori Business](frontend/images/businessmidori.png)
```

**Updating text:**
```markdown
## New Section Title

Your updated marketing content here.
```

### Important Notes

- **No code knowledge required** - just edit the markdown files
- **Images must be in `frontend/images/`** folder
- **Changes take effect immediately** when you save the files
- **Backup your changes** before making major edits
- **Test your changes** by running the application locally

### Getting Help

If you need to add new images or make structural changes, contact the development team. For content updates, you can work independently using any text editor.

## Features

*   **Reddit Thread Analysis:**  Accepts Reddit thread URLs for analysis.
*   **Summary Customization:**
    *   **Length:** Short, Medium, or Long summaries.
    *   **Tone:**  Various tones available (Teacher, Foulmouthed, Cut the Bullshit, etc.).
    *   **Focus:** General or custom focus for summaries.
*   **Advanced Options:**
    *   **ELI5 Summary:**  Simplified explanation.
    *   **Image & Link Analysis:**  Processes images and external links in the main post.
    *   **Top Comment Display:**  Highlights best/important comments (adjustable quantity).
*   **Caching:**  Improves performance for repeated analyses.
*   **Streamlit Interface:**  User-friendly web application.

## Getting Started

### Prerequisites

*   Python 3.11+
*   Streamlit (installed during setup)
*   API Key for an LLM provider (e.g., OpenRouter). Or Local LLM server API (must be OpenAI compatible)

### Installation & Setup

1.  **Clone Repository:**

    ```bash
    git clone https://github.com/codetricity/midori_reddit
    cd midori reddit
    ```

2.  **Virtual Environment with uv (Recommended):**

If uv is not already installed:
`curl -LsSf https://astral.sh/uv/install.sh | sh`

`uv venv`

3.  **Install Dependencies:**

    ```bash
    uv pip install -r requirements.txt
    ```

    **Note for Streamlit Cloud Deployment:**
    
    The project includes a `uv.lock` file for reproducible deployments on Streamlit Cloud. If you're installing dependencies with `uv pip install` and need to update the lock file, run:
    
    ```bash
    uv lock
    ```
    
    This will generate/update the `uv.lock` file based on your current `requirements.txt` and `pyproject.toml`.

4.  **Configuration (`.streamlit/secrets.toml` file):**

    Create `secrets.toml` in the `.streamlit` directory that is hidden in the project root with the following for local use:

    ```toml
    LOCAL_RUN = "true"
    LLM_BASE_URL = "https://openrouter.ai/api/v1"
    LLM_API_KEY = "sk-or-v1-alflalkjfjafljk"
    MODEL_NAME = "meta-llama/llama-3.3-70b-instruct"
    VLM_NAME = "meta-llama/llama-3.2-11b-vision-instruct"
    LOCAL_CACHE_CSV_PATH = "analyses.csv"


    # Reddit API credentials (for PRAW)
    REDDIT_CLIENT_ID = "valfadjfdsaj..."
    REDDIT_CLIENT_SECRET = "w-gdljaflaljdf..."
    REDDIT_USER_AGENT = "NameOfRedditApp"

    APP_PASSWORD = "LoginPassword"
    ```



    **Important Notes:**  
    - Replace the placeholder values with your actual LLM provider details.  
    - The `LOCAL_RUN='true'` setting is required for local execution. Don't confuse this with Local LLMs. You can still enter API information from inference providers (such as Openrouter). Or you can enter the config of your locally running LLM.
    - Proxies are not necessary for local runs, as data retrieval from Reddit generally works fine with a residential IP.  

    <details>
    <summary><h3><b>Using Proxies</b></h3></summary>

    If you ever need to set `LOCAL_RUN='false'` (for example, to use a proxy), you'll also need to create a `secrets.toml` file inside the `.streamlit` directory in the project root. This file should contain your proxy credentials if required:

    ```env
    # Add proxy credentials here if needed

5.  **Run Application:**

    ```bash
    uv run streamlit run frontend/home.py
    ```

    Access the application in your browser. I disabled auto e-mail asking of streamlit but if it asks anyway, just type some dummy e-mail.

## Usage

1.  **Enter Reddit URL:** Input the thread URL on the homepage.
2.  **Customize Summary:** Select Summary Type, Focus (if custom), Length, and Tone.
3.  **Advanced Settings (Optional):** Configure ELI5, image/link analysis, and top comment count under "⚙️ Advanced".
4.  **Analyze:** Click "Analyze".
5.  **Review Results:**  View analysis summary, ELI5 (if enabled), and notable comments on the results page.

## Some Information about Analysis

The ef_score displayed on the analysis page is calculated by multiplying a comment's score by its depth, where depth = 1 indicates a root comment (one without a parent). This approach highlights comment quality more effectively than just using raw scores, as upvoting a deeply nested comment is somewhat less common.

### Comment Ranking System  

- **Best Comments Tab**:  
  Ranks comments in **descending order** of `ef_score`.  

- **Important Comments Tab**:  
  Also uses `ef_scores`, but ranks comments based on the **increase in ef_score from parent to child**.  
  This highlights replies that introduce **significant new information**—for example, when a reply corrects an error in the parent comment.  


## Limitations 
- External links are searched for additional context only if the website does not require JavaScript or has no strict protections. Links to GitHub and Hugging Face work, but X links do not. PDF summaries are also unavailable. This feature wasn't a primary focus, as it's just an extra addition rather than a core part of the project. Therefore I didn't spend much time on it.

- Images and GIFs in comments appear as links in the Best/Important comments section, allowing users to click and view them. However, they will not be displayed on the analysis page.
