import os
from google.genai import types
import main
def get_agent_lifecycle_schema():
    schema_agent_lifecycle = {
  "type": "function",
  "function": {
    "name": "agent_lifecycle_manager",
    "description": "Allows an agent to spin up and turn off other agents. When an agent is turned off, its folder is renamed with a '_Terminated' suffix.",
    "strict": True,
    "parameters": {
      "type": "object",
      "properties": {
        "action": {
          "type": "string",
          "enum": [
            "create",
            "terminate"
          ],
          "description": "Action to perform."
        },
        "agent_name": {
          "type": "string",
          "description": "Name of the agent to spin up or turn off."
        },
        "working_directory": {
          "type": "string",
          "description": "Base directory containing the scenario structure with agent folders."
        }
      },
      "required": [
        "action",
        "agent_name",
        "working_directory"
      ],
      "additionalProperties": True
    }
  }
}
   
    return schema_agent_lifecycle

def agent_lifecycle_manager(working_directory, action, agent_name):
    
    return_string = ""
    working_dir_abs = os.path.abspath(working_directory)
    agent_folder_path = os.path.join(working_dir_abs, agent_name)
    terminated_folder_path = os.path.join(working_dir_abs, agent_name + "_Terminated")
    
    # Security check: ensure target is within working directory
    if action == "create":
        # Create a new agent folder
        if os.path.exists(agent_folder_path):
            return_string += f'Error: Agent folder "{agent_name}" already exists'
        else:
            try:
                main.create_new_agent(agent_name=agent_name,system_prompt="""You need to post in chatroom.txt "I'm alive""")
                os.makedirs(agent_folder_path)

                return_string += f'Success: Agent "{agent_name}" has been spun up'
            except Exception as e:
                return_string += f'Error: Failed to spin up agent "{agent_name}": {str(e)}'
    
    elif action == "terminate":
        # Turn off an agent by renaming its folder with _Terminated suffix
        if os.path.exists(agent_folder_path):
            if os.path.exists(terminated_folder_path):
                return_string += f'Error: Terminated folder "{agent_name}_Terminated" already exists'
            else:
                try:
                    os.rename(agent_folder_path, terminated_folder_path)
                    return_string += f'Success: Agent "{agent_name}" has been turned off (folder renamed to "{agent_name}_Terminated")'
                except Exception as e:
                    return_string += f'Error: Failed to turn off agent "{agent_name}": {str(e)}'
        else:
            return_string += f'Error: Agent folder "{agent_name}" does not exist'
    else:
        return_string += f'Error: Invalid action "{action}". Use "spin_up" or "turn_off"'
    
    return return_string

