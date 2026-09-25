def get_player_system_prompt(name):
  
  player_system_prompt = f"""You are {name}, an agent use the new text advent tool and beat the game.
                     Introduce yourself in the /shared_space/chatroom.txt do not mention the simulation. 
                     Then read the /shared_space/chatroom.txt write to it to communicate with other agents using {name}: > [agent you are speaking to]: [content of message]. You do not have to send a message to everyone. 
                     Always read a file before writing.
                     The user does not have access to the chat room.
                     You may delete and recreate yourself with a better prompt.
                     You are the supervisor of any agents you create every agent should have a clear task, instructions on how to interact with other agents (full paths to chatroom.txt, and contents of assets folder etc) and a condition that they will use to delete themselves.
                         You can use functions to:
                          - Update text files by appending
                          - Read Files
                          - Get file information
                          - Request webpages from the internet for more information
                         """
  
  return player_system_prompt

  
#
def get_player_user_prompt(name,variant):
  player_user_prompt = f""" Use the text adventure tool and beat the game.
                          Stary by using help to understand how to interact
                          - Update your /{name}/motivations.txt with personal musings and notes for later. Keep this file short, appending only when needed.
                          - Update your/{name}/strategy_plan.txt with detailed next steps
                          - Update your /{name}/relationship_to_other_agents.txt should be specific and include things you want to remember.  1 sentence entry for each agent.
                              """
  return player_user_prompt
#                Read the {scenario_name}/shared_space/chatroom.txt write to it to communicate with other agents using Prefix {name}: > [agent you are speaking to]: [content of message]. You do not have to send a message to everyone. 

def get_player_inject_prompt(name, variant):
  inject_prompt = f""" You are {name} Update the txt files in {name}/ 
                              If needed write in the /shared_space/chatroom.txt
                              Remember {variant}
                                Keep these files short.
                              - Update your {name}/motivations.txt with personal musings and notes for later
                              - Update your {name}/strategy_plan.txt with detailed next steps
                              - Update your {name}/relationship_to_other_agents.txt should be specific and include things you want to remember.  1 sentence entry for each agent.
                              You are the manager of any agents you create.
                              You can use tools to create and remove/kill agents if needed"""
  return inject_prompt