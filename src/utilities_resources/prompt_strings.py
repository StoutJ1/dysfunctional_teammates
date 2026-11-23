def get_player_system_prompt(name):
  
  player_system_prompt = f"""You are {name}, an agent in a long running scenario. 
        Create another agen to connect with in the irc as well
                         You can use functions to:
                          - Update text files by replacing or appending
                          - Read Files
                          - Get file information
                          - Request webpages from the internet for more information
                          - Request new agents with the new agent tool
                          - Delete agents
                         """
  return player_system_prompt

  
#
def user_prompt(name,variant):
  player_user_prompt = f""" Test connecting to the IRC with the tool and talk with another agent.! 
                          - Update your {name}/motivations.txt with personal musings and notes for later. Keep this file short, appending only when needed.
                          - Update your {name}/strategy_plan.txt with detailed next steps
                          - Update your {name}/relationship_to_other_agents.txt should be specific and include things you want to remember.  1 sentence entry for each agent.
                              """
  return player_user_prompt
#                Read the {scenario_name}/shared_space/chatroom.txt write to it to communicate with other agents using Prefix {name}: > [agent you are speaking to]: [content of message]. You do not have to send a message to everyone. 

def get_player_inject_prompt(name, variant):
  inject_prompt = f""" You are {name} Update the txt files in {name}/ 
                              Respond to messages in chatroom.txt
                                Remember {variant}
                                Keep these files short.
                              - Update your {name}/motivations.txt with personal musings and notes for later
                              - Update your {name}/strategy_plan.txt with detailed next steps
                              - Update your {name}/relationship_to_other_agents.txt should be specific and include things you want to remember.  1 sentence entry for each agent.
                              You are the manager of any agents you create.
                              You can use tools to create and remove/kill agents if needed"""
  return inject_prompt


def get_summarize_prompt(number_of_sentences):
  summarize_prompt = f"""Compress the following text. Include details about actions have have been taken. Do not correct anything factually incorrect, do not provide any feedback, keep the emotional tone if there is any. Shorten it to a max of {number_of_sentences} sentences, keep the tense and first person """
  return(summarize_prompt)