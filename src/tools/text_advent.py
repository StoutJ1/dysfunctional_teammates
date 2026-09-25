import os
import subprocess
import pexpect
def get_text_advent_type_schema():
    schema_run_python_file = {
        "type": "function",
        "name": "send_command_to_text_adventure",
        "description": "Run a command in a text adventure and return any results, this is a shared instance between agents",
        "parameters": {
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "description": "Command to run"
                },
                
            }
        },
        "required": ["command"]
    }

    return schema_run_python_file

def text_advent_type(working_directory, text_to_send,pexpect_child):
    path_to_venv =os.environ.get("VENV_PATH")

    output_string = ""
    print("Sending", text_to_send)
    #pexpect_child.sendline(text_to_send)
    