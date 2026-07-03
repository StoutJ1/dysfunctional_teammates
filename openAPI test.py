from openai import OpenAI
from dotenv import load_dotenv
from tool_functions_openai import get_files_info,get_file_content,write_file
import ast
import json
load_dotenv()
import os
base_url = os.environ.get("BASE_URL_ENV")
api_key_openai = os.environ.get("OPENAI_API_KEY")
model = os.environ.get("MODEL")
client = OpenAI(base_url=base_url,api_key=f"{api_key_openai}")
working_directory = os.environ.get("WORKING_DIRECTORY")
input_list = []


def get_tools():

        function_declarations=   [get_file_content.get_file_content_schema(),
                                  get_files_info.get_files_info_schema(),
                                  write_file.get_write_file_schema(),
                                  ]
        return function_declarations


tools = get_tools()
def call_function(item,):
        function_name = item.name or ""
        print(f'Calling function: {item.name}')
        function_map = {
            "get_file_content":get_file_content.get_file_content,
            "get_files_info": get_files_info.get_files_info,
            "write_file":write_file.write_file,
          
        }
        if function_name not in function_map:
            return "Item not found"
        args = json.loads(item.arguments)
        args["working_directory"]=  working_directory
        function_result= function_map[function_name](**args)
        #print("Function result:",function_result)
        
        return function_result    

#print(tools)


context=[{"role":"user",
                   "content":"""You are a helpful AI agent, each step decide if you need to use a tool
                     create a file "hello_world.txt" in "/home/james/ready_for_git/pyagent/agent_working_folder/save_files/ """}]
for turn in range(0,10):
    tool_results = []
    response = client.responses.create(model=model,tools=tools,input=context)

    print(10*"*")
    for item in response.output:
        if item.status == "completed":
             print("Done Exiting")
             exit()
        if item.type=="function_call":
            print(f"Call ID {item.call_id}")
            context.append(item)
            function_result = call_function(item)
            result ={"type":"function_call_output","call_id":item.call_id,"output":function_result}
            context.append(result)
            print(f"Results Call ID {result['call_id']}")

            print(f"Result from tool call: {result}, call id {item.call_id}")
        else:
            print(item.content[0].text)
            context.append(item)
        print("Length of context",len(context))
print(context)
             

        
   
 
   





