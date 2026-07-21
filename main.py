import random
from core_agent import core_agent
from utilities import variants
from utilities import prompt_strings, yaml_parse
import os
from dotenv import load_dotenv
from utilities.scenario_manager import initialize_scenario,backup_scenario,create_agent_folders
from utilities.turn_manager import new_turn
import tkinter as tk

#TODO Use context file for the actual iterate
#TODO Add capability for new and delete agents. 
load_dotenv()
agent_config_folder = "shared_space"
variant_types = variants.variant_types
agent_variants = variant_types
number_of_days = 10
number_of_agents = 1
scenario_name = "save_files"
agent_names=[]
agent_instances=[]
deleted_agents_names = []
agent_config_path  = os.environ.get("AGENT_CONFIG_PATH")
agent_context_path = os.environ.get("AGENT_CONTEXT_PATH")
root =tk.Tk()
#multitail command:
#multitail --follow-all -s 2 -du -q 1 "save_files/*/*relation*.txt" "votes.json" "save_files/shared_space/chatroom.txt" -q 1 "save_files/world_state/*.txt"

#TODO  Add ability to tag messages as transient
# Load random names from file
def load_names(filename):
    names = []
    with open(filename, 'r') as f:
        for line in f:
            name = line.strip()
            if name:
                names.append(name)
    return names

# Function to verify if all player statuses in shared_space have agent_name: ready_for_next_day format
#Add section to skip DM next day/reflect on impact
def verify_all_agents_ready(agents, status_file="shared_space/player_status.txt"):    
    #TODO Clean up this check, its really odd.
    # 1. Check if status file exists
    if not os.path.exists(status_file):
        print(f"ERROR: Status file '{status_file}' not found.")
        return False
    
    # 2. Read and parse status data
    status_data = {}
    try:
        with open(status_file, 'r') as f:
            for line in f:
                if ':' in line:
                    line = line.strip()
                    if line:
                        agent_name, status = line.split(':', 1)
                        print(status.strip().lower())
                        status_data[agent_name.strip()] = (status.strip().lower() == 'ready_for_next_day')
    except Exception as e:
        print(f"ERROR: Failed to read status file: {e}")
        return False

    # 3. Verify ALL agents in the list have reported readiness
    missing_agents = []
    not_ready_agents = []
    #print("Data used for checking verification",status_data)
    for current_instance in agent_instances:
        agent_name = current_instance.agent_name if hasattr(current_instance, 'agent_name') else str(current_instance)
        if agent_name not in status_data:
            missing_agents.append(agent_name)
        elif not status_data[agent_name]:
            not_ready_agents.append(agent_name)

    # 4. Log issues

    if missing_agents:
        print(f"WARNING: Missing status for agents: {', '.join(missing_agents)}")
    if not_ready_agents:
        print(f"WARNING: Agents not ready: {', '.join(not_ready_agents)}")

    all_ready = len(missing_agents) == 0 and len(not_ready_agents) == 0
    print("agents not ready",not_ready_agents)
    
    if all_ready:
        print("All agents are ready.")
    return all_ready

def create_new_agent(system_prompt, user_prompt,agents_name):
    agents_name = agents_name.strip("/")
    agent = core_agent(system_prompt=system_prompt, prompt=user_prompt,working_dir=working_directory)
    agent.agent_name = agents_name  # Stoagent_working_folder/save_files/Zilviare the agent's name for reference
    agent.other_agents = agent_names
    agent.variant= random.choice(variant_types)

    create_agent_folders(working_directory,scenario_name,agent.agent_name,agent_context_path)
    yaml_parse.save_agent(yaml_parse.get_yaml_fields(agent),agent_config_path=agent_config_path)

    #Makes new agent here.
    #TODO Inject new agent names to all yamls.

    return agent

def terminate_agent(target_agent_name):
    print(f"Terminating agent {target_agent_name}")
    for agent in agent_instances:
        if agent.agent_name == target_agent_name:
            agent_instances.remove(agent)
            print("Removed:",target_agent_name)

def create_agents_with_prompts(agent_names,scenario_name):
    agents = []
    print(agent_names)

    #agents.append(create_new_agent(system_prompt=f""+prompt_strings.get_dm_system_prompt(scenario_name=scenario_name,name="Mrs.Frizzle",),user_prompt=prompt_strings.get_dm_user_prompt(name="Mrs.Frizzle",scenario_name=scenario_name),agents_name="DM"))
  
    for name in agent_names:
        agent_variant= random.choice(variant_types)
        # Create personalized system prompt using the agent's name
        system_prompt = prompt_strings.get_player_system_prompt(name=name,scenario_name=scenario_name)
        # Create personalized user prompt using the agent's name
        user_prompt = prompt_strings.get_player_user_prompt(name=name,scenario_name=scenario_name,variant=agent_variant)
     
        agent_to_add =create_new_agent(system_prompt=system_prompt,user_prompt=user_prompt,agents_name=name)
        agent_to_add.variant = agent_variant 
        agents.append(agent_to_add)

        
    return agents


def inject_prompt_all(agents,prompt_to_inject=""):
    for agent in agents:
        agent.inject_prompt(prompt_strings.get_player_inject_prompt(name=agent.agent_name,scenario_name=scenario_name,variant=agent.variant))

            
def get_agent_instances():
    agent_instances_return = []
    agent_yamls = []
    active_agents_filenames = [file_item for file_item in os.listdir(agent_config_path) if "_Deleted" not in file_item]
    for agent_file in active_agents_filenames:
        agent_yamls.append(yaml_parse.get_yaml_file_contents(os.path.join(agent_config_path,agent_file)))

    for yaml_doc in agent_yamls:
        #print("Working on YamlDoc", yaml_doc)
        current_agent = core_agent(yaml_doc["system_prompt"],yaml_doc["user_prompt"],working_directory)

        current_agent = yaml_parse.set_var_from_yaml(current_agent,yaml_doc)
        
        agent_instances_return.append(current_agent)
        
    return agent_instances_return
#print(yaml_agent_list[1])  
#test = core_agent("test","test","here")
                


if __name__ == "__main__":
    load_dotenv()

    working_directory = os.environ.get("WORKING_DIRECTORY")
    name_list = load_names("utilities/random_names.txt")
    agent_names = random.sample(name_list,number_of_agents)
    structure_info = initialize_scenario(working_directory,scenario_name=scenario_name, agents=agent_names,agent_context_path=agent_context_path,agent_config_path=agent_config_path)
    
    #create agents
    print("\n--- Creating Agents---")
    

    create_agents_with_prompts(agent_names=agent_names,scenario_name=scenario_name)
    days_count = 0
    inject_every = 1
    inject_every_count = 1
    print(len(get_agent_instances()))
    while days_count < number_of_days: 
        agent_instances = get_agent_instances() 
        for agent in agent_instances:
            
            print(f"\n--- Starting Agent Iteration Loop, Total Agents: {len(agent_instances)} ---")


                #Not the DM
            if agent.agent_name in deleted_agents_names:
                print("Skipping Agent as they have been deleted.")
                break
            print(agent_names)
            agent.deleted_agents = deleted_agents_names
            agent.other_agents = [file_item[:-5] for file_item in os.listdir(os.environ.get("AGENT_CONFIG_PATH")) if ".yaml" in file_item]

            agent.inject_prompt(agent.get_agent_files_contents(scenario_name))
            agent.inject_prompt("Living Agents:"+str(agent.other_agents))
            print("Living Agents:"+str(agent.other_agents))
            agent.inject_prompt("Deleted Agents"+str(deleted_agents_names))
            iteration_count = agent.iterations
            current_iter = 0

            while current_iter < iteration_count:
                current_iter +=1
                print(f"  Processing agent: {agent.agent_name} Iteration: {current_iter} of {iteration_count}")
                current_agent_yaml = yaml_parse.get_yaml_file_contents(os.path.join(agent_config_path,agent.agent_name+".yaml"))
                agent = yaml_parse.set_var_from_yaml(agent_yaml=current_agent_yaml,self=agent)
                agent.other_agents = [file_item[:-5] for file_item in os.listdir(os.environ.get("AGENT_CONFIG_PATH")) if ".yaml" in file_item]

                iteration_count = agent.iterations
                agent.deleted_agents = deleted_agents_names


                #each iteration it should check its files.
                


                status = agent.iterate() 
                if status:
                    print("Model says ending turn early")
                    yaml_parse.save_agent(yaml_parse.get_yaml_fields(agent),agent_config_path)

                    break
                inject_every_count +=1
            #Checking if a new agent is requested:
                if agent.requested_new_agent:
                    #Call new agent folders
                    for requested_agent in agent.new_agents:
                        create_agent_folders(working_directory,scenario_name,requested_agent["name"],agent_context_path)
                        new_agent = create_new_agent(requested_agent["system_prompt"],requested_agent["user_prompt"],requested_agent["name"])

                        print(f"Created new agent {new_agent.agent_name}, Variant: {new_agent.variant}")

                        agent_instances.append(new_agent)       
                        agent_names.append(new_agent.agent_name)

                        agent.other_agents = agent_names
                        print("Injecting agent names", agent.other_agents)
                        agent.inject_prompt("Living Agents:"+str(agent.other_agents))
                        yaml_parse.save_agent(yaml_parse.get_yaml_fields(agent),agent_config_path)


                    agent.reset_new_agent_request()
                    agent_instances = get_agent_instances() 


                if agent.requested_delete_agent:
                    print("Agent Deletion has been requested. ")
                    print("Deleted agents:",deleted_agents_names)
                    for target_agent in agent.delete_agents:
                        for to_remove in agent_instances:
                            if to_remove.agent_name == target_agent["name"]:
                                agent_instances.remove(to_remove)
                                agent_names.remove(to_remove.agent_name)
                                deleted_agents_names.append(to_remove.agent_name)
                                
                                agent_folder_path = os.path.join(working_directory,scenario_name,to_remove.agent_name)
                                print("Renaming:", agent_folder_path)
                                os.rename(agent_folder_path,agent_folder_path+"_Deleted")
                                print("Renamed:", agent_folder_path)


                                to_rename_config = os.path.join(agent_config_path,to_remove.agent_name)
                                to_rename_context = os.path.join(agent_context_path,to_remove.agent_name)
                                print("Attempting to rename",to_rename_config)
                                if os.path.exists(to_rename_config+".yaml") and os.path.exists(to_rename_context):
                                    os.rename(to_rename_config+".yaml",to_rename_config+"_Deleted.yaml")
                                    os.rename(to_rename_context,to_rename_context+"_Deleted")
                                else:
                                    print("File does not exist")
                                if to_remove.agent_name == agent.agent_name:
                                    print("Currently Iterating agent being deleted.")
                            
                    agent_instances = get_agent_instances() 


            inject_prompt_all(agent_instances)


        
        
        backup_scenario(os.path.join("agent_working_folder"),'backup_folder')
