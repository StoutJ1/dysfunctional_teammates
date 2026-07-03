
from google.genai import types
from tool_functions import get_files_info,get_file_content,run_python_file,write_file,set_player_status, voting_tool

def get_config(self):
        self.available_functions = types.Tool(
        function_declarations=[get_files_info.get_files_info_schema(),
                                get_file_content.get_file_content_schema(),
                                write_file.get_write_file_schema(),
                               run_python_file.get_run_python_file_schema(),
                                #New functions from new_functions directory
                               set_player_status.get_set_player_status_schema(),
                                voting_tool.get_voting_tool_schema(),
                               voting_tool.get_consensus_schema(),
                               voting_tool.get_create_topic_schema(),
                               voting_tool.get_close_vote_schema(),
                               voting_tool.get_available_topics_schema(),
                                
                                ],)
        self.thinking_config_val = types.ThinkingConfig(thinking_budget=0)
        tools=[self.available_functions]
        self.config = types.GenerateContentConfig(thinking_config=self.thinking_config_val,system_instruction=self.system_prompt,)   
        self.config = types.GenerateContentConfig(system_instruction=self.system_prompt,        tools=[self.available_functions])
        #self.config = types.GenerateContentConfig(system_instruction=self.system_prompt)

        return self.config