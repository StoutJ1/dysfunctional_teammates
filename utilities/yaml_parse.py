from ruamel.yaml import YAML 
import os

from tools import agent_request, get_files_info,get_file_content, request_tool,write_file,voting_tool,run_python_file

def str_representer(dumper, data):
#Pulled from here https://gist.github.com/alertedsnake/c521bc485b3805aa3839aef29e39f376
    if len(data.splitlines()) > 1:  # check for multiline string
        return dumper.represent_scalar('tag:yaml.org,2002:str', data, style='|')
    return dumper.represent_scalar('tag:yaml.org,2002:str', data)
def get_yaml_fields(self):
    self.tool_names = [tool["name"] for tool in self.get_tools()]
    self.agent_yaml = {
    'name': self.agent_name,
       'iterations':self.iterations,
    'created_by': self.created_by,
    'system_prompt': self.system_prompt,
    'user_prompt': self.user_prompt,
    'variant': self.variant,
    'max_context': self.max_context_messages,
    'tools': self.tool_names,
    'other_agents': self.other_agents,
    'top_p':self.top_p,
    'top_k':self.top_k,
    'temp':self.temp,
    'max_tokens':self.max_tokens,

    'deleted_agents':self.deleted_agents,

    'requested_new_agent':self.requested_new_agent,
    'new_agents':self.new_agents,

    'requested_delete_agent':self.requested_delete_agent,
    'delete_agents':self.delete_agents,
    
   

    }
    print(self.agent_yaml)
    return (self.agent_yaml)
def save_agent(agent_yaml,agent_config_path):
        yaml = YAML()
        yaml.default_flow_style = False
        yaml.indent(sequence=4, offset=2)
        yaml.representer.add_representer(str, str_representer)
        with open(os.path.join(agent_config_path, agent_yaml["name"]+".yaml"),"w+") as dumpfile:
            yaml.dump(agent_yaml,dumpfile)


def set_var_from_yaml(self,agent_yaml):
    self.agent_name = agent_yaml.get("name")
    self.system_prompt = agent_yaml.get("system_prompt")
    self.user_prompt = agent_yaml.get("user_prompt")
    self.variant = agent_yaml.get("variant")
    self.max_context_messages = agent_yaml.get("max_context")
    self.max_tokens = agent_yaml.get("max_tokens")
    self.tools = agent_yaml.get("tools", [])
    self.other_agents = agent_yaml.get("other_agents", [])

    self.deleted_agents = agent_yaml.get("deleted_agents", [])

    self.top_p = agent_yaml.get("top_p")
    self.top_k = agent_yaml.get("top_k")
    self.temp = agent_yaml.get("temp")

    self.requested_new_agent = agent_yaml.get("requested_new_agent")
    self.new_agents = agent_yaml.get("new_agents")

    self.requested_delete_agent = agent_yaml.get("requested_delete_agent")
    self.delete_agents = agent_yaml.get("delete_agents")
    
    self.iterations = agent_yaml.get("iterations")
    self.new_agents = agent_yaml.get("new_agents")

    return self
    
#yaml_agent_list = []
#for agent_file in os.listdir(agent_config_path):

#    with open(os.path.join(agent_config_path,agent_file)) as file:
#        yaml_agent_list.append(safe_load(file))

#print(yaml_agent_list[1])  
#test = core_agent("test","test","here")



def get_yaml_file_contents(yaml_file_path):
    print("Getting Yaml:", yaml_file_path)
    with open(os.path.join(yaml_file_path)) as file:
        to_return = YAML().load(file)
        return to_return



   