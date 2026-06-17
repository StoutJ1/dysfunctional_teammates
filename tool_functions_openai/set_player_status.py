import os
from google.genai import types


def get_set_player_status_schema():
    schema_set_player_status = [{
        "type": "function",
        "name": "set_player_status",
        "description": "Sets the player state of the agent to ready_for_next_day or more_actions_pending. Writes to the scenario/shared_space/player_status.txt file in the scenario directory.",
        "parameters": {
            "type": "object",
            "properties": {
                "working_directory": {
                    "type": "string",
                    "description": "Base directory containing the scenario structure with shared_space folder"
                },
                "agent_name": {
                    "type": "string",
                    "description": "Name of agent ready for next turn"
                },
                "status": {
                    "type": "boolean",
                    "description": "True for ready for next turn, false for need more time"
                }
            }
        },
        "required": ["working_directory", "agent_name", "status"]
    }]

    return schema_set_player_status


def set_player_status(working_directory, agent_name,status):
    """
    Sets the player state of the agent to ready_for_next_day or more_actions_pending.
    
    Writes to the shared_space/player_status.txt file in the scenario directory.
    
    Args:
        working_directory: The base directory containing the scenario structure
        status: true for ready for next turn false, for more time.
    
    Returns:
        dict: Success message or error message
    """
    working_dir_abs = os.path.abspath(working_directory)
    
    # Check path is within working directory
    target_path = os.path.join(working_dir_abs,"save_files", "shared_space", "player_status.txt")
    target_path = os.path.normpath(target_path)
    
    if os.path.commonpath([working_dir_abs, target_path]) != working_dir_abs:
        return {
            "error": f"Cannot write player_status.txt as it is outside the permitted working directory"
        }
    
    # Validate status
    valid_statuses = ['ready_for_next_day', 'more_actions_pending']

    # Write the status to player_status.txt
    try:
        with open(target_path, 'a+') as file:
            if status:
                file.write(f"{agent_name}: ready_for_next_day\n")
            else:
                file.write(f"{agent_name}: more_actions_pending\n")

        return f"Updated {agent_name} status!"
    except Exception as e:
        return {
            "error": f"Error writing player_status.txt: {str(e)}"
        }
