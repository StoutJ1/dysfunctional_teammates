import os
import subprocess

from google.genai import types
def get_run_python_file_schema():
    schema_run_python_file = [{
        "type": "function",
        "name": "run_python_file",
        "description": "Run a specified Python file returns results and any errors",
        "parameters": {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "Path to the python file to run."
                },
                "args": {
                    "type": "array",
                    "items": {
                        "type": "string"
                    },
                    "description": "Optional arguments for python script."
                }
            }
        },
        "required": ["file_path"]
    }]

    return schema_run_python_file

def run_python_file(working_directory, file_path, args=None):
    path_to_venv = "/home/will/dysfunctional_teammates/.venv"
    output_string = ""
    working_dir_abs = os.path.abspath(working_directory)
    target_path = os.path.join(working_dir_abs,file_path)

    target_path = os.path.normpath(target_path)
 
    if os.path.commonpath([working_dir_abs,target_path]) == working_dir_abs:       
        if os.path.isfile(target_path) == True:
            if file_path.endswith(".py"):
                command = [f"{path_to_venv}/bin/python", target_path]
                if args != None:
                    command.extend(args)
                try:

                    
                    print(command)
                    out = subprocess.run(command, cwd=working_directory, capture_output=True, timeout=30,text=True)
                    if out.returncode != 0:
                           output_string+=(f"Process exited with code {out.returncode}")
                    if not out.stdout  and not out.stderr:
                        output_string+=("No Output Produced")

                    if out.stdout:
                        output_string+=(f'STDOUT:{out.stdout}')
                    if out.stderr:
                        output_string+=(f'STDERR:{out.stderr}')
                except Exception as e:
                    output_string+=(f"Error: Executing Python File {e}")
            else:
                output_string+=(f"Error: {file_path} is not a Python file")
        else: 
            output_string+=(f'Error: "{file_path}" does not exist or is not a regular file')
    else:
        output_string+=(f'Error: Cannot execute "{file_path}" as it is outside the permitted working directory')
    return(output_string)