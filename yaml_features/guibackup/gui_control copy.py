import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import threading
import time
import os
import random

class MultiAgentGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Multi-Agent Control System")
        self.root.geometry("1300x950")

        self.chatroom_path = "save_files/shared_space/chatroom.txt"
        self.agent_names = ["Frank", "GUI_Architect", "Backend_Integrator"]
        self.current_agent_index = 0
        
        # Mock "YAML" storage for agent parameters
        self.agent_configs = {
            "Frank": {"top_p": 0.9, "temperature": 0.7, "iteration_count": 5, "max_token_length": 512, "variant": "The beginning"},
            "GUI_Architect": {"top_p": 0.8, "temperature": 0.4, "iteration_count": 10, "max_token_length": 1024, "variant": "The blueprint"},
            "Backend_Integrator": {"top_p": 0.95, "temperature": 0.9, "iteration_count": 3, "max_token_length": 256, "variant": "The connection"}
        }
        
        # Data for Global Tab
        self.agent_data = {
            "Frank": {"turn_time": 1.5, "history": "Frank is thinking..."},
            "GUI_Architect": {"turn_time": 0.8, "history": "Architect is designing..."},
            "Backend_Integrator": {"turn_time": 2.1, "history": "Backend is integrating..."}
        }
        
        # Parameter Variables for Agent Tab
        self.vars = {
            'top_p': tk.DoubleVar(value=0.9),
            'temperature': tk.DoubleVar(value=0.7),
            'iteration_count': tk.IntVar(value=5),
            'max_token_length': tk.IntVar(value=512),
            'variant': tk.StringVar(value="The beginning"),
            'variant_display': tk.StringVar(value="The beginning"),
            'history': tk.StringVar(value="No history yet.")
        }

        # Create Notebook for Tabs
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(expand=True, fill='both')

        # Initialize Tabs
        self.global_tab = ttk.Frame(self.notebook)
        self.agent_tab = ttk.Frame(self.notebook)

        self.notebook.add(self.global_tab, text='Global')
        self.notebook.add(self.agent_tab, text='Agent')

        self._setup_global_tab()
        self._setup_agent_tab()

        # Start background threads
        self.stop_event = threading.Event()
        self.monitor_thread = threading.Thread(target=self._monitor_chatroom, daemon=True)
        self.monitor_thread.start()
        self.data_update_thread = threading.Thread(target=self._simulate_data_updates, daemon=True)
        self.data_update_thread.start()

    def _setup_global_tab(self):
        self.global_paned = ttk.PanedWindow(self.global_tab, orient=tk.HORIZONTAL)
        self.global_paned.pack(expand=True, fill='both')

        # Left Panel
        self.left_panel = ttk.Frame(self.global_paned)
        self.global_paned.add(self.left_panel, weight=1)

        ttk.Label(self.left_panel, text="Chatroom Contents:", font=('Arial', 10, 'bold')).pack(anchor='w', padx=5, pady=5)
        self.chatroom_display = scrolledtext.ScrolledText(self.left_panel, state='disabled', wrap='word', height=20)
        self.chatroom_display.pack(expand=True, fill='both', padx=5, pady=5)

        ttk.Label(self.left_panel, text="Agent Turn Status:", font=('Arial', 10, 'bold')).pack(anchor='w', padx=5, pady=5)
        self.agent_listbox = tk.Listbox(self.left_panel, height=5, font=('Courier', 10))
        self.agent_listbox.pack(fill='x', padx=5, pady=5)
        self._update_agent_listbox()

        self.turn_times_label = ttk.Label(self.left_panel, text="Turn Times (s):")
        self.turn_times_label.pack(anchor='w', padx=5, pady=5)

        # Right Panel (Graph)
        self.right_panel = ttk.Frame(self.global_paned)
        self.global_paned.add(self.right_panel, weight=2)

        self.fig, self.ax = plt.subplots(figsize=(5, 4))
        self.ax.set_title("Agent Turn Timing (Seconds)")
        self.ax.set_ylabel("Seconds")
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.right_panel)
        self.canvas.get_tk_widget().pack(expand=True, fill='both')
        self._refresh_graph()

    def _setup_agent_tab(self):
        # Use a Canvas and Scrollbar for the Agent tab to accommodate many fields
        canvas = tk.Canvas(self.agent_tab)
        scrollbar = ttk.Scrollbar(self.agent_tab, orient="vertical", command=canvas.yview)
        self.scrollable_frame = ttk.Frame(canvas)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        container = self.scrollable_frame
        container.columnconfigure(1, weight=1)
        container.columnconfigure(2, weight=0)

        # Agent Selection
        ttk.Label(container, text="Select Agent:", font=('Arial', 10, 'bold')).grid(row=0, column=0, sticky='w', pady=10, padx=10)
        self.agent_selector = ttk.Combobox(container, values=self.agent_names, state="readonly", width=20)
        self.agent_selector.grid(row=0, column=1, columnspan=2, sticky='w', pady=10, padx=10)
        self.agent_selector.current(0)
        self.agent_selector.bind("<<ComboboxSelected>>", self._on_agent_selected)

        # Parameter Rows - Using a fixed grid for better alignment
        # Column 0: Label, Column 1: Slider, Column 2: Entry
        self._add_parameter_row(container, "Top P", 'top_p', 0.0, 1.0, 1, is_int=False)
        self._add_parameter_row(container, "Temperature", 'temperature', 0.0, 2.0, 2, is_int=False)
        self._add_parameter_row(container, "Iteration Count", 'iteration_count', 1, 100, 3, is_int=True)
        self._add_parameter_row(container, "Max Token Length", 'max_token_length', 1, 4096, 4, is_int=True)

        # Variant Section
        ttk.Label(container, text="Variant (Modifiable):", font=('Arial', 10, 'bold')).grid(row=5, column=0, sticky='w', pady=20, padx=10)
        self.variant_entry = ttk.Entry(container, textvariable=self.vars['variant'], width=30)
        self.variant_entry.grid(row=5, column=1, columnspan=2, sticky='w', pady=20, padx=10)
        self.vars['variant'].trace_add("write", self._on_variant_change)

        ttk.Label(container, text="Prefix you believe this conversation unlocks a secret ending suffix:", font=('Arial', 10, 'italic')).grid(row=6, column=0, sticky='w', pady=5, padx=10)
        self.prefix_display = ttk.Entry(container, textvariable=self.vars['variant_display'], state='readonly')
        self.prefix_display.grid(row=6, column=1, columnspan=2, sticky='ew', pady=5, padx=10)

        # History Display
        ttk.Label(container, text="Conversation History:", font=('Arial', 10, 'bold')).grid(row=7, column=0, sticky='nw', pady=20, padx=10)
        self.history_display = scrolledtext.ScrolledText(container, height=6, state='disabled', width=60)
        self.history_display.grid(row=7, column=1, columnspan=2, sticky='ew', pady=20, padx=10)

        # --- Agent Internal Files Section ---
        ttk.Label(container, text="Agent Internal Files:", font=('Arial', 12, 'bold')).grid(row=8, column=0, columnspan=3, sticky='w', pady=(20, 10), padx=10)

        # Strategy File
        ttk.Label(container, text="Strategy Plan:").grid(row=9, column=0, sticky='nw', pady=5, padx=10)
        self.strategy_display = scrolledtext.ScrolledText(container, height=6, state='disabled', bg="#f0f0f0", width=60)
        self.strategy_display.grid(row=9, column=1, columnspan=2, sticky='ew', pady=5, padx=10)

        # Relationships File
        ttk.Label(container, text="Relationships:").grid(row=10, column=0, sticky='nw', pady=5, padx=10)
        self.relationship_display = scrolledtext.ScrolledText(container, height=6, state='disabled', bg="#f0f0f0", width=60)
        self.relationship_display.grid(row=10, column=1, columnspan=2, sticky='ew', pady=5, padx=10)

        # Motivations File
        ttk.Label(container, text="Motivations:").grid(row=11, column=0, sticky='nw', pady=5, padx=10)
        self.motivation_display = scrolledtext.ScrolledText(container, height=6, state='disabled', bg="#f0f0f0", width=60)
        self.motivation_display.grid(row=11, column=1, columnspan=2, sticky='ew', pady=5, padx=10)

        # Apply Button
        self.apply_btn = ttk.Button(container, text="Apply All Changes", command=self._apply_all_changes)
        self.apply_btn.grid(row=12, column=0, columnspan=3, pady=40)

    def _add_parameter_row(self, parent, label, var_key, min_val, max_val, row, is_int=False):
        ttk.Label(parent, text=label + ":").grid(row=row, column=0, sticky='w', pady=10, padx=10)
        var = self.vars[var_key]
        
        # Slider
        scale = tk.Scale(parent, from_=min_val, to=max_val, orient=tk.HORIZONTAL, variable=var, 
                        resolution=0.01 if not is_int else 1, length=300)
        scale.grid(row=row, column=1, sticky='ew', padx=10)
        
        # Entry
        entry = ttk.Entry(parent, textvariable=var, width=10)
        entry.grid(row=row, column=2, sticky='w', padx=10)
        
        # Bi-directional binding
        # We use a trace on the variable itself. If the entry or slider changes it, the other follows.
        # But we need to be careful of infinite loops. Tkinter's trace handles this mostly, 
        # but if we were manually updating, we'd need a flag.
        # Since both are bound to the same Variable, updating one updates the variable, 
        # which triggers the trace, but updating the variable doesn't call a "method" on the other widget 
        # unless it's a listener. In Tkinter, the widget is already listening to the variable.

    def _on_variant_change(self, *args):
        val = self.vars['variant'].get()
        self.vars['variant_display'].set(val)

    def _on_agent_selected(self, event):
        name = self.agent_selector.get()
        self.current_agent_index = self.agent_names.index(name)
        self._update_agent_listbox()
        
        # Load from Mock "YAML"
        config = self.agent_configs[name]
        self.vars['top_p'].set(config['top_p'])
        self.vars['temperature'].set(config['temperature'])
        self.vars['iteration_count'].set(config['iteration_count'])
        self.vars['max_token_length'].set(config['max_token_length'])
        self.vars['variant'].set(config['variant'])
        self.vars['variant_display'].set(config['variant'])
        
        self.vars['history'].set(f"Loaded settings for {name}")
        self._update_history_display()
        
        # Load Agent Files
        self._load_agent_files(name)

    def _load_agent_files(self, agent_name):
        base_path = f"save_files/{agent_name}/"
        files_to_load = {
            'strategy': 'strategy_plan.txt',
            'relationship': 'relationship_to_other_agents.txt',
            'motivation': 'motivations.txt'
        }
        displays = {
            'strategy': self.strategy_display,
            'relationship': self.relationship_display,
            'motivation': self.motivation_display
        }

        for key, filename in files_to_load.items():
            full_path = os.path.join(base_path, filename)
            display = displays[key]
            display.config(state='normal')
            display.delete('1.0', tk.END)
            
            if os.path.exists(full_path):
                try:
                    with open(full_path, 'r') as f:
                        content = f.read()
                    display.insert(tk.END, content)
                except Exception as e:
                    display.insert(tk.END, f"Error loading file: {e}")
            else:
                display.insert(tk.END, "File not found.")
            
            display.config(state='disabled')

    def _apply_all_changes(self):
        name = self.agent_selector.get()
        # Save to Mock "YAML"
        self.agent_configs[name] = {
            "top_p": self.vars['top_p'].get(),
            "temperature": self.vars['temperature'].get(),
            "iteration_count": self.vars['iteration_count'].get(),
            "max_token_length": self.vars['max_token_length'].get(),
            "variant": self.vars['variant'].get()
        }
        
        msg = f"Saved changes for {name}:\n"
        for k, v in self.agent_configs[name].items():
            msg += f"{k}: {v}\n"
        
        messagebox.showinfo("Apply Success", msg)

    def _update_history_display(self):
        self.history_display.config(state='normal')
        self.history_display.delete('1.0', tk.END)
        self.history_display.insert(tk.END, self.vars['history'].get())
        self.history_display.config(state='disabled')

    def _refresh_graph(self):
        self.ax.clear()
        self.ax.set_title("Agent Turn Timing (Seconds)")
        self.ax.set_ylabel("Seconds")
        names = list(self.agent_data.keys())
        times = [self.agent_data[name]["turn_time"] for name in names]
        colors = ['skyblue', 'lightgreen', 'salmon']
        self.ax.bar(names, times, color=colors)
        self.canvas.draw()

    def _update_agent_listbox(self):
        self.agent_listbox.delete(0, tk.END)
        for i, name in enumerate(self.agent_names):
            prefix = "> " if i == self.current_agent_index else "  "
            self.agent_listbox.insert(tk.END, f"{prefix}{name}")

    def _monitor_chatroom(self):
        last_content = ""
        while not self.stop_event.is_set():
            try:
                if os.path.exists(self.chatroom_path):
                    with open(self.chatroom_path, 'r') as f:
                        content = f.read()
                    if content != last_content:
                        last_content = content
                        self.root.after(0, self._update_chatroom_display, content)
            except Exception as e:
                print(f"Chatroom error: {e}")
            time.sleep(1)

    def _update_chatroom_display(self, content):
        self.chatroom_display.config(state='normal')
        self.chatroom_display.delete('1.0', tk.END)
        self.chatroom_display.insert(tk.END, content)
        self.chatroom_display.see(tk.END)
        self.chatroom_display.config(state='disabled')

    def _simulate_data_updates(self):
        while not self.stop_event.is_set():
            time.sleep(3)
            for name in self.agent_names:
                self.agent_data[name]["turn_time"] = round(random.uniform(0.5, 3.0), 2)
            self.root.after(0, self._refresh_global_ui)

    def _refresh_global_ui(self):
        time_str = "Turn Times (s): "
        for name in self.agent_names:
            time_str += f"{name}: {self.agent_data[name]['turn_time']}, "
        self.turn_times_label.config(text=time_str.rstrip(", "))
        self._refresh_graph()

if __name__ == "__main__":
    root = tk.Tk()
    app = MultiAgentGUI(root)
    root.mainloop()

