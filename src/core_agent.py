import os
from dotenv import load_dotenv
from openai import OpenAI,types
import json
import pickle
import pexpect
import time
from tools import agent_request, get_files_info,get_file_content, request_tool,write_file,voting_tool,run_python_file, text_advent
from utilities_resources import prompt_strings


class core_agent():
    def __init__(self,system_prompt,user_prompt,working_dir):
        self.verbose = False
        #different for qwen Qwen: user, only 1 system, Gemma supports multiple system messages.
        self.role_for_system = "user"
        self.agent_param={"working_directory":"","agent_name":"","deleted_agents":[],"system_prompt":""}
        self. working_directory = working_dir
        self.pending_inject_prompt = ""
        self.system_prompt = system_prompt
        self.agent_name = ""
        self.all_agents = []
        self.variant =""
        self.user_prompt=user_prompt
        self.function_calls=[]
        self.api_key_openai = os.environ.get("OPENAI_API_KEY")
        self.model = os.environ.get("MODEL")
        self.base_url = os.environ.get("BASE_URL_ENV")
        self.working_directory = os.environ.get("WORKING_DIRECTORY")
        self.config_path = os.environ.get("AGENT_CONFIG_PATH")
        self.context_path = os.environ.get("AGENT_CONTEXT_PATH")
        self.client = OpenAI(base_url=self.base_url,api_key=f"{self.api_key_openai}")
        self.max_context_messages = 100
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
       
            

    def call_function(self,item,):
            function_name = item.name or ""
            #print(f'Calling function: {item.name}')
            function_map = {
                "get_file_content":get_file_content.get_file_content,
                "get_files_info": get_files_info.get_files_info,
                "write_file":write_file.write_file,
                "create_topic":voting_tool.create_topic,
                "submit_vote":voting_tool.submit_vote,
                "get_consensus":voting_tool.get_consensus,
                "get_available_topics":voting_tool.get_available_topics,
                "close_vote":voting_tool.close_vote,
                "request_new_agent":"",
                "request_delete_agent":"",
                "request_page":request_tool.request_page,
                "run_python_file":run_python_file.run_python_file,
                "send_command_to_text_adventure":"",


            }
            if function_name not in function_map:
                return "Tool not found"
            
            
            args = json.loads(item.arguments)
            
            if function_name == "request_new_agent":
                #print("---Other Agents:",self.other_agents, "Deleted Agents", self.deleted_agents)
                if (args["name"] not in self.other_agents) and (args["name"] not in self.deleted_agents):
                    self.requested_new_agent = True
                    self.new_agents.append({"system_prompt": args["system_prompt"],"user_prompt":args["user_prompt"],"name":args["name"]})
                    #print("New Agent Requested", args["name"])
                    return "Agent Requested, they will be started next turn"
                else:
                    return "Agent name already in use"
            if function_name == "send_command_to_text_adventure":
                print(10*"-")
                print("Text Adventure:",args["command"])
                self.pexpect_child.sendline(args["command"])
                time.sleep(0.1)
                self.pexpect_child.expect("(>)|(\*\*MORE\*\*)")
                output_string = self.pexpect_child.before
                
                print(output_string)
                return output_string


            
            if function_name =="request_delete_agent":
                self.requested_delete_agent = True
                print("Name For Deletion",args["name"])
                self.delete_agents.append({"name":args["name"]})
                return "Delete Requested"

            if function_name == "get_file_content":

                args['forbidden_paths'] = self.other_agents
                args['current_agent'] = self.agent_name

            args["working_directory"]=  self.working_directory
            #The rest are handled here
            function_result= function_map[function_name](**args)
            return function_result    
                       
                
    
    def reset_new_agent_request(self):
        self.requested_new_agent = False 
        self.new_agents = []
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
        
        #print(">"*100,"Raw text of prefix",raw_text_prefix)
                

        #print(self.context[:])
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
        response = client.responses.create(model=self.model,tools=self.tools,input=context,max_output_tokens=int(self.max_tokens))
        #response = client.responses.create(model=self.model,tools=self.tools,input=context)
        #print(response)
        #response = client.responses.create(model=self.model,tools=self.tools,input=context)
        try: 
            for item in response.output:
                if item.type=="function_call":

                    function_result = self.call_function(item)
                    result ={"type":"function_call_output","call_id":item.call_id,"output":function_result}
                    #Append both the function call, and its result.

                    context.append(item)
                    context.append(result)
                    if self.verbose:
                        print(f"Result from tool call: {result}")
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
        
        
    def inject_prompt(self,prompt_to_inject):
        try:
            #print(f"""Prompt injected to {self.agent_name} prompt is:{prompt_to_inject}""")
            self.context.append({"role":self.role_for_system,"content":prompt_to_inject})
            self.write_context(self.context)
        except AttributeError:
            print("Attribute Error")


    def get_tools(self):
        function_declarations=   [get_file_content.get_file_content_schema(),
                                  get_files_info.get_files_info_schema(),
                                  write_file.get_write_file_schema(),
                                  voting_tool.get_available_topics_schema(),
                                  voting_tool.get_consensus_schema(),
                                  voting_tool.get_create_topic_schema(),
                                  voting_tool.get_submit_vote_schema(),
                                  voting_tool.get_close_vote_schema(),
                                  agent_request.get_request_new_agent_schema(),
                                  agent_request.get_remove_agent_request_schema(),
                                  request_tool.get_request_page_tool_schema(),
                                  run_python_file.get_run_python_file_schema(),
                                  text_advent.get_text_advent_type_schema(),
                                  ]
        return function_declarations
    

    def get_agent_files_contents(self):
        to_return = ""
        #print("Scenario file",self.scenario)
        agent_file_path = os.path.join(self.working_directory,self.agent_name)
        files_in_agent_folder = os.listdir(os.path.join(self.working_directory,self.agent_name))
        to_return = ""
        try:
            for file in files_in_agent_folder:
                with open(os.path.join(agent_file_path,file)) as current:
                    to_return += (f" Contents of {file}: {current.readlines()} ")
        except UnicodeDecodeError:
            print("Unable to read files for:", self.agent_name)
        return to_return

    def load_context(self):
        to_return = ""
        #print(os.path.join(self.context_path,self.agent_name,"context"))
        try:
            with open(os.path.join(self.context_path,self.agent_name,"context"),"rb") as load_file:
                to_return =  pickle.load(load_file)
        except FileNotFoundError: 
            print("Failed to find file")
        return to_return
    def write_context(self,to_write):
        try:
            with open(os.path.join(self.context_path,self.agent_name,"context"),"wb") as write_file:
                pickle.dump(to_write,write_file)
        except FileNotFoundError:
            print("Unable to dump pickle, file not found",self.agent_name) 
            
    
    def iterate(self):
        try:
            load_dotenv()
            self.tools=self.get_tools()
            
            self.write_context(self.context)
            self.context = self.load_context()
            #print("Sending:",self.context)
            self.context,self.completed = self.send_message(self.client,self.context,)
            self.write_context(self.context)
            
        

            if self.completed == True:
                return self.completed
        except Exception as e:
            print("-- Exception while iterating --", e)
    