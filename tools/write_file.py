import os
from google.genai import types

def get_write_file_schema():
    schema_write_file = {
        "type": "function",
        "name": "write_file",
        "description": "Writes content to specificed filename relative to the working directory",
        "parameters": {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "Path to the file to write, relative to working directory"
                },
                "content": {
                    "type": "string",
                    "description": "Content to write to file"
                },
                "append": {
                    "type": "boolean",
                    "description": "Use True to append to file, False to overrwrite. ALWAYS USE APPEND IN chatroom.txt"
                },

            },
            "required": ["file_path", "content","append"]

        },
        "strict":True
    }

    return schema_write_file


def write_file(working_directory, file_path, content,append):
    working_dir_abs = os.path.abspath(working_directory)
    target_path = os.path.join(working_dir_abs,file_path)

    target_path = os.path.normpath(target_path)
 
    if os.path.commonpath([working_dir_abs,target_path]) == working_dir_abs:
        print("valid Path",target_path)
        if os.path.exists(target_path) == False:
           os.makedirs(os.path.dirname(target_path),exist_ok=True)
        if append:
            mode = "a+"
        else:
            mode = "w+"
        with  open(target_path,mode) as file:
            if mode == "a+":
                contents = file.write(content+"\n")
            
            if mode == "w+":
                contents = file.write(content+"\n")
            
            print("Writing")
            return (f'Successfully wrote to "{file_path}" ({len(content)} characters written)')
                

           # print(f'Error: Cannot write to "{file_path}" as it is a directory')
    else:
        return (f'Error: Cannot write to "{file_path}" as it is outside the permitted working directory')