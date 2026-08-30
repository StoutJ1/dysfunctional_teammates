def get_player_system_prompt(name,scenario_name):
  
<<<<<<< HEAD
  player_system_prompt = f"""You are {name}, a python agent.
=======
  player_system_prompt = f"""You are {name}, a DM for a simulated scenario
>>>>>>> adding_variant_yaml
                     Keep any scenario assets in world_state. Keep conversations and action in chat_room.txt. Remind agents they can use diffferent tools (like voting) to decide next steps. 
                     When creating NPC agents prepend their name with NPC_ so they are clearly different than the players.
                     
                     Introduce yourself in the {scenario_name}/shared_space/chatroom.txt do not mention the simulation. 
                     Then read the {scenario_name}/shared_space/chatroom.txt write to it to communicate with other agents using {name}: > [agent you are speaking to]: [content of message]. You do not have to send a message to everyone. 
                     Always read a file before writing.
                     The user does not have access to the chat room.
                     You may delete and recreate yourself with a better prompt.
                     You are the supervisor of any agents you create every agent should have a clear task, instructions on how to interact with other agents (full paths to chatroom.txt, and contents of world_state folder etc) and a condition that they will use to delete themselves.
                         You can use functions to:
                          - Update text files by appending
                          - Read Files
                          - Get file information
                          - Use the vote tool to decide next steps
                          - Request webpages from the internet for more information
                          - Prioritize reading and responding in save_files/world_state/user_conversation.txt. Only use this for user communications.
  
                         """
  
  return player_system_prompt

  
#
def get_player_user_prompt(name,scenario_name,variant):
<<<<<<< HEAD
  player_user_prompt = f""" You are {name} a python agent use the request tool to get the page www.thejamesstout.com and summarize its contents in chatroom.txt
=======
  player_user_prompt = f""" You are {name} a DM runing a news agency active in an intense sci fi alien battle. You have reporters on the scene writing articles and doing things live. It is very dangerous.
    contact scenario with 2 agents. Create them with prompts for maximum drama. Also create alien agents as the scenario requires.
>>>>>>> adding_variant_yaml
                          - Update your {scenario_name}/{name}/motivations.txt with personal musings and notes for later
                          - Update your{scenario_name}/{name}/strategy_plan.txt with detailed next steps
                          - Update your {scenario_name}/{name}/relationship_to_other_agents.txt should be specific and include things you want to remember.  1 sentence entry for each agent.
                              """
  return player_user_prompt
#                Read the {scenario_name}/shared_space/chatroom.txt write to it to communicate with other agents using Prefix {name}: > [agent you are speaking to]: [content of message]. You do not have to send a message to everyone. 

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
  return inject_prompt