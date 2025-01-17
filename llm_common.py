from openai import AsyncOpenAI
import os
import json
from typing import Optional, Dict, List, Union

async def chat_completion(
    chat_history: List[Dict[str, str]], 
    api_key: str,
    json_schema: Optional[Dict] = None,
    temperature: float = 0.2
) -> str:
    """
    Unified chat completion function for both local and cloud LLMs using OpenAI-compatible API.
    Supports JSON mode for DeepInfra and guided JSON for vLLM.
    """
    # Determine if we're using local or cloud based on environment
    is_local = os.getenv("USE_LOCAL_LLM", "false").lower() == "true"
    
    # Get complete base URL with path
    base_url = os.getenv("BASE_URL" if is_local else "CLOUD_BASE_URL").rstrip('/')
    
    model = os.getenv("MODEL_PATH" if is_local else "CLOUD_MODEL_NAME")

    # Create AsyncOpenAI client
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

    # Handle JSON schema if provided
    if json_schema is not None:
        if is_local:
            # For local LLM (vLLM), use guided_json to enforce JSON schema
            request_params["extra_body"] = {"guided_json": json_schema}
        else:
            # For cloud LLM (DeepInfra), use JSON mode
            request_params["response_format"] = {"type": "json_object"}
            # Include the schema in the prompt to guide the model
            schema_str = json.dumps(json_schema) if isinstance(json_schema, dict) else json_schema
            request_params["messages"].append({
                "role": "system",
                "content": f"Please provide the output in JSON format that complies with the following schema: {schema_str}"
            })

    try:
        response = await client.chat.completions.create(**request_params)
        return response.choices[0].message.content
    except Exception as e:
        print(f"Full base URL: {base_url}")
        print(f"Request params: {request_params}")
        raise