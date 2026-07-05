import os
from dotenv import load_dotenv
from openai import OpenAI
import json

from tool_functions_openai import get_files_info,get_file_content,write_file,voting_tool,set_player_status
import argparse



class simple_agent_object():
    def __init__(self,system_prompt,prompt,working_dir):
        self. working_directory = working_dir
        self.first_run = True
        self.system_prompt = system_prompt
        self.agent_name = ""
        self.other_agents = []
        self.variant =""
        self.user_prompt=prompt
        self.function_calls=[]
        self.api_key_openai = os.environ.get("OPENAI_API_KEY")
        self.model = os.environ.get("MODEL")
        self.base_url = os.environ.get("BASE_URL_ENV")
        self.working_directory = os.environ.get("WORKING_DIRECTORY")
        self.client = OpenAI(base_url=self.base_url,api_key=f"{self.api_key_openai}")
        


        if self.first_run:
            self.first_run =False
            self.context = [{"role":"system","content":self.system_prompt},{"role":"user",
                   "content":self.user_prompt}]
    def call_function(self,item,):
            function_name = item.name or ""
            print(f'Calling function: {item.name}')
            function_map = {
                "get_file_content":get_file_content.get_file_content,
                "get_files_info": get_files_info.get_files_info,
                "write_file":write_file.write_file,
                "set_player_status":set_player_status.set_player_status,
                "create_topic":voting_tool.create_topic,
                "submit_vote":voting_tool.submit_vote,
                "get_consensus":voting_tool.get_consensus,
                "get_available_topics":voting_tool.get_available_topics,
                "close_vote":voting_tool.close_vote,


            }
            if function_name not in function_map:
                return "Item not found"
            args = json.loads(item.arguments)
            args["working_directory"]=  self.working_directory
            function_result= function_map[function_name](**args)
            #print("Function result:",function_result)

            return function_result    
    
            
    def send_message(self, client, context):
        self.function_results_parts = []
        self.function_call_results = []

        load_dotenv()
        
        client = OpenAI(base_url=self.base_url,api_key=f"{self.api_key_openai}")
        response = client.responses.create(model=self.model,tools=self.tools,input=context,reasoning={"effort":"low"})
        for item in response.output:
            if response.output_text:
                print("Status is Completed")
                return True
            if item.type=="function_call":
                context.append(item)
                function_result = self.call_function(item)
                result ={"type":"function_call_output","call_id":item.call_id,"output":function_result}
                context.append(result)
                #print(f"Results Call ID {result['call_id']}")
                #print(f"Result from tool call: {result}, call id {item.call_id}")
                print(item.arguments)
            else:
                print(item.content[0].text)
                context.append(item)
        return context
    def inject_prompt(self,prompt_to_inject):
        #print(f"Prompt injected to {self.agent_name} prompt is: {prompt_to_inject}")
        self.context.append({"role":"system","content":prompt_to_inject})


    def get_tools(self):
        function_declarations=   [get_file_content.get_file_content_schema(),
                                  get_files_info.get_files_info_schema(),
                                  write_file.get_write_file_schema(),
                                  voting_tool.get_available_topics_schema(),
                                  voting_tool.get_consensus_schema(),
                                  voting_tool.get_create_topic_schema(),
                                  voting_tool.get_submit_vote_schema(),
                                  voting_tool.get_close_vote_schema(),
                                  set_player_status.get_set_player_status_schema(),
                                  ]
        return function_declarations
    

    



    
            
    def iterate(self):
        load_dotenv()
        self.tools=self.get_tools()

        self.completed = self.send_message(self.client,self.context,)
        if self.completed == True:
            return self.completed
        print("-"*50)
    