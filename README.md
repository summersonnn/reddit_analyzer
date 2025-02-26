# Reddit Thread Analyzer 🔍

[![Streamlit App](https://img.shields.io/badge/Streamlit-App-orange?style=flat-square&logo=streamlit)](https://streamlit.io/)
[![Python](https://img.shields.io/badge/Python-3.9+-blue?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=flat-square)](https://opensource.org/licenses/MIT)

<br />

This project leverages LLMs to analyze Reddit threads, offering concise summaries and key insights. It helps users grasp lengthy discussions quickly. For an entertaining learning experience, try selecting one of the humorous tones! This project is intended purely for educational purposes, with the main goal of avoiding the need to spend half an hour reading an entire thread.

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

*   Python 3.9+
*   Streamlit (installed during setup)
*   API Key for an LLM provider (e.g., OpenRouter). Or Local LLM server API (must be OpenAI compatible)

### Installation & Setup

1.  **Clone Repository:**

    ```bash
    git clone https://github.com/summersonnn/reddit_analyzer/tree/main
    cd reddit_analyzer
    ```

2.  **Virtual Environment (Recommended):**

    ```bash
    python -m venv venv
    source venv/bin/activate  # Linux/macOS
    venv\Scripts\activate  # Windows
    ```

3.  **Install Dependencies:**

    ```bash
    pip install -r requirements.txt
    ```

4.  **Configuration (`.env` file):**

    Create `.env` in the project root with the following for local use:

    ```env
    LOCAL_RUN='true'
    LLM_BASE_URL=YOUR_LLM_BASE_URL_HERE
    LLM_API_KEY=YOUR_API_KEY_HERE
    MODEL_NAME=YOUR_LLM_MODEL_NAME_HERE
    VLM_NAME=YOUR_VLM_MODEL_NAME_HERE (can be same as the MODEL_NAME)
    LOCAL_CACHE_CSV_PATH=analyses.csv

    # Optional for local run:
    # PROXY_HTTP=YOUR_HTTP_PROXY_HERE
    # PROXY_HTTPS=YOUR_HTTPS_PROXY_HERE
    # CLOUD_CACHE_CSV_PATH=reddit-links-bucket/analyses.csv
    ```

    **Note:** Replace placeholders with your actual LLM provider details and API key.  `LOCAL_RUN='true'` is essential for local execution.
    You won't need cloud cache csv path and proxy for local usage as getting data from reddit is successfull with a residential ip anyway. 
    You will need to create an "analyses.csv" in the project root folder manually if you opt for a local run. This will be your cache.

6.  **Run Application:**

    ```bash
    streamlit run frontend/home.py
    ```

    Access the application in your browser.

## Usage

1.  **Enter Reddit URL:** Input the thread URL on the homepage.
2.  **Customize Summary:** Select Summary Type, Focus (if custom), Length, and Tone.
3.  **Advanced Settings (Optional):** Configure ELI5, image/link analysis, and top comment count under "⚙️ Advanced".
4.  **Analyze:** Click "Analyze".
5.  **Review Results:**  View analysis summary, ELI5 (if enabled), and notable comments on the results page.

## Some Information about Analysis

The ef_score displayed on the analysis page is calculated by multiplying a comment’s score by its depth, where depth = 1 indicates a root comment (one without a parent). This approach highlights comment quality more effectively than just using raw scores, as upvoting a deeply nested comment is somewhat less common (!), I suppose.

### Comment Ranking System  

- **Best Comments Tab**:  
  Ranks comments in **descending order** of `ef_score`.  

- **Important Comments Tab**:  
  Also uses `ef_scores`, but ranks comments based on the **increase in ef_score from parent to child**.  
  This highlights replies that introduce **significant new information**—for example, when a reply corrects an error in the parent comment.  




## Contributing

Feel free to contribute in any way. Bug fixes are welcomed.
Also looking for good system prompts for new tones!

## License

This project is licensed under the **MIT License**. See `LICENSE` for details.

## Questions or Issues

For questions, bug reports, or feature requests, please open an issue on GitHub.

