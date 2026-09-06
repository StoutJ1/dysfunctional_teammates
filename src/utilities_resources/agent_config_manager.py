import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import yaml
import os
from dotenv import load_dotenv
from pathlib import Path

class AgentConfigManager:
    def __init__(self, root, directory):
        self.root = root
        self.root.title("Agent Config Manager")
        self.directory = directory
        self.current_file = None
        self.current_data = {}
        self.chatroom_path = os.environ.get("WORKING_DIRECTORY")+'save_files/shared_space/chatroom.txt'

        # Main Notebook for tabs
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        # Config Tab
        self.config_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.config_frame, text="Agent Config")

        # Chatroom Tab
        self.chat_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.chat_frame, text="Chatroom")

        # Setup Config Tab Layout
        self.setup_config_tab()
        
        # Setup Chatroom Tab Layout
        self.setup_chatroom_tab()

        self.refresh_file_list()

    def setup_config_tab(self):
        # Main layout within config tab
        self.paned_window = ttk.PanedWindow(self.config_frame, orient=tk.HORIZONTAL)
        self.paned_window.pack(fill=tk.BOTH, expand=True)

        # Left Frame: File List
        self.left_frame = ttk.Frame(self.paned_window)
        self.paned_window.add(self.left_frame, weight=1)

        self.file_listbox = tk.Listbox(self.left_frame)
        self.file_listbox.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.file_listbox.bind('<<ListboxSelect>>', self.on_file_select)
        
        self.refresh_button = ttk.Button(self.left_frame, text="Refresh Files", command=self.refresh_file_list)
        self.refresh_button.pack(fill=tk.X, padx=2, pady=2)


        # Right Frame: Editor
        self.right_frame = ttk.Frame(self.paned_window)
        self.paned_window.add(self.right_frame, weight=4)

        # Editor Widgets
        self.create_editor_widgets()

    def setup_chatroom_tab(self):
        # Chatroom layout
        self.chat_text = tk.Text(self.chat_frame, state="disabled", wrap=tk.WORD)
        self.chat_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.chat_refresh_button = ttk.Button(self.chat_frame, text="Refresh Chat", command=self.refresh_chatroom)
        self.chat_refresh_button.pack(pady=5)
        
        # Load chat initially
        self.refresh_chatroom()

    def refresh_chatroom(self):
        try:
            if os.path.exists(self.chatroom_path):
                with open(self.chatroom_path, 'r') as f:
                    content = f.readlines()
                new_content = []
                for line in content:
                    new_content.append(line+"\n")
                    new_content.append("-"*50+"\n")

                self.chat_text.config(state="normal")
                self.chat_text.delete("1.0", tk.END)
                self.chat_text.insert("1.0", "".join(new_content))
                self.chat_text.see(tk.END)
                self.chat_text.config(state="disabled")
            else:
                self.chat_text.config(state="normal")
                self.chat_text.delete("1.0", tk.END)
                self.chat_text.insert("1.0", "Chatroom file not found.")
                self.chat_text.config(state="disabled")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load chatroom: {e}")

    def create_editor_widgets(self):
        # Use a canvas and scrollbar for the editor part
        self.canvas = tk.Canvas(self.right_frame)
        self.scrollbar = ttk.Scrollbar(self.right_frame, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = ttk.Frame(self.canvas)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        # Fields

        # User Prompt (Read Only)
        ttk.Label(self.scrollable_frame, text="User Prompt (Read Only):").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.user_prompt_entry = tk.Text(self.scrollable_frame, height=10, background='light gray')
        self.user_prompt_entry.grid(row=0, column=1, columnspan=2, sticky="ew", padx=5, pady=5)
        
        # Max Tokens
        ttk.Label(self.scrollable_frame, text="Max Tokens:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        self.token_slider = ttk.Scale(self.scrollable_frame, from_=50, to=20000, orient=tk.HORIZONTAL, command=self._sync_tokens)
        self.token_slider.grid(row=1, column=1, sticky="ew", padx=5, pady=5)
        self.token_entry = ttk.Entry(self.scrollable_frame, width=10)
        self.token_entry.grid(row=1, column=2, padx=5, pady=5)
        self.token_entry.bind("<Return>", lambda e: self.on_entry_move())

        # Iterations
        ttk.Label(self.scrollable_frame, text="Iterations:").grid(row=2, column=0, sticky="w", padx=5, pady=5)
        self.iter_slider = ttk.Scale(self.scrollable_frame, from_=1, to=100, orient=tk.HORIZONTAL, command=self._sync_iters)
        self.iter_slider.grid(row=2, column=1, sticky="ew", padx=5, pady=5)
        self.iter_entry = ttk.Entry(self.scrollable_frame, width=10)
        self.iter_entry.grid(row=2, column=2, padx=5, pady=5)
        self.iter_entry.bind("<Return>", lambda e: self.on_entry_move())

        # System Prompt
        ttk.Label(self.scrollable_frame, text="System Prompt:").grid(row=3, column=0, sticky="nw", padx=5, pady=5)
        self.system_text = tk.Text(self.scrollable_frame, height=15, width=50)
        self.system_text.grid(row=3, column=1, columnspan=2, sticky="nsew", padx=5, pady=5)

        # Pending Injection
        ttk.Label(self.scrollable_frame, text="Pending Inject Prompt:").grid(row=4, column=0, sticky="nw", padx=5, pady=5)
        self.pending_inject = tk.Text(self.scrollable_frame, height=1, width=50)
        self.pending_inject.grid(row=4, column=1, columnspan=2, sticky="nsew", padx=5, pady=5)

        # Variant
        ttk.Label(self.scrollable_frame, text="Variant:").grid(row=5, column=0, sticky="nw", padx=5, pady=5)
        self.variant = tk.Text(self.scrollable_frame, height=1, width=50)
        self.variant.grid(row=5, column=1, columnspan=2, sticky="nsew", padx=5, pady=5)
        
        # Deleted Agents (Read Only)
        ttk.Label(self.scrollable_frame, text="Deleted Agents:").grid(row=6, column=0, sticky="w", padx=5, pady=5)
        self.deleted_agents_entry = ttk.Entry(self.scrollable_frame, state="readonly")
        self.deleted_agents_entry.grid(row=6, column=1, columnspan=2, sticky="ew", padx=5, pady=5)
        
        # Save Button
        self.save_button = ttk.Button(self.scrollable_frame, text="SAVE CHANGES", command=self.save_changes)
        self.save_button.grid(row=7, column=0, columnspan=3, pady=20)

        # Configure columns
        self.scrollable_frame.columnconfigure(1, weight=1)

    def refresh_file_list(self):
        self.file_listbox.delete(0, tk.END)
        files = [f for f in os.listdir(self.directory) if f.endswith('.yaml')]
        for f in files:
            self.file_listbox.insert(tk.END, f)

    def on_file_select(self, event):
        selection = self.file_listbox.curselection()
        if not selection:
            return
        
        filename = self.file_listbox.get(selection[0])
        filepath = os.path.join(self.directory, filename)
        
        try:
            with open(filepath, 'r') as f:
                self.current_data = yaml.safe_load(f)
            
            self.current_file = filepath
            self.load_data_to_ui()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load YAML to UI: {e}")

    def load_data_to_ui(self):
        # Max Tokens
        tokens = self.current_data.get('max_tokens', 0)
        self.token_slider.set(tokens)
        self.token_entry.delete(0, tk.END)
        self.token_entry.insert(0, str(tokens))

        # Iterations
        iters = self.current_data.get('iterations', 0)
        self.iter_slider.set(iters)
        self.iter_entry.delete(0, tk.END)
        self.iter_entry.insert(0, str(iters))

        # System Prompt
        self.system_text.delete("1.0", tk.END)
        self.system_text.insert("1.0", self.current_data.get('system_prompt', ''))

        # Variant
        self.variant.delete("1.0", tk.END)
        self.variant.insert("1.0", self.current_data.get('variant', ''))

        # Pending Inject
        self.pending_inject.delete("1.0", tk.END)
        self.pending_inject.insert("1.0", self.current_data.get('pending_inject_prompt', ''))
        
        # Read only fields
        self._update_readonly_field(self.user_prompt_entry, self.current_data.get('user_prompt', ''))
        
    def _update_readonly_field(self, widget, value):
        widget.config(state="normal")
        widget.delete("1.0", tk.END)
        widget.insert("1.0", value)
        widget.config(state="disabled")

    def _sync_tokens(self, val):
        self.token_entry.delete(0, tk.END)
        self.token_entry.insert(0, str(int(float(val))))

    def _sync_iters(self, val):
        self.iter_entry.delete(0, tk.END)
        self.iter_entry.insert(0, str(int(float(val))))

    def on_entry_move(self):
        try:
            tokens = int(self.token_entry.get())
            self.token_slider.set(tokens)
        except ValueError:
            pass
        try:
            iters = int(self.iter_entry.get())
            self.iter_slider.set(iters)
        except ValueError:
            pass

    def create_new_agent(self):
        agent_name = simpledialog.askstring("New Agent", "Enter agent name:")
        if not agent_name:
            return
        
        filename = f"{agent_name}.yaml"
        filepath = os.path.join(self.directory, filename)
        
        if os.path.exists(filepath):
            messagebox.showerror("Error", "An agent with this name already exists.")
            return
        
        default_data = {
            'name': agent_name,
            'created_by': 'User',
            'iterations': 7,
            'other_agents': [],
            'pending_inject_prompt': '',
            'variant': '',
            'max_context_messages': 10,
            'system_prompt': '',
            'user_prompt': '',
            'tools': [
                'get_file_content', 'get_files_info', 'write_file', 'get_available_topics',
                'get_consensus', 'create_topic', 'submit_vote', 'close_vote',
                'request_new_agent', 'request_delete_agent', 'request_page', 'run_python_file'
            ],
            'max_tokens': 5000,
            'deleted_agents': [],
            'requested_new_agent': False,
            'new_agents': [],
            'requested_delete_agent': False,
            'delete_agents': []
        }
        
        try:
            with open(filepath, 'w') as f:
                yaml.dump(default_data, f, default_flow_style=False)
            messagebox.showinfo("Success", f"Agent {agent_name} created successfully!")
            self.refresh_file_list()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to create agent YAML: {e}")

    def save_changes(self):
        if not self.current_file:
            messagebox.showwarning("Warning", "No file selected.")
            return

        try:
            new_data = self.current_data.copy()
            new_data['max_tokens'] = int(self.token_entry.get())
            new_data['iterations'] = int(self.iter_entry.get())
            new_data['system_prompt'] = self.system_text.get("1.0", tk.END).strip()
            new_data['pending_inject_prompt'] = self.pending_inject.get("1.0", tk.END).strip()
            new_data['variant'] = self.variant.get("1.0", tk.END).strip()
            with open(self.current_file, 'w') as f:
                yaml.dump(new_data, f, default_flow_style=False)
            
            messagebox.showinfo("Success", "Configuration saved successfully!")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save YAML: {e}")

if __name__ == "__main__":
    root = tk.Tk()
    # load_dotenv path should be handled carefully. Using a relative path or env var.
    test_venv = load_dotenv("/home/will/dysfunctional_teammates/.env")


    config_path = os.environ.get("AGENT_CONFIG_PATH")
    print(config_path)
    if config_path:
        # Assuming the structure is ../[AGENT_CONFIG_PATH]/ as in the original code
        manager = AgentConfigManager(root, f"../{config_path}/")
    else:
        # Fallback for local testing if env var is missing
        manager = AgentConfigManager(root, "save_files/world_state/")
        
    root.mainloop()

