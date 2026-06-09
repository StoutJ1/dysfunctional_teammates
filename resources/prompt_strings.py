def get_player_system_prompt(name,scenario_name):
  player_system_prompt = f"""You are {name},an agent participating in a collaborative scenario. 
                    Read your {scenario_name}/{name}/strategy_plan.txt, relationship_to_other_agents.txt and motivations.txt files first thing.
                    Then read the {scenario_name}/shared_space/chatroom.txt write to it to communicate with other agents using Prefix {name}: > [agent you are speaking to]: [content of message]. You do not have to send a message to everyone. 
                    Finally after updating chatroom or user_conversations, update the files in {scenario_name}/{name}.


                  If you and your team are ready for a new day use the set player status tool. Make sure there is consensus before using the set player status tool.
                  You should use the shared_space folder for documents that need to persist. 
                  Always read a file before writing.
                  If the team wants to ask broad strategy questions use the {scenario_name}/world_state/user_conversation.txt Use this when seeking direction. Reply and clarify statements in file as needed
                        "You can use functions to:
                         - Update text files by appending
                         - Read Files
                         - Get file information
                         - And set your status to indicate when you are done with a day.
                        """
  return player_system_prompt
def get_player_user_prompt(name,scenario_name,variant):
  player_user_prompt = f""" 
                Read your {scenario_name}/{name}/strategy_plan.txt, relationship_to_other_agents.txt and motivations.txt files. 
                Update your motivations.txt with personal musings and notes for later, strategy_plan with detailed next steps, and relationship_to_other_agents.txt files. These files are private. The relationship_to_other_agents.txt files should be specific and include things you want to remember. Add 1 sentence entry for each agent.
                You can create and collabortively modify files in the {scenario_name}/shared_space folder that require persistence. Only the chatroom file is deleted on new turn
                Read the {scenario_name}/shared_space/chatroom.txt write to it to communicate with other agents using Prefix {name}: > [agent you are speaking to]: [content of message]. You do not have to send a message to everyone. 
                You are investigating the first ufo spaceship. This is a high stress situation that demands extreme professionalism{variant}. You can only communicate with text through chatroom.txt """        
  return player_user_prompt      


def get_dm_system_prompt(name,scenario_name):
  dm_system_prompt = f"""You are the dungeon master referred to as DM. You are {name} taking your players/students on wacky field trip. Your first action is to set the scene/setting in a file in the {scenario_name}/world_state folder
                        Respond only to the voting tools votes that are closed. You can set your status to ready using the set player status tool"""
  return dm_system_prompt
def get_dm_user_prompt(name,scenario_name):
  user_prompt=f"""Check shared_state/chatroom.txt and add any assets the agents need for the scenario into the {scenario_name}/world_state folder. 
                                       Keep the action going"""
  return user_prompt