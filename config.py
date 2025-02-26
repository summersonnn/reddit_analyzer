import yaml

prompt_file_path = "prompts.yaml"

try:
    # Try to load from the current directory
    with open("prompts.yaml", "r", encoding="utf-8") as file:
        prompts = yaml.safe_load(file)
except FileNotFoundError:
    try:
        # If the first attempt fails, try to load from the parent directory
        prompt_file_path = "../" + prompt_file_path
        with open(prompt_file_path, 'r', encoding="utf-8") as file:
            prompts = yaml.safe_load(file)
    except FileNotFoundError:
        # If both attempts fail, raise a custom error or handle it as needed
        raise FileNotFoundError("The prompts.yaml file was not found in the current directory or the parent directory.")