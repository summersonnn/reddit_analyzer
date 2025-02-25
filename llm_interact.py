import os
from typing import List, Dict
from openai import OpenAI
from openai import AsyncOpenAI
# import time

def chat_completion(
    chat_history: List[Dict[str, str]],
    temperature: float = 0.9,
    is_image=False
) -> str:
    """
    Unified chat completion function using OpenAI-compatible API.
    """
    base_url = os.getenv("LLM_BASE_URL").rstrip('/')
    api_key = os.getenv("LLM_API_KEY").rstrip('/')
    model = os.getenv("VLM_NAME" if is_image else "MODEL_NAME")

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

async def async_chat_completion(
    chat_history: List[Dict[str, str]],
    temperature: float = 0.9,
    is_image: bool = False
) -> str:
    """
    Asynchronous chat completion function using OpenAI-compatible API.
    """
    base_url = os.getenv("LLM_BASE_URL").rstrip('/')
    api_key = os.getenv("LLM_API_KEY").rstrip('/')
    model = os.getenv("VLM_NAME" if is_image else "MODEL_NAME")
    
    # Create the asynchronous OpenAI client
    client = AsyncOpenAI(
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
        response = await client.chat.completions.create(**request_params)
        return response.choices[0].message.content
    except Exception as e:
        raise
    finally:
        await client.close()  # Ensure the client is closed

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()

    # Check if the model is multimodal and adjust the chat history accordingly
    is_multimodal = True

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
                        "url": "https://i.redd.it/duiwqfpzq3he1.png"
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
        response = chat_completion(chat_history, is_image=True)
        print(f"Assistant: {response}")

    except Exception as e:
        print(f"An error occurred: {e}")

