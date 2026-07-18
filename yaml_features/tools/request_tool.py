import os
import subprocess
import requests
def get_request_page_tool_schema():
    schema_curl_tool = {        "type": "function",
        "name": "request_page",
        "description": "Download page to shared_space/pages folder",
        "parameters": {
            "type": "object",
            "properties": {
                "url_path": {
                    "type": "string",
                    "description": "Url to download"
                },
                "file_name": {
                    "type": "string",
                    "description":"file_name"
                    },
                    
            }
        },
        "required": ["url_path","file_name"],
    "strict": True}

    return schema_curl_tool

def request_page(working_directory,url_path, file_name):
    print("Running Request Page Tool, working dir", working_directory)
    output_string = ""
    working_dir_abs = os.path.abspath(working_directory)

    target_path = os.path.join(working_dir_abs,"save_files","shared_space/pages")

    target_path = os.path.normpath(target_path)
    #return(f"Checking if {working_dir_abs} exists",os.path.commonpath([working_dir_abs,target_path]))
    print(target_path)
    if os.path.commonpath([working_dir_abs,target_path]) == working_dir_abs:
        if not os.path.exists(target_path):
            os.makedirs(target_path)
            print("Created Folder",target_path) 
        if os.path.exists(target_path) == True:   
            r = requests.get(url_path)
            output_string = "Complete"
            print("Saving to",os.path.join(target_path,file_name))
            with open(os.path.join(target_path,file_name),'w+') as file:
                file.write(r.text)
    return(output_string)