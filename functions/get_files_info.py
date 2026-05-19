import os
from google.genai import types
def get_files_info_schema():
    schema_get_files_info = types.FunctionDeclaration(
    name="get_files_info",
    description="Lists files in directory relative to the working directory, providing file size and directory status",
    parameters=types.Schema(
        type=types.Type.OBJECT,
        properties={
            "directory": types.Schema(
                type=types.Type.STRING,
                description="Path to list files from, relative to the working directory (default is the working directory itself)",
            ),
            
        },
        required=["directory"],
    ),
)   
    return schema_get_files_info
def get_files_info(working_directory, directory="."):
    
    return_string = ""
    working_dir_abs = os.path.abspath(working_directory)
    target_path = os.path.join(working_dir_abs,directory)
    target_path = os.path.normpath(target_path)
    if os.path.exists(target_path):
        if os.path.commonpath([working_dir_abs,target_path]) == working_dir_abs:
            if os.path.isfile(directory) == False:
                return_string += (f'Success: "{directory}" is within the working directory')
                results = ""
                return_string +=(f'Results for"{directory}"directory')
                
                for file in os.listdir(target_path):
                        current_file = os.path.join(target_path,file)
                        results += f' - {file}: file_size={str(os.lstat(current_file).st_size)} bytes, is_dir={str(os.path.isdir(current_file))}\n'
                return_string +=(results)
            else: 
                return_string +=(f'Error: "{directory}" is not a directory')
        else:
         return_string +=(f'Error: Cannot list "{directory}" as it is outside the permitted working directory')
    else:
        return_string +=(f'Error: "{directory}" is not a directory')
    return return_string

