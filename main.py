import random
from simple_agent_object import simple_agent_object
from resources import variants
from resources import prompt_strings
import random
import shutil
import os
import json
from dotenv import load_dotenv
from scenario_manager import initialize_scenario,backup_scenario
from turn_manager import new_turn
from time import time
variant_types = variants.variant_types
agent_variants = variant_types
number_of_days = 10
number_of_agents = 3
scenario_name = "save_files"
agent_names=[]
agent_instances=[]

#multitail command:
#multitail --follow-all -s 5 -du -q 1 "*/*.txt" "../votes.json"
#multitail --follow-all -s 2 -du -q 1 "*/*relation*.txt" "../votes.json" "shared_space/chatroom.txt" -q 1 "world_state/*.txt"
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
    agent = simple_agent_object(system_prompt=system_prompt, prompt=user_prompt,working_dir=working_directory)
    agent.scenario = scenario_name
    agent.agent_name = agents_name  # Store the agent's name for reference
    agent.other_agents = agent_names
    return agent

def terminate_agent(agent_name):
    print(f"Terminating agent {agent_name}")
    for agent in agent_instances:
        if agent.name == agent_name:
            agent_instances.remove(agent)
            print("Removed")

def create_agents_with_prompts(agent_names,scenario_name):
    agents = []
    print(agent_names)

    agents.append(create_new_agent(system_prompt=f""+prompt_strings.get_dm_system_prompt(scenario_name=scenario_name,name="Mrs.Frizzle",),user_prompt=prompt_strings.get_dm_user_prompt(name="Mrs.Frizzle",scenario_name=scenario_name),agents_name="DM"))
  
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
        if prompt_to_inject == "":
            prompt_to_inject=prompt_strings.get_player_inject_prompt(name=agent.agent_name,scenario_name=scenario_name,variant=agent.variant)

        if agent.agent_name == "DM":
            agent.inject_prompt(prompt_strings.get_dm_inject_prompt(name=agent.agent_name,scenario_name=scenario_name))
        else: 
            agent.inject_prompt(prompt_strings.get_player_inject_prompt(name=agent.agent_name,scenario_name=scenario_name,variant=agent.variant))

            

                


if __name__ == "__main__":
    load_dotenv()

    working_directory = os.environ.get("WORKING_DIRECTORY")
    name_list = load_names("random_names.txt")
    agent_names = random.sample(name_list,number_of_agents)
    structure_info = initialize_scenario(working_directory,scenario_name=scenario_name, agents=agent_names)
    
    # Create simple agents with placeholder prompts using the scenario agent names
    print("\n--- Creating Agents with Placeholder Prompts ---")
    

    agent_instances = create_agents_with_prompts(agent_names=agent_names,scenario_name=scenario_name)
    days_count = 0
    inject_every = 1
    inject_every_count = 1
    while days_count < number_of_days:    
        for agent in agent_instances:
            timerstart = time()
            print("\n--- Starting Agent Iteration Loop ---")
            if agent.agent_name == "DM":
                iteration_count = 6
            else:
                #Not the DM
                agent.inject_prompt(agent.get_agent_files_contents())
                iteration_count = 5
            print("Adding Agent Files Contents")

            for iteration in range(iteration_count):
                print(f"  Processing agent: {agent.agent_name} Iteration: {iteration} of {iteration_count}")
                status = agent.iterate() 

                if status:
                    print("Model says ending turn early")
                
                    break     
            print("*"*10,f"Completed Agent: {time()-timerstart:.2f} secs","*"*10)
            inject_prompt_all(agent_instances)


        # Check for ready for next turn after 3 iterations
        print("\n--- Checking Ready for Next Day Status ---")
        verification_result = verify_all_agents_ready(agent_instances,os.path.join(working_directory,scenario_name,"shared_space/player_status.txt"))
        
        if verification_result:
            print(f"Starting new Day")
            new_turn(scenario_name)
            inject_prompt_all(agent_instances,"New Day. Shared state has been reset.")
            days_count +=1
        backup_scenario(os.path.join("agent_working_folder"),'backup_folder')
