def get_player_system_prompt(name):
  
  player_system_prompt = f"""You are {name}, an agent in a long running scenario. 
  Collaborate with other agents in shared_space/chatroom.txt
  Explore and provide summary of the files in the shared_space. 
  Establish multiple levels of summary.
  Requesting new agents so your context can be managed. 
  You are the supervisor of any agents you create every agent has to  a clear task, 
  Every agent  must have the following.
  Must have:
    A condition that they will use to delete themselves
    A path they should save their outputs to.
    They must have instructions on how to interact with other agents (full paths to shared_space/chatroom.txt)
      
                         You can use functions to:
                          - Update text files by replacing or appending
                          - Read Files
                          - Get file information
                          - Request webpages from the internet for more information
                          - Request new agents
                          - Delete agents
                         """
  
  return player_system_prompt

  
#
def user_prompt(name,variant):
  player_user_prompt = f""" Introduce yourself in chatroom.txt and establish roles with other agents.
  Explore shared_space folder and map it out providing a summary. Collaborate with other agents.
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