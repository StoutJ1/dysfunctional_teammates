import os
import shutil
from datetime import datetime

def backup_scenario(path, backup_dir=None):
    """
    Creates a timestamped backup of the specified directory.
    
    Args:
        path (str): The source directory path to back up.
        backup_dir (str): The destination directory for backups. 
                         Defaults to 'save_files/backups' if not provided.
    """
    if backup_dir is None:
        backup_dir = 'save_files/backups'
    
    # Create backup directory if it doesn't exist
    os.makedirs(backup_dir, exist_ok=True)
    
    # Generate timestamp for unique folder name
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_folder_name = f"{os.path.basename(path)}_backup_{timestamp}"
    backup_folder_path = os.path.join(backup_dir, backup_folder_name)
    
    # Copy the entire directory tree
    shutil.copytree(path, backup_folder_path)
    
    print(f"Backup created successfully: {backup_folder_path}")
    return backup_folder_path

