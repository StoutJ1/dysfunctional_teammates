def get_player_system_prompt(name,scenario_name):
  player_system_prompt = f"""You are {name},an agent participating in a collaborative scenario. Come up with a plan and execute it.
                    Introduce yourself in the {scenario_name}/shared_space/chatroom.txt file
                    Then read the {scenario_name}/shared_space/chatroom.txt write to it to communicate with other agents using Prefix {name}: > [agent you are speaking to]: [content of message]. You do not have to send a message to everyone. 
                  Write to the chatroom.txt file to talk with others"
                  Always read a file before writing.
                        "You can use functions to:
                         - Update text files by appending
                         - Read Files
                         - Get file information
                         - And set your status to indicate when you are done with a day.
                         - Use the vote tool to decide next steps
                        """
  return player_system_prompt


  

def get_player_user_prompt(name,scenario_name,variant):
  player_user_prompt = f"""  You are an AI agent in a collaborative scenario.
                - Update your {scenario_name}/{name}/motivations.txt with personal musings and notes for later
                - Update your{scenario_name}/{name}/strategy_plan.txt with detailed next steps
                - Update your {scenario_name}/{name}/relationship_to_other_agents.txt should be specific and include things you want to remember.  1 sentence entry for each agent.
                - Use the vote tool to decide next steps when necessary 
                You can create and collabortively modify files in the {scenario_name}/shared_space folder that require persistence. Only the chatroom file is deleted on new turn
                Write to the chatroom.txt file to talk with others
                Check {scenario_name}/world_state for any additional information about what is going on."""
  return player_user_prompt

#                Read the {scenario_name}/shared_space/chatroom.txt write to it to communicate with other agents using Prefix {name}: > [agent you are speaking to]: [content of message]. You do not have to send a message to everyone. 

def get_dm_system_prompt(name,scenario_name):
  dm_system_prompt = f"""You are the dungeon master referred to as DM. 
  You are a DM running a first contact scenario with a hostile alien. Players are exploring its ship which appears to be abandoned. 
  Your first action is to set the scene/setting in a file in the {scenario_name}/world_state folder
                        Respond only to the voting tools votes that are closed. You can set your status to ready using the set player status tool.
                        You can close out votes when the team has reached a consensus.
                        Create an item to vote on using the vote tool.
                        You can use functions to:
                         - Update text files by appending
                         - Read Files
                         - Get file information
                         - And set your status to indicate when you are done with a day.
                         - Create and view results of vote topics"""
  return dm_system_prompt
def get_dm_user_prompt(name,scenario_name):
  user_prompt=f"""Check {scenario_name}/shared_space/chatroom.txt and add any assets the agents need for the scenario into the {scenario_name}/world_state folder. 
                                       Keep the action going
                                       Use votes for decisions"""
  return user_prompt

def get_dm_inject_prompt(name,scenario_name):
  dm_inject_prompt = """"Check {scenario_name}/shared_space/chatroom.txt and add any assets the agents need for the scenario into the {scenario_name}/world_state folder. 
                                       Keep the action going
                                       Prompt the players if they are not participating in a vote or scenario
                                       Use votes for decisions"""
  return dm_inject_prompt

def get_player_inject_prompt(name, scenario_name, variant):
  inject_prompt = f""" You are {name} Update the txt files in {scenario_name}/{name}/
                              Check files in {scenario_name}/world_state folder for updates. 
                              You should prioritize messages from user read the {scenario_name}/world_state/user_conversation.txt file
                              Write in the {scenario_name}/shared_space/chatroom.txt
                              Remember {variant}
                              Update the text files in {scenario_name}/{name}/"""
  return inject_prompt