import os
def get_request_new_agent_schema():
    schema_new_agent_request = {
        "type": "function",
        "name": "request_new_agent",
        "description": """Requests a new agent, name must be unique. Agent will begin actions after the next system update. IMPORTANT: Provide the chatroom path and requirement to interact using read and write.  Every agent  must have the following.
  Must have:
    A condition that they will use to delete themselves
    A path they should save their outputs to.
    They must have instructions on how to interact with other agents (full paths to shared_space/chatroom.txt)
""",
        "parameters": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "Request agent's unique name"
                },
                "system_prompt": {
                    "type": "string",
                    "description": "New agent's system prompt"
                },
                "user_prompt": {
                    "type": "string",
                    "description": "New agent's user prompt"
                },
            
            
            },
                    "required": ["name","system_prompt","user_prompt"]

        },
        "strict":True
    }
    return schema_new_agent_request
#logic for this tool will be primarily in the agent file

def get_remove_agent_request_schema():
    schema_remove_agent_request = {
        "type": "function",
        "name": "request_delete_agent",
        "description": "Requests removal of an agent be terminated at the end of the turn",
        "parameters": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "Agent name to remove."
                },
                
            
            },
                    "required": ["name"]

        },
        "strict":True
    }

    return schema_remove_agent_request
#logic for this tool will be primarily in the agent file
