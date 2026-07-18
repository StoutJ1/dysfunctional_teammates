import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import threading
import time
import os
import yaml
try:
    from data_manager import DataManager
except ImportError:
    # Fallback if running from different context
    import sys
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    from data_manager import DataManager

class MultiAgentGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Multi-Agent Control GUI")
        self.root.geometry("1000x850")

        # Data Management
        self.dm = DataManager()
        self.agent_names = self.dm.agent_names
        self.current_agent_index = 0
        self.agent_data = {name: {"turn_time": 0.0} for name in self.agent_names}
        self.stop_event = threading.Event()

        # Variables
        self.vars = {
            'top_p': tk.DoubleVar(),
            'temperature': tk.DoubleVar(),
            'iteration_count': tk.IntVar(),
            'max_token_length': tk.IntVar(),
            'variant': tk.StringVar(value="default"),
            'variant_display': tk.StringVar(value="default"),
            'history': tk.StringVar(value="System Ready"),
        }

        self.tab_control = ttk.Notebook(root)
        
        self.global_tab = ttk.Frame(self.tab_control)
        self.agent_tab = ttk.Frame(self.tab_control)
        
        self.tab_control.add(self.global_tab, text='Global')
        self.tab_control.add(self.agent_tab, text='Agent')
        self.tab_control.pack(expand=1, fill="both")

        self._setup_global_tab()
        self._setup_agent_tab()

        # Threads
        self.chat_thread = threading.Thread(target=self._monitor_chatroom, daemon=True)
        self.chat_thread.start()
        self.sim_thread = threading.Thread(target=self._update_turn_times_from_file, daemon=True)
        self.sim_thread.start()

    def _setup_global_tab(self):
        # Chatroom Display
        ttk.Label(self.global_tab, text="Chatroom Contents:", font=('Arial', 12, 'bold')).pack(pady=(10, 0), anchor='w', padx=10)
        self.chatroom_display = scrolledtext.ScrolledText(self.global_tab, height=15, state='disabled')
        self.chatroom_display.pack(fill="both", expand=True, padx=10, pady=5)

        # Agent Turn List
        ttk.Label(self.global_tab, text="Agent Turn List:", font=('Arial', 12, 'bold')).pack(pady=(10, 0), anchor='w', padx=10)
        self.agent_listbox = tk.Listbox(self.global_tab, height=5, font=('Courier', 10))
        self.agent_listbox.pack(fill="x", padx=10, pady=5)
        self._update_agent_listbox()

        # Turn Times Label
        self.turn_times_label = ttk.Label(self.global_tab, text="Turn Times (s): Loading...")
        self.turn_times_label.pack(pady=5)

        # Graph
        self.fig, self.ax = plt.subplots(figsize=(5, 3), dpi=100)
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.global_tab)
        self.canvas.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=10)

    def _setup_agent_tab(self):
        container = ttk.Frame(self.agent_tab)
        container.pack(fill="both", expand=True, padx=10, pady=10)

        # Agent Selector
        ttk.Label(container, text="Select Agent:", font=('Arial', 10, 'bold')).grid(row=0, column=0, sticky='w', pady=10, padx=10)
        self.agent_selector = ttk.Combobox(container, values=self.agent_names, state="readonly", width=20)
        self.agent_selector.grid(row=0, column=1, columnspan=2, sticky='w', pady=10, padx=10)
        self.agent_selector.current(0)
        self.agent_selector.bind("<<ComboboxSelected>>", self._on_agent_selected)

        # Parameter Rows
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

        # Agent Internal Files Section
        ttk.Label(container, text="Agent Internal Files:", font=('Arial', 12, 'bold')).grid(row=8, column=0, columnspan=3, sticky='w', pady=(20, 10), padx=10)

        self.strategy_display = self._create_scrolled_text(container, "Strategy Plan:", 9)
        self.relationship_display = self._create_scrolled_text(container, "Relationships:", 10)
        self.motivation_display = self._create_scrolled_text(container, "Motivations:", 11)

        # Apply Button
        self.apply_btn = ttk.Button(container, text="Apply All Changes", command=self._apply_all_changes)
        self.apply_btn.grid(row=12, column=0, columnspan=3, pady=40)

        # Initial Load
        self._on_agent_selected(None)

    def _create_scrolled_text(self, parent, label_text, row):
        ttk.Label(parent, text=label_text).grid(row=row, column=0, sticky='nw', pady=5, padx=10)
        txt = scrolledtext.ScrolledText(parent, height=6, state='disabled', bg="#f0f0f0", width=60)
        txt.grid(row=row, column=1, columnspan=2, sticky='ew', pady=5, padx=10)
        return txt

    def _add_parameter_row(self, parent, label, var_key, min_val, max_val, row, is_int=False):
        ttk.Label(parent, text=label + ":").grid(row=row, column=0, sticky='w', pady=10, padx=10)
        var = self.vars[var_key]
        
        scale = tk.Scale(parent, from_=min_val, to=max_val, orient=tk.HORIZONTAL, variable=var, 
                        resolution=0.01 if not is_int else 1, length=300)
        scale.grid(row=row, column=1, sticky='ew', padx=10)
        
        entry = ttk.Entry(parent, textvariable=var, width=10)
        entry.grid(row=row, column=2, sticky='w', padx=10)

    def _on_variant_change(self, *args):
        val = self.vars['variant'].get()
        self.vars['variant_display'].set(val)

    def _on_agent_selected(self, event):
        name = self.agent_selector.get()
        self.current_agent_index = self.agent_names.index(name)
        self._update_agent_listbox()
        
        config = self.dm.get_agent_config(name)
        self.vars['top_p'].set(config.get('top_p', 0.9))
        self.vars['temperature'].set(config.get('temperature', 1.0))
        self.vars['iteration_count'].set(config.get('iteration_count', 50))
        self.vars['max_token_length'].set(config.get('max_token_length', 512))
        self.vars['variant'].set(config.get('variant', 'default'))
        self.vars['variant_display'].set(config.get('variant', 'default'))
        
        self.vars['history'].set(f"Loaded settings for {name}")
        self._update_history_display()
        self._load_agent_files(name)

    def _load_agent_files(self, agent_name):
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
            path1 = f"save_files/{agent_name}/{filename}"
            path2 = f"save_files/shared_space/{filename}"
            
            full_path = path1 if os.path.exists(path1) else path2
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
                display.insert(tk.END, f"File not found: {filename}")
            
            display.config(state='disabled')

    def _apply_all_changes(self):
        name = self.agent_selector.get()
        config = {
            "top_p": self.vars['top_p'].get(),
            "temperature": self.vars['temperature'].get(),
            "iteration_count": self.vars['iteration_count'].get(),
            "max_token_length": self.vars['max_token_length'].get(),
            "variant": self.vars['variant'].get()
        }
        if self.dm.save_agent_config(name, config):
            messagebox.showinfo("Success", f"Configuration for {name} updated successfully.")
        else:
            messagebox.showerror("Error", f"Failed to save configuration for {name}.")

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
        self.ax.bar(names, times, color=['skyblue', 'lightgreen', 'salmon'])
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
                content = self.dm.read_chatroom()
                if content != last_content:
                    last_content = content
                    self.root.after(0, self._update_chatroom_display, content)
            except Exception:
                pass
            time.sleep(1)

    def _update_chatroom_display(self, content):
        self.chatroom_display.config(state='normal')
        self.chatroom_display.delete('1.0', tk.END)
        self.chatroom_display.insert(tk.END, content)
        self.chatroom_display.see(tk.END)
        self.chatroom_display.config(state='disabled')

    def _update_turn_times_from_file(self):
        while not self.stop_event.is_set():
            try:
                turn_times = self.dm.get_turn_times()
                for name, time_val in turn_times.items():
                    if name in self.agent_data:
                        self.agent_data[name]["turn_time"] = time_val
                self.root.after(0, self._refresh_global_ui)
            except Exception:
                pass
            time.sleep(3)

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

