import os
from typing import List, Dict
from openai import OpenAI  # Import the synchronous OpenAI client

def chat_completion(
    chat_history: List[Dict[str, str]],
    temperature: float = 0.2
) -> str:
    """
    Unified chat completion function for both local and cloud LLMs using OpenAI-compatible API.
    """
    # Determine if we're using local or cloud based on environment
    is_local = os.getenv("USE_LOCAL_LLM", "false").lower() == "true"
    
    # Get complete base URL with path
    base_url = os.getenv("BASE_URL" if is_local else "CLOUD_BASE_URL").rstrip('/')
    api_key = os.getenv("VLLM_API_KEY" if is_local else "CLOUD_LLM_API_KEY").rstrip('/')
    model = os.getenv("MODEL_PATH" if is_local else "CLOUD_MODEL_NAME")

    # Create OpenAI client
    client = OpenAI(
        api_key=api_key,
        base_url=base_url,
    )

    # Prepare request parameters
    request_params = {
        "model": model,
        "messages": chat_history.copy(),
        "temperature": temperature,
    }

    try:
        response = client.chat.completions.create(**request_params)
        return response.choices[0].message.content
    except Exception as e:
        print(f"Full base URL: {base_url}")
        print(f"Request params: {request_params}")
        raise