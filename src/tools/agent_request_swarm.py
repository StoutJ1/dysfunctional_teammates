import os
def get_agent_request_swarm():
    agent_request_swarm_schema = {
        "type": "function",
        "name": "request_agent_swarm",
        "description": """Requests MULTIPLE simple worker LLM models that will run immediately They are not considered agents.  
        The length of the arrays must match. The prompts need VERY SPECIFIC AND Detailed instructions. 
        They do not have unique names.
        Remind the agents the tools they can use: 1. Read, 2. Write, 3.Get directory info 4.Run Python.""",
        "parameters": {
            "type": "object",
            "properties": {
               
                "system_prompts": {
                    "type": "array",
                    "description": """An array of ordered system_prompts."""
                },
                "user_prompts": {
                    "type": "array",
                    "description": """An array of ordered user_prompts."""
                },
            
            
            },
                    "required": ["system_prompts","user_prompts"]

        },
        "strict":True
    }
    return  agent_request_swarm_schema
