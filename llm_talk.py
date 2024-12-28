import requests
import json
import os

SYSTEM_PROMPT = """Analyze the entire thread, including the title, original post, comments, and subcomments. Prioritize information from posts with the highest scores, as they indicate strong user agreement. Identify contradictions, biases, and emerging trends within the discussion. Summarize the key points and conclusions based on the most reliable information."""

def send_vllm_request(chat_history, api_key, temperature=0.3, stream=False):
    """
    Sends a request to the vLLM server with the given context and returns the response.
    """
    host_ip = os.environ.get("HOST_IP")
    url = f"http://{host_ip}:8000/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Accept": "text/event-stream" if stream else "application/json"
    }
    data = {
        "model": "/home/kubilay/Projects/llm/models/Meta-Llama-3.1-8B-Instruct-Q5_K_M.gguf",
        "messages": chat_history,
        "temperature": temperature,
        "stream": stream,
        "stop_token_ids": [128001, 128009]
    }

    response = requests.post(url, headers=headers, json=data, stream=stream)
    if response.status_code == 200:
        return response
    else:
        print(f"Request failed with status code: {response.status_code}")
        return None

def chat_with_vllm(api_key, chat_history, stream=False, prompt_user=True):
    """
    Starts a chat session with the vLLM server.
    """
    while True:
        if prompt_user:
            user_input = input("You: ")
            chat_history.append({"role": "user", "content": user_input})
        
        if stream:
            print("LLM: ", end="", flush=True)
            response_text = ""
            response = send_vllm_request(chat_history, api_key, stream=True)
            
            if response:
                for line in response.iter_lines():
                    if line:
                        line = line.decode('utf-8')
                        if line.startswith('data: '):
                            data = line[6:]  # Remove 'data: ' prefix
                            if data == '[DONE]':
                                break
                            try:
                                chunk = json.loads(data)
                                content = chunk["choices"][0]["delta"].get("content", "")
                                if content:
                                    print(content, end="", flush=True)
                                    response_text += content
                            except json.JSONDecodeError:
                                continue
            print()  # New line after streaming completes
            chat_history.append({"role": "assistant", "content": response_text})
            return response_text
        else:
            response = send_vllm_request(chat_history, api_key)
            if response:
                response_json = response.json()
                llm_response = response_json.get('choices', [{}])[0].get('message', {}).get('content', '')
                print(f"LLM: {llm_response}")  
                chat_history.append({"role": "assistant", "content": llm_response})
                return llm_response

        if not prompt_user:
            break

if __name__ == "__main__":
    chat_history = []
    api_key = os.getenv("VLLM_API_KEY")

    # Add system prompt
    system_message = {
        "role": "system", 
        "content": SYSTEM_PROMPT
    }

    chat_history.append(system_message)
    chat_with_vllm(api_key, chat_history, stream=True)  # Set stream=True to enable streaming