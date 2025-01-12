import aiohttp
import asyncio
import json
import os

async def send_vllm_request(chat_history, api_key, json_schema, temperature=0.2):
    """
    Sends a request to the vLLM server with the given context and returns the response.
    """
    base_url = os.getenv("BASE_URL")
    model = os.getenv("MODEL_PATH")
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Accept": "application/json"
    }
    
    data = {
        "model": model,
        "messages": chat_history,
        "temperature": temperature,
        "stop_token_ids": [128001, 128009]
    }

    if json_schema is not None:
        # Convert to string if it's a dict
        if isinstance(json_schema, dict):
            data["guided_json"] = json.dumps(json_schema)
        # Use as is if it's already a string
        elif isinstance(json_schema, str):
            data["guided_json"] = json_schema
        else:
            raise TypeError(f"Unsupported json_schema type: {type(json_schema)}")

    async with aiohttp.ClientSession() as session:
        async with session.post(base_url, headers=headers, json=data) as response:
            if response.status == 200:
                response_json = await response.json()
                return response_json["choices"][0]["message"]["content"]
            else:
                print(f"Request failed with status code: {response.status}")
                return None