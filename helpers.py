
import jsonschema
from jsonschema import ValidationError
from typing import List, Dict, Any

def json_schema_to_label_sets(schema):
    """
    Converts a JSON Schema to a dictionary of label sets for zero-shot classification.
    Handles boolean properties (without enums) to create the label set ["True", "False", "None"].

    Args:
        schema (dict): The JSON Schema.

    Returns:
        dict: A dictionary where keys are property names (categories) and
              values are lists of labels for that category.
    """
    label_sets = {}

    if not isinstance(schema, dict) or schema.get("type") != "object" or "properties" not in schema:
        return label_sets

    for property_name, property_details in schema["properties"].items():
        if property_details.get("type") == "boolean":
            # Special handling for booleans (no enums)
            label_sets[property_name] = ["True", "False", "None"]
        elif "enum" in property_details:
            # Other types with enums
            label_sets[property_name] = property_details["enum"]
        else:
            print(f"Warning: Property '{property_name}' has no 'type' or 'enum'. Using ['None'] as label.")
            label_sets[property_name] = ["None"]

    return label_sets

# This is just for testing purposes. To make sure every dict in the list have same keys. If not, spot the faulty dict.
def print_dict_keys_as_lists(list_of_dicts):
    # Create a list of lists containing the keys of each dictionary
    list_of_keys = [list(dictionary.keys()) for dictionary in list_of_dicts]
    
    # Print each inner list on a separate line
    for keys in list_of_keys:
        print(keys)

# Function to validate JSON schema after step 1
def validate_json_schema(json_schema):
    try:
        # Validate the schema itself
        jsonschema.Draft7Validator.check_schema(json_schema)
        print("JSON schema is valid.")
        return True
    except ValidationError as e:
        print(f"JSON schema is invalid: {e}")
        return False

# just for functionality testing (used inside deep_analysis_of_thread)
def print_dict_value_counts(analysis_results: List[Dict[str, Any]], stage: str = "Before Standardization"):
    """
    Prints the number of values in each dictionary of a list and a descriptive message.

    Args:
        analysis_results: A list of dictionaries.
        stage: A string describing the stage (e.g., "Before Standardization", "After Standardization").
    """
    if not analysis_results:
        print(f"{stage}: The analysis_results list is empty.")
        return

    value_counts = [len(d.values()) for d in analysis_results]
    print(f"{stage}: Number of values in each dictionary: {value_counts}")

def add_none_to_enum(json_data):
    """
    Adds "None" to the enum property of keys in a JSON object if it's not already present.
    Correctly handles nested "properties" objects.

    Args:
        json_data: A dictionary representing the JSON data.

    Returns:
        A new dictionary with "None" added to the enum lists where appropriate.
    """

    if not isinstance(json_data, dict):
        return json_data

    new_json_data = json_data.copy()

    for key, value in new_json_data.items():
        if isinstance(value, dict):
            if "enum" in value:
                if "None" not in value["enum"]:
                    value["enum"].append("None")
            elif "properties" in value:  # Handle nested properties
                new_json_data[key]["properties"] = add_none_to_enum(value["properties"])
            else:
                new_json_data[key] = add_none_to_enum(value)  # Recurse for other nested dicts

    return new_json_data

# Just for now. We will allow arrays in the json in the future.
def remove_array_type_elements(json_data):
    """
    Removes elements with a type of "array" from a JSON schema.

    Args:
        json_data: The JSON schema as a dictionary.

    Returns:
        A new dictionary with array-type elements removed.
    """

    if not isinstance(json_data, dict):
        return json_data

    new_json_data = {}
    for key, value in json_data.items():
        if isinstance(value, dict):
            if "type" in value and value["type"] == "array":
                continue  # Skip elements with type "array"
            else:
                new_json_data[key] = remove_array_type_elements(value)
        elif isinstance(value, list):
             new_json_data[key] = [remove_array_type_elements(item) for item in value]
        else:
            new_json_data[key] = value

    return new_json_data
