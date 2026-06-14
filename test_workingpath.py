from tool_functions import get_files_info,get_file_content,run_python_file,write_file,set_player_status, voting_tool
import os
from dotenv import load_dotenv
load_dotenv()
wd = os.environ.get("WORKING_DIRECTORY")
print(wd)
print(get_file_content.get_file_content(wd,"save_files/shared_space/chatroom.txt"))