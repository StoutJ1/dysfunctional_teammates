import os
from dotenv import load_dotenv
from google import genai
from google.genai import types
from functions import get_files_info,get_file_content,run_python_file,write_file,set_player_status
from google.genai.types import HttpOptions
import argparse



class simple_agent_object():
    def __init__(self,system_prompt,prompt):
        self. working_directory = "./agent_working_folder"
        self.first_run = True
        self.system_prompt = system_prompt
        self.agent_name = ""
        self.other_agents = []
        self.user_prompt=prompt
        if self.first_run:
            self.first_run =False
            self.messages = [types.Content(role="user",parts=[types.Part(text=self.user_prompt),])]

            
    def send_message(self,client,messages,system_config):
        self.function_results_list = []
        load_dotenv()

        self.output = client.models.generate_content(model=f'models/{os.environ.get("MODEL")}',
                                                contents=messages,
                                                config=system_config)
        if self.output.usage_metadata != None:
            for self.current_candidate in self.output.candidates:
                for part in self.current_candidate.content.parts:
                    if part.text:
                        print(part.text)

            if self.output.function_calls != None:
                #print(output.function_calls)
                for self.call in self.output.function_calls:
                    #print(f"Calling function: {call.name}({call.args})")
                    
                    self.function_call_result = self.call_function(self.call)
                    if self.function_call_result.parts == None:
                        raise "Empty Parts list"
                    if self.function_call_result.parts[0].function_response == None:
                        raise "Empty function response"
                    if self.function_call_result.parts[0].function_response.response == None:
                        raise "Empty function response response"
                    self.function_results_list.append(self.function_call_result.parts[0])
                    
        else:
            print("API Error")
            
        return self.output,self.function_results_list
    def inject_prompt(self,prompt_to_inject):
        self.messages.append(types.Content(role="user",parts=[types.Part(text=prompt_to_inject,)]))



    def call_function(self,function_call,):
        self.function_name = function_call.name or ""
        print(f'Calling function: {function_call.name}')
        self.function_map = {
            "get_file_content":get_file_content.get_file_content,
            "get_files_info": get_files_info.get_files_info,
            "write_file": write_file.write_file,
            "run_python_file": run_python_file.run_python_file,
            # New functions from new_functions directory
            "set_player_status": set_player_status.set_player_status,
            
        }
        if self.function_name not in self.function_map:
            return types.Content(
                role="tool",
                parts=[
                    types.Part.from_function_response(name=self.function_name,response={"error":f"Unknown function: {self.function_name}"})
                ]
            )

        self.args = dict(function_call.args) if function_call.args else {}
        self.args["working_directory"]=  self.working_directory
        if function_call.name =="get_file_content":
            forbidden_paths = []
            for self.other_agent_name in self.other_agents:
                forbidden_paths.append(os.path.join(self.working_directory,self.other_agent_name))
            self.args["forbidden_paths"] = forbidden_paths
        self.function_result=    self.function_map[self.function_name](**self.args)

        return types.Content(
        role="tool",
        parts=[
            types.Part.from_function_response(
                name=self.function_name,
                response={"result": self.function_result},
            )
        ],
    )

    def get_config(self):

        self.available_functions = types.Tool(
        function_declarations=[get_files_info.get_files_info_schema(),
                                get_file_content.get_file_content_schema(),
                                write_file.get_write_file_schema(),
                                run_python_file.get_run_python_file_schema(),
                                # New functions from new_functions directory
                                set_player_status.get_set_player_status_schema(),
                                ],)
        self.thinking_config_val = types.ThinkingConfig(thinking_budget=0)
        self.config = types.GenerateContentConfig(tools=[self.available_functions],
                                                thinking_config=self.thinking_config_val,
                                                system_instruction=self.system_prompt,)   
        return self.config

    def save_to_messages(self,messages,output_from_send_message,function_call_results):
        for current_candidate in output_from_send_message.candidates:
            messages.append(current_candidate.content)
    
        messages.append(types.Content(role="user", parts=function_call_results))
        return messages

    def iterate_steps(self,client,messages):
        self.config = self.get_config()
        self.generate_content_results,self.function_call_results = self.send_message(client,messages,self.config)
        self.messages  = self.save_to_messages(self.messages,self.generate_content_results,self.function_call_results)
        print("-"*50)
        if len(self.function_call_results)== 0:
            print("No more functions to run.")
            # with open("save_history.txt",'w+') as file:
            #     for content in self.messages:
            #         file.write(str(content.parts))
            # print("Wrote History")
            return "Finished"
            
    def iterate(self):
        load_dotenv()
        self.api_key = os.environ.get("GEMINI_API_KEY")
        self.base_url_env = os.environ.get("BASE_URL_ENV")
        self.client = genai.Client(api_key=self.api_key,http_options=HttpOptions(base_url=self.base_url_env))
        
        #print("Model list:",list(client.models.list()))
        
        
        self.iterate_steps(self.client,self.messages,)
