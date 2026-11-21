import os
from dotenv import load_dotenv
from openai import OpenAI,types
import json
import pickle
import pexpect
import time
from tools import  get_files_info,get_file_content,write_file,run_python_file,chatroom_managent


class swarm_agent():
    def __init__(self,system_prompt,user_prompt,working_dir):
        #different for qwen Qwen: user, only 1 system, Gemma supports multiple system messages.
        self.role_for_system = "user"
        self.agent_param={"working_directory":"","agent_name":"","deleted_agents":[],"system_prompt":""}
        self. working_directory = working_dir
        self.system_prompt = system_prompt
        self.agent_name = ""
        self.user_prompt=user_prompt
        self.function_calls=[]
        self.api_key_openai = os.environ.get("OPENAI_API_KEY")
        self.model = os.environ.get("SWARM_MODEL")
        self.base_url = os.environ.get("BASE_URL_ENV")
        self.working_directory = os.environ.get("WORKING_DIRECTORY")
        self.client = OpenAI(base_url=self.base_url,api_key=f"{self.api_key_openai}")
        self.max_context_messages = 50
        self.deleted_agents = []
        self.context =[]
        self.context.append({"role":"system","content":self.system_prompt})
        self.context.append({"role":"user","content":self.user_prompt})
        self.top_p = 0
        self.top_k = 0
        self.temp = 0
        self.iterations = 7
        
        self.created_by = "User"

        self.requested_new_agent = False
        self.new_agents = []

        self.requested_delete_agent = False
        self.delete_agents = []

        self.max_tokens = 5000
        self.pexpect_child = []
    def inject_prompt(self,prompt_to_inject):
        try:
            self.context.append({"role":self.role_for_system,"content":prompt_to_inject})
        except AttributeError:
            print("Attribute Error")

            

    def call_function(self,item,):
            function_name = item.name or ""
            #print(f'Calling function: {item.name}')
            function_map = {
                "get_file_content":get_file_content.get_file_content,
                "get_files_info": get_files_info.get_files_info,
                "write_file":write_file.write_file,
          #      "run_python_file":run_python_file.run_python_file,
          #      "get_chatroom_content_tool":chatroom_managent.get_chatroom_content_tool,
                #"send_command_to_text_adventure":"",


            }
            if function_name not in function_map:
                return "Tool not found"
            
            args = json.loads(item.arguments)
            
            args["working_directory"]=  self.working_directory
            #The rest are handled here
            function_result= function_map[function_name](**args)
            return function_result    
                       
                
    

    def get_text_from_context(self, context_to_string):
        text_out = []
        for item in context_to_string:
            if hasattr(item,'type'):
                #print("Type is:",item.type)
                if item.type == 'reasoning':
                #print("Reasoning",item.content[0].text)
                    text_out.append(str(item.content[0].text))
                if item.type == "function_call":
                #print("Name:",item.name,"Arguments:",item.arguments)
                    text_out.append(str("Tool Used:"+item.name+" Arguments:"+item.arguments))

                #print("Type:",item.type)
                if item.type == "function_call_output":
                #print(item)
                    text_out.append(str(item.output))
                else:
                    if 'role' in item:
                        #print(item['content'])
                        text_out.append(item['content'])
                if 'type' in item:
                    #print("item",item['output'])
                    text_out.append(item['output'])
        return text_out
    
    def prune_context(self):
        """
        Prunes the context to ensure it does not exceed max_context_messages,
        while always preserving the system prompt (the first element).
        """
        to_summarize = []
    
        if self.max_context_messages is None:
            return
        
            #Keep system prompt
        system_prompt = self.context[0]
            # Remaining messages allowed after the system prompt
        allowed_additional_messages = self.max_context_messages - 1
        
        if allowed_additional_messages <= 0:
            # If max_context_messages is 1, we only keep the system prompt.
            self.context = [system_prompt]
        #This must be smaller than max context length.
        number_to_summarize = 40

        prefix = self.context[1:number_to_summarize]
        raw_text_prefix = "/n".join(self.get_text_from_context(prefix))
        text_summarized = self.summarize_text(raw_text_prefix,number_of_sentences=5)
                        

        print("-"*100)
        self.pruned_context = []
        #Keeping system prompt
        self.pruned_context.append(system_prompt)
        #Appending summarized
        self.pruned_context.append({"role":"user","content":text_summarized})
        
        #Getting just the remaining context text
        print("Pruned context is:",self.pruned_context,"value is:",self.prune_context)
        #This slice should pull starting from the number to summarize so summarizing six will slice [6:] until the end. (This shoudl be extend?)
        self.pruned_context.extend(self.context[number_to_summarize:])
        print("-"*100)
        print("Summarized:",text_summarized)        
        print("Pruned Current Length is:",len(self.pruned_context),"Max Allowed Addtional",allowed_additional_messages)
        print("-"*100)
        
        return self.pruned_context
    def summarize_text(self,to_summarize,number_of_sentences):
            self.summarize_context=[]
            self.summarize_context.append({"role":"system","content":prompt_strings.get_summarize_prompt(number_of_sentences)})
            self.summarize_context.append({"role":"user","content":"Summarize the following:"+to_summarize})
            #Using independant response so I don't have to limit by the max messages etc.
            self.response = self.client.responses.create(model=self.model,input=self.summarize_context)
            print(self.response)
            print("*"*100)
            print(self.response.output_text)
            print("*"*100)

            print("Done Summarizing")
            return self.response.output_text

            
    def send_message(self, client, context):
        self.function_results_parts = []
        self.function_call_results = []

        load_dotenv()
        response = client.responses.create(model=self.model,tools=self.tools,input=context,max_output_tokens=int(self.max_tokens),reasoning={"effort":"low"})
        try: 
            for item in response.output:
                if item.type=="function_call":

                    function_result = self.call_function(item)
                    result ={"type":"function_call_output","call_id":item.call_id,"output":function_result}
                    #Append both the function call, and its result.
    
                    context.append(item)
                    context.append(result)
                else:
                    #If its not a tool call its a reasoning item
                    #print(" ".join([content_from_item.text for content_from_item in item.content]))
                    
                    self.context.append(item)
            if len(self.context) > self.max_context_messages:
                self.context = self.prune_context()
                print("Pruned Messages")

            if response.output_text:
                print("Status is Completed")
                return self.context,True
            else:
                return self.context,False
        except AttributeError:
            print("Failed to add items to context")
        


    def get_tools(self):
        function_declarations=   [get_file_content.get_file_content_schema(),
                                  get_files_info.get_files_info_schema(),
                                  write_file.get_write_file_schema(),
                                  run_python_file.get_run_python_file_schema(),
                                  chatroom_managent.get_chatroom_content_schema(),
                                  ]
        return function_declarations
    

            
    
    def iterate(self):
        try:
            load_dotenv()
            self.tools=self.get_tools()
            self.context,self.completed = self.send_message(self.client,self.context,)
            if self.completed == True:
                return self.completed
        except Exception as e:
            print("-- Exception while iterating swarm agent --", e)
            with open("Debug.txt",'w+') as debug:
                debug.write(str(self.context))
    