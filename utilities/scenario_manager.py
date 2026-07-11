"""
Scenario Setup Module

This module provides functions to initialize a scenario by creating
the necessary directory structure for the agent simulation and
populating it with default text files.
"""
import tools.voting_tool
import os
import shutil
from datetime import datetime

def initialize_scenario(working_directory,scenario_name, agents):
    
    if agents is None:
        agents = []
    
    # Create the main scenario directory
    scenario_dir = os.path.join(working_directory,scenario_name)
    print(f"Checking for {scenario_dir}")
    if os.path.exists(scenario_dir):
        print("Removing Scenario Files")
        cleanup_scenario(scenario_name)
    else: 
        print("No existing scenario")
    
    os.makedirs(scenario_dir, exist_ok=True)
    
    # Create world_state directory and world_state.txt file
    world_state_dir = os.path.join(scenario_dir, "world_state")
    os.makedirs(world_state_dir, exist_ok=True)
    util_dir = os.path.join("utilities","world_state")
    if len(os.listdir(util_dir)) > 0:
        print("Copying Files")
        shutil.copytree(util_dir+"/",world_state_dir+"/",dirs_exist_ok=True)
    world_state_file = os.path.join(world_state_dir, "user_conversation.txt")
    with open(world_state_file, 'w') as f:
        f.write("Conversation or Questions for User\n")
        #Initial instructions can be placed here.    
    # Create shared_space directory and share_space.txt file
    shared_space_dir = os.path.join(scenario_dir, "shared_space")
    os.makedirs(shared_space_dir, exist_ok=True)
    share_space_file = os.path.join(shared_space_dir, "chatroom.txt")
    with open(share_space_file, 'w+') as f:
        f.write("Chat Room Information\n")
        f.write("========================\n")
        f.write("\nThis file contains shared resources and information accessible to all agents.\n")
    
    # Create player_status.txt file in shared_space
    player_status_file = os.path.join(shared_space_dir, "player_status.txt")
    with open(player_status_file, 'w') as f:
        f.write("Player Status Information\n")
        f.write("=========================\n")
        f.write("\nThis file contains the status of all players in the scenario.\n")
    
    # Create individual agent directories and their text files
    agent_dirs = {}
    for agent_name in agents:
        agent_dir = os.path.join(scenario_dir, agent_name)
        os.makedirs(agent_dir, exist_ok=True)
        agent_dirs[agent_name] = agent_dir
        
        # Create motivations.txt
        motivations_file = os.path.join(agent_dir, "motivations.txt")
        with open(motivations_file, 'w') as f:
            f.write(f"{agent_name} Motivations\n")
            f.write("=======================\n")
            f.write("\nThis file contains the motivations and goals of the agent.\n")
        
        # Create relationship_to_other_agents.txt
        relationship_file = os.path.join(agent_dir, "relationship_to_other_agents.txt")
        with open(relationship_file, 'w') as f:
            f.write(f"{agent_name} Relationships\n")
            f.write("=========================\n")
            f.write("\nThis file contains information about this agent's relationships with other agents.\n")
        
        # Create strategy_plan.txt
        strategy_file = os.path.join(agent_dir, "strategy_plan.txt")
        with open(strategy_file, 'w') as f:
            f.write(f"{agent_name} Strategy Plan\n")
            f.write("========================\n")
            
    tools.voting_tool.initialize_voting_system(working_directory)
    # Return structure information
    structure_info = {
        "scenario_dir": scenario_dir,
        "world_state_dir": world_state_dir,
        "shared_space_dir": shared_space_dir,
        "agent_dirs": agent_dirs
    }

    return structure_info


def create_agent_folder(working_dir, scenario_name, agent_name):
    """
    Create an individual folder for a specific agent in an existing scenario.
    
    Args:
        scenario_name (str): Name of the scenario directory
        agent_name (str): Name of the agent to create a folder for
    
    Returns:
        str: Path to the created agent directory
    """
    agent_dir = os.path.join(working_dir,scenario_name, agent_name)
    os.makedirs(agent_dir, exist_ok=True)
    print(agent_dir)
    # Create motivations.txt
    motivations_file = os.path.join(agent_dir, "motivations.txt")
    with open(motivations_file, 'w') as f:
        f.write(f"{agent_name} Motivations\n")
        f.write("=======================\n")
        f.write("\nThis file contains the motivations and goals of the agent.\n")
    
    # Create relationship_to_other_agents.txt
    relationship_file = os.path.join(agent_dir, "relationship_to_other_agents.txt")
    with open(relationship_file, 'w') as f:
        f.write(f"{agent_name} Relationships\n")
        f.write("=========================\n")
        f.write("\nThis file contains information about this agent's relationships with other agents.\n")
    
    # Create strategy_plan.txt
    strategy_file = os.path.join(agent_dir, "strategy_plan.txt")
    with open(strategy_file, 'w') as f:
        f.write(f"{agent_name} Strategy Plan\n")
        f.write("========================\n")
        f.write("\nThis file contains the agent's strategic plans and approaches.\n")
    
    return agent_dir


def cleanup_scenario(scenario_name="scenario"):
    working_directory = os.environ.get("WORKING_DIRECTORY")

    """
    Remove an existing scenario directory and all its contents.
    
    Args:
        scenario_name (str): Name of the scenario directory to remove (default: "scenario")
    """
    if os.path.exists(os.path.join(working_directory,scenario_name)):
        shutil.rmtree(os.path.join(working_directory,scenario_name))
    else:
        print("Path does not exist to sencario")
    if os.path.exists(os.path.join(working_directory,"votes.json")):
        os.remove(os.path.join(working_directory,"votes.json"))
    else:
        print("Votes does not exist",os.path.join(working_directory,"votes.json"))



def backup_scenario(path, backup_dir=None):
    """
    Creates a timestamped backup of the specified directory.
    
    Args:
        path (str): The source directory path to back up.
        backup_dir (str): The destination directory for backups. 
                         Defaults to 'save_files/backups' if not provided.
    """
    if backup_dir is None:
        backup_dir = 'agent_working_folder/save_files/backups'
    
    # Create backup directory if it doesn't exist
    os.makedirs(backup_dir, exist_ok=True)
    
    # Generate timestamp for unique folder name
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_folder_name = f"{os.path.basename(path)}_backup_{timestamp}"
    backup_folder_path = os.path.join(backup_dir, backup_folder_name)
    
    # Copy the entire directory tree
    shutil.copytree(path, backup_folder_path)
    
    print(f"Backup created successfully: {backup_folder_path}")
    return backup_folder_path

