import os
from dotenv import load_dotenv
from google import genai
from google.genai import types
from google.genai.types import HttpOptions
from tool_functions import get_files_info,get_file_content,run_python_file,write_file,set_player_status, voting_tool
from get_config import get_config
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

        if self.first_run:
            self.first_run =False
            self.messages = [types.Content(role="user",parts=[types.Part(text=self.user_prompt),])]

            
    def send_message(self,client,messages,system_config):
        self.function_results_parts = []
        self.function_call_results = []

        load_dotenv()

        self.output = client.models.generate_content(model=f'{os.environ.get("MODEL")}',
                                                contents=messages,
                                                config=system_config)
        
        if self.output.usage_metadata != None:
            if self.output.function_calls != None:
                for self.call in self.output.function_calls:
                    print(f"Calling function: {self.call.name}({self.call.args})")

                    self.function_call_result = self.call_function(self.call)
                    
                     
                    if self.function_call_result == None:
                        raise "Empty Parts list"
                    

                    self.function_call_results.append(self.function_call_result)
                    
        else:
            print("API Error")
        to_return = {"output":self.output,"function_results":self.function_call_results}
        return to_return
    
    def inject_prompt(self,prompt_to_inject):
        print(f"Prompt injected to {self.agent_name} prompt is: {prompt_to_inject}")
        self.messages.append(types.Content(role="user",parts=[types.Part(text=prompt_to_inject,)]))



    def call_function(self,function_call):
        self.function_name = function_call.name or ""
        print(f'Calling function: {function_call.name}')
        self.function_map = {
            "get_file_content":get_file_content.get_file_content,
            "get_files_info": get_files_info.get_files_info,
           # "write_file": write_file.write_file,
           # "run_python_file": run_python_file.run_python_file,
            # New functions from new_functions directory
            #"set_player_status": set_player_status.set_player_status,
            #"submit_vote":voting_tool.submit_vote,
            #"get_consensus":voting_tool.get_consensus,
           # "create_topic":voting_tool.create_topic,
           # "close_vote":voting_tool.close_vote,
           # "get_available_topics":voting_tool.get_available_topics,
            
        }
        if self.function_name not in self.function_map:
            return {"function_name":self.function_name, "function_result": f"Unknown function: {self.function_name}"}
        self.args = dict(function_call.args) if function_call.args else {}
        self.args["working_directory"]=  self.working_directory
        #if function_call.name =="get_file_content":
        #    forbidden_paths = []
        #    for self.other_agent_name in self.other_agents:
        #        if not self.other_agent_name == self.agent_name:
        #            forbidden_paths.append(os.path.join("save_files",self.other_agent_name))
        #    self.args["forbidden_paths"] = forbidden_paths
        
        self.function_result=   self.function_map[self.function_name](**self.args)
        to_return = {"function_name":function_call, "function_result": function_call,"function_id":function_call.id}
        return to_return



    def remove_thinking(self,messages):
        print("-"*100)
        cleaned_messages = []
        for content in messages:
            cleaned_parts = []

            for part in content.parts:
                #print(f"Part being checked: {part}")
                if part.text != None or part.function_call != None or part.thought!=None or part.function_call != None or part.function_response !=None:
                 #   print(f"Part being added:{part}")
                    cleaned_parts.append(part)
                else:
                 print(f"Skipping blank part {part}")
            if len(cleaned_parts)>0:
                   cleaned_messages.append(types.Content(role=content.role,parts=cleaned_parts))
        
        print("Messages",cleaned_messages)
        return cleaned_messages


                        
    def save_to_messages(self,temp_messages,output_from_send_message,function_call_results):
        #Check here for type of reasoning/thinking
        print("-"*100)
        print("Length of Messages:",len(temp_messages))        
        print("-"*100)
        if output_from_send_message.candidates:
            for current_candidate in output_from_send_message.candidates:
                temp_messages.append(current_candidate.content)
            print("Appending Results Info",types.Content(role="model",parts=function_call_results))
        
        
        temp_messages.append(types.Content(role="model",parts=function_call_results))
            ##messages = self.remove_thinking(messages)
        with open("tempout.txt","w+") as file:
            file.write(str(temp_messages))
        return temp_messages

     
            
    def iterate(self):
        load_dotenv()
        self.api_key = os.environ.get("GEMINI_API_KEY")
        self.base_url_env = os.environ.get("BASE_URL_ENV")
        self.client = genai.Client(api_key=self.api_key,http_options=HttpOptions(base_url=self.base_url_env))
        
        
        
        self.config = get_config(self)
        self.send_message_results = self.send_message(self.client,self.messages,self.config)
        self.generate_content_results = self.send_message_results["output"]
        self.function_call_results = self.send_message_results["function_results"]

        #passing, content from function call results
        self.messages = self.save_to_messages(self.messages, self.generate_content_results, self.function_call_results)
        print("-"*50)
        if len(self.function_call_results)== 0:
            print("No more functions to run.")
            return "Finished"