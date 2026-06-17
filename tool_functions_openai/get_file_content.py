import os
from google.genai import types

MAX_CHARS = 10000
def get_file_content_schema():
    schema_get_file_content = {
            "type":"function",
            "name":"get_file_content",
            "description":"Gets contents of file and returns the last 1000 characters if there are more than 1000 characters",
            "parameters":{
                "type":"object",
                "properties":{
                    "file_path":{
                        "type":"string","description":"Name of file to get contents of relative to working directory (default is the working directory itself.) "
                    },
    
                },
            },
                "required":["file_path"], 
        }
       
    return schema_get_file_content

def get_file_content(working_directory,file_path, forbidden_paths=None):
    """
    Gets contents of file and returns the last 1000 characters if there are more than 1000 characters.
    
    Args:
        file_path: Name of file to get contents of relative to working directory
        forbidden_paths: List of forbidden paths that will be rejected if accessed
    
    Returns:
        String containing file contents or error message
    """
    output_string = ""
    
    # Check if forbidden_paths parameter is provided
    if forbidden_paths is None:
        forbidden_paths = []
    # Check if the requested path is in the forbidden list
    target_path = os.path.normpath(os.path.join(working_directory, file_path))

    for forbidden_path in forbidden_paths:
        # Check for exact match or if file_path starts with forbidden path
        if target_path == forbidden_path or file_path.startswith(forbidden_path):
            output_string += f'Error: Access denied. You are not allowed to access other agents private files"{target_path}"'
            print(f'Error: Access denied. You are not allowed to access other agents private files"{target_path}"')
            return output_string
    
    try:
        

        # Check if the resolved path is within the working directory
        if not target_path.startswith(working_directory):
            output_string += f'Error: Cannot read "{file_path}" as it is outside the permitted working directory'
            print("Outside working directory:",working_directory, "Attempted to access:",target_path)
            return output_string
        
        # Check if file exists and is a regular file
        if os.path.isfile(target_path):
            print(f"File Read is: {file_path}")
            with open(target_path, 'r') as file:
                contents = file.read()
                if len(contents) > MAX_CHARS:
                    contents = contents[-MAX_CHARS:]
                    contents += f'[...File "{file_path}" truncated to last {MAX_CHARS} characters]'
                    output_string += f'{os.path.basename(target_path)} truncated: True'
                    output_string += contents
                else:
                    output_string += contents
        else:
            # Check if it's a directory
            if os.path.isdir(target_path):
                output_string += f'Error: File is a directory: "{file_path}"'
            else:
                output_string += f'Error: File not found or is not a regular file: "{file_path}"'
    except Exception as e:
        output_string += f'Error: Failed to read file "{file_path}": {str(e)}'
        print(f"File Attempted to Read is: {target_path}")

    
    return output_string

