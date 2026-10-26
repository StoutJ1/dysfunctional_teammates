import os
def get_chatroom_content_schema():
    schema_chatroom_content = {
        "type": "function",
               "name": "get_chatroom_content_tool",
               "description": "Requests a new agent, name must be unique. Agent will begin actions after the next system update. IMPORTANT: To prevent duplicate agents, verify the agent is not already requested.",
          "parameters": {
            "type": "object",
            "properties": {
                "line_count": {
                    "type": "string",
                    "description": "Number of lines to read"
                    },
                },
                                   "required": ["line_count"]
               
                       },
                       "strict":True
        }
    

    return schema_chatroom_content
def get_chatroom_content_tool(working_directory, line_count=5):
    
    return_string = ""
    working_dir_abs = os.path.abspath(working_directory)
    target_path = os.path.join(working_dir_abs,"shared_space/chatroom.txt")
    print("Chatroom target path",target_path)
    if os.path.exists(target_path):
       with open(target_path) as chat_file:
           lines = chat_file.readlines()
           if int(line_count) > len(lines):
               line_count = len(lines)
           #Return only the last x lines
           return_string = " ".join(lines[-int(line_count):])
           print("Reading chat",return_string, "Lines read:",line_count)

           #  
    else:
        return_string +=(f'Error: "Cannot find chatroom.txt" is not a valid file')
    return return_string

