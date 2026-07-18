import yaml
import os

class DataManager:
    def __init__(self, base_dir="save_files", chatroom_path="save_files/shared_space/chatroom.txt"):
        self.base_dir = base_dir
        self.chatroom_path = chatroom_path
        self.agent_names = ['Frank', 'GUI_Architect', 'Backend_Integrator']

    def get_agent_config_path(self, agent_name):
        return os.path.join(self.base_dir, agent_name, "config.yaml")

    def load_all_configs(self):
        configs = {}
        for name in self.agent_names:
            configs[name] = self.get_agent_config(name)
        return configs

    def get_agent_config(self, agent_name):
        path = self.get_agent_config_path(agent_name)
        if os.path.exists(path):
            try:
                with open(path, 'r') as f:
                    return yaml.safe_load(f)
            except Exception as e:
                print(f"Error loading config for {agent_name}: {e}")
        
        # Default config if not found
        return {
            "top_p": 0.9,
            "temperature": 1.0,
            "iteration_count": 50,
            "max_token_length": 512,
            "variant": "default"
        }

    def save_agent_config(self, agent_name, config):
        path = self.get_agent_config_path(agent_name)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        try:
            with open(path, 'w') as f:
                yaml.dump(config, f)
            return True
        except Exception as e:
            print(f"Error saving config for {agent_name}: {e}")
            return False

    def read_chatroom(self):
        if os.path.exists(self.chatroom_path):
            try:
                with open(self.chatroom_path, 'r') as f:
                    return f.read()
            except Exception as e:
                print(f"Error reading chatroom: {e}")
        return ""

    def get_turn_times(self):
        # For now, we'll look for a turn_times.yaml in the base_dir
        path = os.path.join(self.base_dir, "turn_times.yaml")
        if os.path.exists(path):
            try:
                with open(path, 'r') as f:
                    return yaml.safe_load(f)
            except Exception as e:
                print(f"Error reading turn times: {e}")
        return {name: 0.0 for name in self.agent_names}

