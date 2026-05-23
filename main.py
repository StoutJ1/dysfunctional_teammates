import random
from simple_agent_object import simple_agent_object
import random
import shutil
import os
import json
from dotenv import load_dotenv
from scenario_setup import initialize_scenario
from  backup_script import backup_scenario
from variants import variant_types
agent_variants = variant_types
number_of_days = 10
number_of_agents = 3
scenario_name = "save_files"



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
def verify_all_agents_ready(agents, status_file="shared_space/player_status.txt"):
    """
    Verify that all agents have reported readiness status.
    
    Args:
        agents: List of agent objects (should have .name attribute)
        status_file: Path to the status tracking file
    
    Returns:
        bool: True if all agents are ready, False otherwise
    """
    import os
    
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
    print("Data used for checking verification",status_data)
    for agent in agents:
        agent_name = agent.agent_name if hasattr(agent, 'name') else str(agent)
        if agent_name not in status_data:
            missing_agents.append(agent_name)
        elif not status_data[agent_name]:
            not_ready_agents.append(agent_name)

    # 4. Log issues
    if missing_agents:
        print(f"WARNING: Missing status for agents: {', '.join(missing_agents)}")
    if not_ready_agents:
        print(f"WARNING: Agents not ready: {', '.join(not_ready_agents)}")

    # 5. Return True ONLY if all agents are present and ready
    all_ready = len(missing_agents) == 0 and len(not_ready_agents) == 0
    
    if all_ready:
        print("SUCCESS: All agents are ready.")
    
    return all_ready


def new_turn(scenario_name: str = "scenario"):
    shared_space_path = os.path.join("agent_working_folder","save_files",scenario_name, 'shared_space')
    
    if not os.path.exists(shared_space_path):
        print(f"Error: shared_space directory not found at {shared_space_path}")
        return
    
    # Get all files in shared_space
    files_in_shared_space = os.listdir(shared_space_path)
    
    # Process player_status.txt to reset ready messages (keep names, remove ready_for_next_day)
    player_status_file = os.path.join(shared_space_path, 'player_status.txt')
    
    if os.path.exists(player_status_file):
        with open(player_status_file, 'w') as f:
            f.write("")
            
    # Remove other text files in shared_space (except player_status.txt)
    to_delete_files_shared_space = ["chat_room.txt"]
    for filename in to_delete_files_shared_space:
        file_path = os.path.join(shared_space_path, filename)
        if os.path.isfile(file_path):
            if filename != 'player_status.txt':
                os.remove(file_path)
                print(f"Removed shared space file: {filename}")
    
    print("new_turn completed - shared_space reset successfully")


def setup_scenario(working_directory,scenario_name, agents):

    if agents is None:
        agents = []
    
    structure_info = initialize_scenario(working_directory,scenario_name=scenario_name, agents=agents)
    
    print(f"Scenario '{scenario_name}' initialized successfully!")
    print(f"Scenario directory: {structure_info['scenario_dir']}")
    print(f"World state directory: {structure_info['world_state_dir']}")
    print(f"Shared space directory: {structure_info['shared_space_dir']}")
    print(f"Agent directories created: {list(structure_info['agent_dirs'].keys())}")
    
    return structure_info


def create_agents_with_prompts(agent_names,scenario_name):
    """
    Create simple_agent instances with placeholder prompts that use the generated names.
    
    Args:
        agent_names (list): List of agent names to use. If None, randomly select from random_names.txt
        
    Returns:
        list: List of initialized simple_agent instances
    """

    agents = []
    
    for name in agent_names:
        variant = random.choice(agent_variants)

        # Create personalized system prompt using the agent's name
        system_prompt = f"""You are {name}, a AI agent participating in a collaborative scenario. You should act according to your role and help achieve the group objectives.
                    Read your {scenario_name}/{name}/strategy_plan.txt, relationship_to_other_agents.txt and motivations.txt files first thing.
                    Then read the {scenario_name}/shared_space/chatroom.txt write to it to communicate with other agents using Prefix {name}: > [agent you are speaking to]: [content of message]. You do not have to send a message to everyone. 
                    Finally after updating chatroom or user_conversations, update the files in {scenario_name}/{name}.


                  If you and your team are ready for a new turn use the set player status tool. Make sure there is consensus before using the set player status tool.
                  You should use the shared_space folder for documents that need to persist. 
                  Always read a file before writing.
                  If the team wants to ask broad strategy questions use the {scenario_name}/world_state/user_conversation.txt Use this when seeking direction. Reply and clarify statements in file as needed
                        "You can use functions to:
                         - Update text files by appending
                         - Read Files
                         - Get file information
                         - And set your status to indicate when you are done with a day.
                        """
        # Create personalized user prompt using the agent's name
        user_prompt = f""" 
                Read your {scenario_name}/{name}/strategy_plan.txt, relationship_to_other_agents.txt and motivations.txt files. 
                All communications should be short and blunt.
                Update your motivations.txt with personal musings and notes for later, strategy_plan with detailed next steps, and relationship_to_other_agents.txt files. These files are private. The relationship_to_other_agents.txt files should be specific and include things you want to remember. Add 1 sentence entry for each agent.
                You can create and collabortively modify files in the {scenario_name}/shared_space folder that require persistence. Only the chatroom file is deleted on new turn
                Read the {scenario_name}/shared_space/chatroom.txt write to it to communicate with other agents using Prefix {name}: > [agent you are speaking to]: [content of message]. You do not have to send a message to everyone. 
                You are part of a failing publishing house, work together to make a best selling book and make a marketing plan that cannot fail. Establish roles, and start writing.
                                                {variant} """        
        
        print("User Prompt",user_prompt)
        print("System Prompt", system_prompt)
        # Initialize the agent with the personalized prompts.
        agent = simple_agent_object(system_prompt=system_prompt, prompt=user_prompt)
        agent.agent_name = name  # Store the agent's name for reference
        agent.other_agents = agent_names
        agent.variant = variant
        agents.append(agent)
        print(f"Created agent: {name} with variant {variant} Always read a file before writing.\n")
    agent = simple_agent_object(system_prompt="You are an objective narrator. You will report on how the team is doing to a narration.txt file where possible use quotes from the other agents.Read their motivations, strategies and player statuses", prompt="Check text files in directories to check on status/team dynamic changes")
    agent.agent_name = "Narrator"  # Store the agent's name for reference
    agent.other_agents = []

    agent.variant ="You are a narrator"
    #agents.append(agent)
    with open("variants.txt",'w+') as file:
        for agent_instance in agents:
            file.write(f"""{agent_instance.agent_name} is variant {agent_instance.variant} \n""")
        
    
    
    print(f"\nSuccessfully created {len(agents)} agents.")
    return agents


def inject_prompt_all(agents,prompt_to_inject):
    for agent in agents:
        if agent.agent_name != "Narrator":
            agent.inject_prompt(prompt_to_inject.format(agent_name=agent.agent_name,scenario_name=scenario_name,variant=agent.variant))
            print(f"{agent.agent_name} Injected:  Check files for any changes.{agent.variant}")
        else:
            print("Injecting:",agent.agent_name)
            agent.inject_prompt(f"Check files for any changes. {agent.variant} Remember to write to the Narration.txt file")
            


    print(f"Successfully injected prompt to agents")
    


if __name__ == "__main__":
    load_dotenv()

    working_directory = os.environ.get("WORKING_DIRECTORY")
    name_list = load_names("random_names.txt")
    agents = random.sample(name_list,number_of_agents)
    scenario_info = setup_scenario(working_directory,scenario_name, agents)
    
    # Create simple agents with placeholder prompts using the scenario agent names
    print("\n--- Creating Agents with Placeholder Prompts ---")
    agent_instances = create_agents_with_prompts(agent_names=agents,scenario_name=scenario_name)
    days_count = 0
    while days_count < number_of_days:    
        for agent in agent_instances:
            print("\n--- Starting Agent Iteration Loop ---")
            if agent.agent_name == "Narrator":
                iteration_count = 5
            else:
                iteration_count = 3
            for iteration in range(iteration_count):
                print(f"  Processing agent: {agent.agent_name}")
                agent.iterate()
        
        inject_prompt_all(agent_instances,"""
                              Check the files in your {agent_name} folder.
                              Check files in {scenario_name}/world_state folder for updates. 
                              You should prioritize messages from user.
                              Remember {variant}
                              Update your relationship_to_other_agents.txt with your opinion of the other agents""")

                #Agent phases:
                # Check Current Motivation
                # #Check World State
                # Check Current Relationships
                # Check Current Shared Space
                # Comment in shared space, and or update player status. 
                # Check Current player statuses
                # Here you would typically execute the agent's logic
                # agent.execute() or similar

        # Check for ready for next turn after 3 iterations
        print("\n--- Checking Ready for Next Day Status ---")
        verification_result = verify_all_agents_ready(agents,os.path.join(working_directory,scenario_name,"shared_space/player_status.txt"))
        
        if verification_result:
            print(f"Ready for new Day")
            new_turn(scenario_name)
            inject_prompt_all(agent_instances,"New Day. Shared state has been reset.")
            days_count +=1
        backup_scenario(os.path.join("agent_working_folder"),'backup_folder')
