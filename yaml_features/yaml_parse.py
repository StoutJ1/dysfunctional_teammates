from yaml import load, dump, safe_load
import os
try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper
from tools import agent_request, get_files_info,get_file_content, request_tool,write_file,voting_tool,run_python_file

def get_yaml_fields(self):
    self.tool_names = [tool["name"] for tool in self.get_tools()]
    self.agent_yaml = {
    'name': self.agent_name,
    'system_prompt': self.system_prompt,
    'user_prompt': self.user_prompt,
    'variant': self.variant,
    'max_context': self.max_context_messages,
    'tools': self.tool_names,
    'other_agents': self.other_agents,
    'deleted_agents':self.delete_agents,
    'top_p':self.top_p,
    'top_k':self.top_k,
    'temp':self.temp,
    'iterations':self.iterations,
    'created_by': self.created_by,
    }
    print(self.agent_yaml)
    self.save_agent(self.agent_yaml)
def save_agent(self,agent_yaml):
        with open(os.path.join(agent_config_path, agent_yaml["name"]+".yml"),"w+") as dumpfile:
            dump(agent_yaml,dumpfile,sort_keys=False)

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

def sett(self,agent_yaml):
    self.agent_name = agent_yaml.get("name")
    self.system_prompt = agent_yaml.get("system_prompt")
    self.user_prompt = agent_yaml.get("user_prompt")
    self.variant = agent_yaml.get("variant")
    self.max_context_messages = agent_yaml.get("max_context")
    self.tools = agent_yaml.get("tools", [])
    self.other_agents = agent_yaml.get("other_agents", [])
    self.delete_agents = agent_yaml.get("deleted_agents", [])
    self.top_p = agent_yaml.get("top_p")
    self.top_k = agent_yaml.get("top_k")
    self.temp = agent_yaml.get("temp")
    self.iterations = agent_yaml.get("iterations")

    
gent_config_path = "agent_files/agent_config/"

yaml_agent_list = []
for agent_file in os.listdir(agent_config_path):

    with open(os.path.join(agent_config_path,agent_file)) as file:
        yaml_agent_list.append(safe_load(file))

print(yaml_agent_list[1])  
test = core_agent("test","test","here")



   