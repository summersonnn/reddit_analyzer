import requests
import json
import os

def send_vllm_request(chat_history, api_key, json_schema, temperature=0.2, stream=False):
    """
    Sends a request to the vLLM server with the given context and returns the response.
    """
    base_url = os.getenv("BASE_URL")
    model = os.getenv("MODEL_PATH")
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Accept": "text/event-stream" if stream else "application/json"
    }

    data = {
        "model": model,
        "messages": chat_history,
        "temperature": temperature,
        "stream": stream,
        "stop_token_ids": [128001, 128009]
    }

    if json_schema is not None:
        data["guided_json"] = json.dumps(json_schema)

    response = requests.post(base_url, headers=headers, json=data, stream=stream)
    if response.status_code == 200:
        return response.json()["choices"][0]["message"]["content"] 
    else:
        print(f"Request failed with status code: {response.status_code}")
        return None
