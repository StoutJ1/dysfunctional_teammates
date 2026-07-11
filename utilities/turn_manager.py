import os
def new_turn(scenario_name: str = "scenario"):
    shared_space_path = os.path.join("agent_working_folder",scenario_name, 'shared_space')
    
    if not os.path.exists(shared_space_path):
        print(f"Error: shared_space directory not found at {shared_space_path}")
        return
    
    # Get all files in shared_space
    files_in_shared_space = os.listdir(shared_space_path)
    
    # Process player_status.txt to reset ready messages (keep names, remove ready_for_next_day)
    player_status_file = os.path.join(shared_space_path, 'player_status.txt')
    
    if os.path.exists(player_status_file):
        with open(player_status_file, 'w') as f:
            f.write("")
            
    # Remove other text files in shared_space (except player_status.txt)
    #TODO This isn't deleting.
    to_delete_files_shared_space = ["chat_room.txt"]
    for filename in to_delete_files_shared_space:
        file_path = os.path.join(shared_space_path, filename)
        if os.path.isfile(file_path):
            if filename != 'player_status.txt':
                os.remove(file_path)
                print(f"Removed shared space file: {filename}")
    
    print("New Day shared space reset")
