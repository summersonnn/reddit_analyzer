from openai import AsyncOpenAI
import os
import json

async def chat_with_deepinfra(chat_history, api_key, prompts, json_schema=None):
    """
    Starts a chat session with the DeepInfra API.
    If `json_schema` is provided, the response format is set to JSON.
    """
    base_url = os.getenv("CLOUD_BASE_URL")
    model = os.getenv("CLOUD_MODEL_NAME")

    # Create an AsyncOpenAI client with your DeepInfra token and endpoint
    client = AsyncOpenAI(
        api_key=api_key,
        base_url=base_url,
    )

    # Prepare the request parameters
    request_params = {
        "model": model,
        "messages": chat_history,
    }

    # Add response_format only if json_schema is provided
    if json_schema is not None:
        request_params["response_format"] = {"type": "json_object"}
        # Add system message with JSON schema prompt from yaml
        schema_prompt = prompts["json_schema_system_prompt"].format(
            schema=json.dumps(json_schema)
        )
        request_params["messages"].insert(0, {
            "role": "system",
            "content": schema_prompt
        })

    # Make the API call
    response = await client.chat.completions.create(**request_params)
    llm_response = response.choices[0].message.content
    return llm_response