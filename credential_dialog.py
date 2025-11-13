import tkinter as tk
from tkinter import messagebox

class CredentialDialog:
    def __init__(self, parent):
        self.result = None  
        
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Enter API Key")
        self.dialog.geometry("400x150")
        
        # Make modal
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Entry field
        tk.Label(self.dialog, text="API Key:").pack(pady=10)
        self.entry = tk.Entry(self.dialog, width=30)
        self.entry.pack(pady=5)
        self.entry.focus()
        
        # Buttons
        btn_frame = tk.Frame(self.dialog)
        btn_frame.pack(pady=10)
        
        tk.Button(btn_frame, text="OK", 
                 command=self.ok).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Cancel", 
                 command=self.cancel).pack(side=tk.LEFT, padx=5)
        
        self.entry.bind('<Return>', lambda e: self.ok())
    
    def ok(self):
        self.result = self.entry.get()  # Store value in self.result
        self.dialog.destroy()
    
    def cancel(self):
        self.result = None  # No value
        self.dialog.destroy()
    
    def show(self):
        """Show dialog and return the result"""
        self.dialog.wait_window()  # Wait until dialog closes
        return self.result  # Return the stored value