from getpass import getpass
import time
import re
import os
from user_manager import UserManager
from finance_tracker import FinanceTracker
from gui import LoginGUI  
import tkinter as tk

def secure_password_cleanup(pwd: str):
    """Overwrite password in memory"""
    if pwd:
        pwd = 'x' * len(pwd)
    del pwd

def is_valid_username(username: str) -> bool:
    """Check if username meets requirements"""
    return 4 <= len(username) <= 20 and username.isalnum()

def is_strong_password(password: str) -> bool:
    """Check password strength requirements"""
    if len(password) < 8:
        return False
    if not re.search(r'[A-Z]', password):
        return False
    if not re.search(r'[0-9]', password):
        return False
    if not re.search(r'[^A-Za-z0-9]', password):
        return False
    return True

def main():
    # Initialize the user manager
    user_manager = UserManager()
    
    # Start the GUI application
    root = tk.Tk()
    LoginGUI(root, user_manager)
    root.mainloop()

if __name__ == "__main__":
    main()
