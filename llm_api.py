from openai import OpenAI
import os

SYSTEM_PROMPT = """Analyze the entire thread, including the title, original post, comments, and subcomments. Prioritize information from posts with the highest scores, as they indicate strong user agreement. Identify contradictions, biases, and emerging trends within the discussion. Summarize the key points and conclusions based on the most reliable information."""

def chat_with_deepinfra(api_key, chat_history, stream=False, prompt_user=True):
    """
    Starts a chat session with the DeepInfra API.
    """
    # Create an OpenAI client with your DeepInfra token and endpoint
    client = OpenAI(
        api_key=api_key,
        base_url="https://api.deepinfra.com/v1/openai",
    )

    while True:
        if prompt_user:
            user_input = input("You: ")
            chat_history.append({"role": "user", "content": user_input})
        
        if stream:
            print("LLM: ", end="", flush=True)
            response_text = ""
            response = client.chat.completions.create(
                model="meta-llama/Llama-3.3-70B-Instruct-Turbo",
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
                model="meta-llama/Llama-3.3-70B-Instruct-Turbo",
                messages=chat_history,
            )
            llm_response = response.choices[0].message.content
            print(f"LLM: {llm_response}")  
            chat_history.append({"role": "assistant", "content": llm_response})
            return llm_response


if __name__ == "__main__":
    chat_history = []
    api_key = os.getenv("DEEPINFRA_API_KEY")

    # Add system prompt
    system_message = {
        "role": "system", 
        "content": SYSTEM_PROMPT
    }

    chat_history.append(system_message)
    chat_with_deepinfra(api_key, chat_history, stream=True)  # Set stream=True to enable streaming
