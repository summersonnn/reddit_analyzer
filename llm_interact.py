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

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()

    # Check if the model is multimodal and adjust the chat history accordingly
    is_multimodal = False

    chat_history = [
        {"role": "system", "content": "You are a helpful assistant."},
    ]
    
    if is_multimodal:
        chat_history.append({
            "role": "user",
            "content": [
                {
                    "type": "image_url",
                    "image_url": {
                        "url": "https://i.redd.it/ij7ubrn3mkfe1.jpeg"
                    }
                },
                {
                    "type": "text",
                    "text": "Describe what's on this image:"
                }
            ]
        })
    else:
        chat_history.append({
            "role": "user",
            "content": "Who won the superbowl in 2020?"
        })

    try:
        response = chat_completion(chat_history)
        print(f"Assistant: {response}")

    except Exception as e:
        print(f"An error occurred: {e}")


"""Try this:

chat_history = [
    {
        "role": "user",
        "content": [
            # Post
            {"type": "text", "text": "POST: [Post text]"},
            {"type": "image_url", "image_url": {"url": "post-image.jpg"}},
            
            # Comment 1
            {"type": "text", "text": "COMMENT 1: [Comment text]"},
            {"type": "image_url", "image_url": {"url": "comment1-image.jpg"}},
            
            # Comment 2 (text-only, no image)
            {"type": "text", "text": "COMMENT 2: [Comment text]"},
            
            # Final instruction for thread summary
            {"type": "text", "text": "Summarize the entire thread, including key details from the post and comments above."}
        ]
    }
]
"""