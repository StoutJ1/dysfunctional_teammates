import os

MAX_CHARS = 1000

def get_file_content(file_path, forbidden_paths=None):
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
    for forbidden_path in forbidden_paths:
        # Check for exact match or if file_path starts with forbidden path
        if file_path == forbidden_path or file_path.startswith(forbidden_path):
            output_string += f'Error: Access denied. You are not allowed to access "{file_path}"'
            return output_string
    
    # Normalize the path to prevent path traversal attacks
    try:
        # Get the absolute path of the working directory
        working_dir = os.getcwd()
        
        # Combine working directory with file path and normalize
        target_path = os.path.normpath(os.path.join(working_dir, file_path))
        
        # Check if the resolved path is within the working directory
        if not target_path.startswith(working_dir):
            output_string += f'Error: Cannot read "{file_path}" as it is outside the permitted working directory'
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
    
    return output_string

