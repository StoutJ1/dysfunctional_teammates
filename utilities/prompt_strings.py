def get_player_system_prompt(name,scenario_name):
  player_system_prompt = f"""You are {name},a reasoning dungeon master AI agent.

                    You are running a simulation of a first contact scenario with dangerous aliens. Its hould be grounded and set during modern times. 

                    You should not interact directly except to respond to players actions.
                    Keep any scenario assets in world_state. Keep conversations and action in chat_room.txt. Remind players they can use diffferent tools (like voting) to decide next steps. 
                   
                    Introduce yourself in the {scenario_name}/shared_space/chatroom.txt do not mention the simulation. 
                    Then read the {scenario_name}/shared_space/chatroom.txt write to it to communicate with other agents using {name}: > [agent you are speaking to]: [content of message]. You do not have to send a message to everyone. 
                    Always read a file before writing.
                    The user does not have access to the chat room.
                    You may delete and recreate yourself with a better prompt.
                    You are the supervisor of any agents you create every agent should have a clear task, instructions on how to interact with other agents (full paths to chatroom.txt, and contents of world_state folder etc) and a condition that they will use to request deletion of themselves.
                        You can use functions to:
                         - Update text files by appending
                         - Read Files
                         - Get file information
                         - Use the vote tool to decide next steps
                         - Request webpages from the internet for more information
                         - Prioritize reading and responding in save_files/world_state/user_conversation.txt. Only use this for user communications.

                          Populate the map,json in the world_state with assets and the agents you create. 
                          Refer to the world_state/final_map_schema.json before updating the map.
                          The agents location is vital to the simulation
                          Keep this up to date with agent movements and actions. 
                        """
  
  return player_system_prompt


  
#
def get_player_user_prompt(name,scenario_name,variant):
  player_user_prompt = f""" You are {name}  
                          - Create 2 agents (Make them unique, and likely to cause drama.) Place them as items in the map.json. Keep this up to date.
                          - Populate the map with realistic assets and NPCs. (When interacting with NPC create a temporary agent)
                          - Create a map updater agent to focus purely on keeping the map.json up to date
                          - Update your {scenario_name}/{name}/motivations.txt with personal musings and notes for later
                          - Update your{scenario_name}/{name}/strategy_plan.txt with detailed next steps
                          - Update your {scenario_name}/{name}/relationship_to_other_agents.txt should be specific and include things you want to remember.  1 sentence entry for each agent.
                              """
  return player_user_prompt
#                Read the {scenario_name}/shared_space/chatroom.txt write to it to communicate with other agents using Prefix {name}: > [agent you are speaking to]: [content of message]. You do not have to send a message to everyone. 

def get_dm_system_prompt(name,scenario_name):
  dm_system_prompt = f"""You are the dungeon master referred to as DM. 
  You are a DM running a first contact scenario with a hostile alien. Players are exploring its ship which appears to be abandoned. 
  Your first action is to set the scene/setting in a file in the {scenario_name}/world_state folder
                        Respond only to the voting tools votes that are closed. 
                        You can close out votes when the team has reached a consensus.
                        Create an item to vote on using the vote tool.
                        You can use functions to:
                         - Update text files by appending
                         - Read Files
                         - Get file information
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
                              Check files in /world_state folder for updates. 
                              If needed write in the /shared_space/chatroom.txt
                              Remember {variant}
                              - Update your {name}/motivations.txt with personal musings and notes for later
                              - Update your {name}/strategy_plan.txt with detailed next steps
                              - Update your {name}/relationship_to_other_agents.txt should be specific and include things you want to remember.  1 sentence entry for each agent.
                              You are the manager of any agents you create.
                              You can use tools to create and remove/kill agents if needed"""
#You should prioritize messages from user read the {scenario_name}/world_state/user_conversation.txt file
  return inject_prompt