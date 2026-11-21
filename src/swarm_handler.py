#TODO variants appear to be changing after the fact.
#TODO forbidden paths now in get file content, technically an agent could overrwrite another agent's files.
import random
from swarm_agent import swarm_agent
import os
from dotenv import load_dotenv
from datetime import datetime
import json
load_dotenv()



agent_config_folder = "shared_space"
iteration_count = 5
turn_count = 3

working_directory = os.environ.get("WORKING_DIRECTORY")
#multitail command for terminal follow along:
#multitail --follow-all -s 2 -du -q 1 "save_files/*/*relation*.txt" "votes.json" "save_files/shared_space/chatroom.txt" -q 1 "save_files/world_state/*.txt"



  
def create_new_agent(system_prompt, user_prompt,agents_name,created_by="User"):
    agents_name = agents_name.strip("/")
    agent = swarm_agent(system_prompt=system_prompt, user_prompt=user_prompt,working_dir=working_directory)
    agent.agent_name = agents_name  
    agent.created_by = created_by
    
    
    return agent



def create_swarm_agents_with_prompts(number_of_agents,swarm_system_prompts,swarm_user_prompts):
    agents = []
    for current_swarm_agent_index in range(number_of_agents):
        name = "Swarm Agent" + str(current_swarm_agent_index)
        user_prompt=swarm_system_prompts[current_swarm_agent_index]
        system_prompt=f"You are {name} {swarm_user_prompts[current_swarm_agent_index]}"
        agent_to_add =create_new_agent(system_prompt=system_prompt,user_prompt=user_prompt,agents_name=name)
        agents.append(agent_to_add)
    return agents



            
def activate_swarm(swarm_system_prompts,swarm_user_prompts):

    load_dotenv()
    swarm_count = len(swarm_system_prompts)
    print(f"Creating Swarm of {swarm_count} Using {swarm_system_prompts}")
    system_prompt_list = swarm_system_prompts
    user_prompt_list = swarm_user_prompts
    print("System Prompts",system_prompt_list)
    swarm_agents = create_swarm_agents_with_prompts(swarm_count,swarm_system_prompts=system_prompt_list,swarm_user_prompts=user_prompt_list)
    current_turn = 0
    
    while current_turn < turn_count: 
        current_turn +=1
    
        for agent in swarm_agents:
            print(f"\n--- Starting Swarm Agent Iteration Loop, Total Swarm-Mini Agents: {len(swarm_agents)} Current Turn {current_turn} out of {turn_count} turns---")

            current_iteraton = 0
            
            while current_iteraton < iteration_count:
                    current_iteraton +=1
                    #TODO Replace with a countdown for the agent.
                    agent.inject_prompt(f"Current loop {current_turn} out of {turn_count} loops.  Turn: {current_iteraton} of {iteration_count} turns per loop" )
                                        
                    status = agent.iterate() 
                    if status:
                        print("Swarm agent ending turn early. ")
                        current_iteraton = iteration_count
                        agent_context_path=os.path.join(working_directory,"shared_space","Swarm_Agents")
                        os.makedirs(agent_context_path,exist_ok=True)
                        with open(os.path.join(agent_context_path,agent.agent_name+".txt"),"w+") as context_file:
                             context_file.writelines(str(agent.context))
    print("Swarm Complete")



