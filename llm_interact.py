import os
from typing import List, Dict
from openai import OpenAI
from openai import AsyncOpenAI
import json
import asyncio
import time

def chat_completion(
    chat_history: List[Dict[str, str]],
    temperature: float = 0.2,
    is_image=False
) -> str:
    """
    Unified chat completion function for both local and cloud LLMs using OpenAI-compatible API.
    """
    # Determine if we're using local or cloud based on environment
    is_local = os.getenv("USE_LOCAL_LLM", "false").lower() == "true"
    base_url = os.getenv("BASE_URL" if is_local else "CLOUD_BASE_URL").rstrip('/')
    api_key = os.getenv("VLLM_API_KEY" if is_local else "CLOUD_LLM_API_KEY").rstrip('/')
    
    if not is_image:
        model = os.getenv("MODEL_PATH" if is_local else "CLOUD_MODEL_NAME")
    else: # image
        model = os.getenv("MODEL_PATH" if is_local else "CLOUD_VMODEL_NAME")


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

# Async version of chat completion 
async def async_chat_completion(
    chat_history: List[Dict[str, str]],
    temperature: float = 0.2,
    is_image: bool = False
) -> str:
    """
    Asynchronous chat completion function for both local and cloud LLMs using an OpenAI-compatible API.
    """
    # Determine if we're using local or cloud based on environment variables
    is_local = os.getenv("USE_LOCAL_LLM", "false").lower() == "true"
    base_url = os.getenv("BASE_URL" if is_local else "CLOUD_BASE_URL").rstrip('/')
    api_key = os.getenv("VLLM_API_KEY" if is_local else "CLOUD_LLM_API_KEY").rstrip('/')
    
    # Choose the appropriate model based on whether it's an image request or not
    if not is_image:
        model = os.getenv("MODEL_PATH" if is_local else "CLOUD_MODEL_NAME")
    else:
        model = os.getenv("MODEL_PATH" if is_local else "CLOUD_VMODEL_NAME")
    
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

    start_time = time.time()
    print("Start time of the async_chat_completion function: ", start_time)
    
    try:
        response = await client.chat.completions.create(**request_params)
        print("Finish time of the async_chat_completion function: ", time.time())
        return response.choices[0].message.content
    except Exception as e:
        raise

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

