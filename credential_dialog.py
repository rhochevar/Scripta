import json
import os
import tkinter as tk
from typing import Optional
from tkinter import messagebox

class CredentialDialog:
    api_key: str = ""

    def __init__(self, parent):
        self.result : Optional[str] = None
        self.config_file = "config.json" 

        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                    self.api_key = config.get('api_key')
        except Exception as e:
            print(e)
        
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Scripta - Enter API Key")
        self.dialog.geometry("400x150")
        
        # Make modal
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Entry field
        tk.Label(self.dialog, text="API Key:").pack(pady=10)
        self.entry = tk.Entry(self.dialog, width=50)
        try:
            self.entry.insert(0, self.api_key) # Show current API key if stored
        except Exception as e:
            print(f"config.json file not found: {e}")
        self.entry.pack(pady=5)
        self.entry.focus()
        
        # Buttons
        btn_frame = tk.Frame(self.dialog)
        btn_frame.pack(pady=10)
        
        tk.Button(btn_frame, text="Save", 
                 command=self.save).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Cancel", 
                 command=self.cancel).pack(side=tk.LEFT, padx=5)
        
        self.entry.bind('<Return>', lambda e: self.save())
    
    def save(self):
        self.result = self.entry.get()  # Store value in self.result

        try: # Attempt to dump config to json file
            config = {'api_key': self.result.strip()}
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=2)
            print("Configuration saved")
        except Exception as e:
            print(f"Error saving config: {e}")
            messagebox.showerror("Error", f"Failed to save configuration: {e}")
        self.dialog.destroy()
    
    def cancel(self):
        self.result = None  # No value
        self.dialog.destroy()
    
    def show(self):
        """Show dialog and return the result"""
        self.dialog.wait_window()  # Wait until dialog closes
        return self.result.strip()  # Return the stored value
    
