import os
from dotenv import load_dotenv
from openai import OpenAI
import json
import pickle
from tools import agent_request, get_files_info,get_file_content, request_tool,write_file,voting_tool,run_python_file



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
        self.max_context_messages = 10
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


            }
            if function_name not in function_map:
                return "Tool not found"
            print(item)
            
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
            if function_name =="request_delete_agent":
                self.requested_delete_agent = True
                print("Name For Deletion",args["name"])
                self.delete_agents.append({"name":args["name"]})
                return "Delete Requested"
            else:
                args["working_directory"]=  self.working_directory
                function_result= function_map[function_name](**args)
                return function_result    
    
    def reset_new_agent_request(self):
        self.requested_new_agent = False 
        self.new_agents = []
        
    def prune_context(self):
        """
        Prunes the context to ensure it does not exceed max_context_messages,
        while always preserving the system prompt (the first element).
        """
        if self.max_context_messages is None:
            return

        if len(self.context) <= self.max_context_messages:
            return
        #Keep system prompt
        system_prompt = self.context[0]
        # Remaining messages allowed after the system prompt
        allowed_additional_messages = self.max_context_messages - 1
        
        if allowed_additional_messages <= 0:
            # If max_context_messages is 1, we only keep the system prompt.
            self.context = [system_prompt]
        else:
            # Keep the system prompt and the last 'allowed_additional_messages' from the rest of the context.
            self.context = [system_prompt] + self.context[-(allowed_additional_messages):]
                
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
                    
                    context.append(item)
            self.prune_context()
            if response.output_text:
                print("Status is Completed")
                return context,True
            else:
                return context,False
        except AttributeError:
            print("Failed to add items to context")
        
        
    def inject_prompt(self,prompt_to_inject):
        try:
            print(f"""Prompt injected to {self.agent_name} prompt is:{prompt_to_inject}""")
            print(f"Current context: {self.context}")
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
                                  
                                  ]
        return function_declarations
    

    def get_agent_files_contents(self,scenario):
        self.scenario = scenario
        to_return = ""
        #print("Scenario file",self.scenario)
        agent_file_path = os.path.join(self.working_directory,self.scenario,self.agent_name)
        files_in_agent_folder = os.listdir(os.path.join(self.working_directory,self.scenario,self.agent_name))
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
            