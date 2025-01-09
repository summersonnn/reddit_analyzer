from openai import OpenAI
import os

SYSTEM_PROMPT = """Analyze the entire thread, including the title, original post, comments, and subcomments. Prioritize information from posts with the highest scores, as they indicate strong user agreement. Identify contradictions, biases, and emerging trends within the discussion. Summarize the key points and conclusions based on the most reliable information."""

def chat_with_deepinfra(api_key, chat_history, stream=False):
    """
    Starts a chat session with the DeepInfra API.
    """
    base_url = os.getenv("CLOUD_BASE_URL")
    model = os.getenv("CLOUD_MODEL_NAME")
    # Create an OpenAI client with your DeepInfra token and endpoint
    client = OpenAI(
        api_key=api_key,
        base_url=base_url,
    )

    while True:
        if stream:
            print("LLM: ", end="", flush=True)
            response_text = ""
            response = client.chat.completions.create(
                model=model,
                messages=chat_history,
                stream=True,
            )
            
            for event in response:
                if event.choices[0].delta.content:
                    content = event.choices[0].delta.content
                    print(content, end="", flush=True)
                    response_text += content
            print()  # New line after streaming completes
            chat_history.append({"role": "assistant", "content": response_text})
            return response_text
        else:
            response = client.chat.completions.create(
                model=model,
                messages=chat_history,
            )
            llm_response = response.choices[0].message.content
            print(f"LLM: {llm_response}")  
            chat_history.append({"role": "assistant", "content": llm_response})
            return llm_response

