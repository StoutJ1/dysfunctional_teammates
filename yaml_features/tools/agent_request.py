import os
def get_request_new_agent_schema():
    schema_new_agent_request = {
        "type": "function",
        "name": "request_new_agent",
        "description": "Requests a new agent, name must be unique",
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
