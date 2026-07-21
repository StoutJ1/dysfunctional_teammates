import os
from dotenv import load_dotenv
from openai import OpenAI
import json
import pickle
from tools import agent_request, get_files_info,get_file_content, request_tool,write_file,voting_tool,run_python_file
import argparse



class core_agent():
    def __init__(self,system_prompt,prompt,working_dir):
        self.agent_param={"working_directory":"","agent_name":"","other_agents":[],"deleted_agents":[],"system_prompt":"","user_prompt":""}
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
        self.config_path = os.environ.get("AGENT_CONFIG_PATH")
        self.context_path = os.environ.get("AGENT_CONTEXT_PATH")
        self.client = OpenAI(base_url=self.base_url,api_key=f"{self.api_key_openai}")
        self.max_context_messages = 50
        self.deleted_agents = []
        
        self.top_p = 0
        self.top_k = 0
        self.temp = 0
        self.iterations = 10
        self.created_by = "test"

        self.requested_new_agent = False
        self.new_agents = []

        self.requested_delete_agent = False
        self.delete_agents = []

        self.context = []
        self.max_tokens = 5000

       
            

    def call_function(self,item,):
            function_name = item.name or ""
            print(f'Calling function: {item.name}')
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
            #    "request_page":request_tool.request_page,
                "run_python_file":run_python_file.run_python_file,


            }
            if function_name not in function_map:
                return "Tool not found"
            args = json.loads(item.arguments)
            if function_name == "request_new_agent":
                print("---Other Agents:",self.other_agents, "Deleted Agents", self.deleted_agents)
                if (args["name"] not in self.other_agents) and (args["name"] not in self.deleted_agents):
                    self.requested_new_agent = True
                    self.new_agents.append({"system_prompt": args["system_prompt"],"user_prompt":args["user_prompt"],"name":args["name"]})
                    print("New Agent Requested", args["name"])
                    return "Requested"
                else:
                    return "Agent name already in use"
            if function_name =="request_delete_agent":
                self.requested_delete_agent = True
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

        # The first message is the system prompt. 
        # We want to keep the system prompt and the most recent N-1 messages.
        # However, the total count should be at most max_context_messages.
        
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
        response = client.responses.create(model=self.model,tools=self.tools,input=context,reasoning={"effort":"low"},max_output_tokens=int(self.max_tokens))
  
        #response = client.responses.create(model=self.model,tools=self.tools,input=context)
        
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
                print(f"Result from tool call: {result}")
                print(item.arguments)
            else:
                print(item.content[0].text)
                context.append(item)
        self.prune_context()

        return context
    def inject_prompt(self,prompt_to_inject):
        #print(f"""Prompt injected to {self.agent_name} prompt is: "role":"system","content":{prompt_to_inject}""")
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
                                  agent_request.get_request_new_agent_schema(),
                                  agent_request.get_remove_agent_request_schema(),
        #                          request_tool.get_request_page_tool_schema(),
                                  run_python_file.get_run_python_file_schema(),
                                  
                                  ]
        return function_declarations
    

    def get_agent_files_contents(self,scenario):
        self.scenario = scenario
        print("Scenario file",self.scenario)
        agent_file_path = os.path.join(self.working_directory,self.scenario,self.agent_name)
        files_in_agent_folder = os.listdir(os.path.join(self.working_directory,self.scenario,self.agent_name))
        to_return = ""
        for file in files_in_agent_folder:
            with open(os.path.join(agent_file_path,file)) as current:
                to_return += (f" Contents of {file}: {current.readlines()} ")
        return to_return


    def write_context(self, convo_history):
        with open(os.path.join(self.context_path,self.agent_name,"context.txt"),"wb+") as dump_file:
            pickle.dump(convo_history,dump_file)
            #file.write(bytes(context))

    def load_context(self):
        print(os.path.join(self.context_path,self.agent_name,"context.txt"))
        with open(os.path.join(self.context_path,self.agent_name,"context.txt"),"rb") as file:
            to_return =  pickle.load(file)
        return to_return
    

    def iterate(self):
        load_dotenv()

        self.tools=self.get_tools()
        if self.first_run:
           self.first_run =False
           self.context = [{"role":"system","content":self.system_prompt},{"role":"user",
                "content":self.user_prompt}]
           self.write_context(self.context)
        else:
            self.context = self.load_context()
        self.completed = self.send_message(self.client,self.context,)
        print(self.write_context(self.context))
        if self.completed == True:
            return self.completed
        print("-"*50)
    