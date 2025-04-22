from getpass import getpass
import time
import re
from user_manager import UserManager
from finance_tracker import FinanceTracker

def secure_password_cleanup(pwd: str):
    """Overwrite password in memory"""
    if pwd:
        pwd = 'x' * len(pwd)
    del pwd

def show_auth_menu():
    print("\n=== Personal Finance Tracker ===")
    print("1. Login")
    print("2. Sign Up")
    print("3. Exit")

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
    user_manager = UserManager()
    
    while True:
        show_auth_menu()
        choice = input("Select option (1-3): ").strip()
        
        if choice == '1':
            max_attempts = 3
            for attempt in range(max_attempts):
                username = input("Username: ").strip().lower()
                password = getpass("Password: ")
                
                result = user_manager.verify_user(username, password)
                secure_password_cleanup(password)
                
                if result['status'] == 'success':
                    print(f"\nWelcome, {username}!")
                    try:
                        tracker = FinanceTracker(user_manager)
                        while user_manager.check_session():
                            tracker.show_menu()
                    except Exception as e:
                        print(f"Error in finance tracker: {e}")
                    finally:
                        user_manager.logout()
                    break
                
                print(f"Invalid credentials ({max_attempts-attempt-1} attempts left)")
                if attempt < max_attempts - 1:
                    time.sleep(2)  # Throttle attempts
            else:
                print("Too many failed attempts. Exiting.")
                if input("Forgot password? (y/n): ").lower() == 'y':
                    print("Please contact admin for password reset")
                break
                
        elif choice == '2':
            while True:
                username = input("Choose a username (4-20 alphanumeric chars): ").strip().lower()
                if not is_valid_username(username):
                    print("Invalid username - must be 4-20 alphanumeric characters")
                    continue
                    
                # Check if user exists by trying to get their folder
                try:
                    user_folder = user_manager._get_user_folder(username)
                    if os.path.exists(os.path.join(user_folder, 'latest_data.json')):
                        print("Username already exists")
                        continue
                    break
                except:
                    print("Invalid username")
                    continue
                    
            while True:
                password = getpass("Choose a password (min 8 chars with uppercase, number, special): ")
                if not is_strong_password(password):
                    print("Password too weak - must contain uppercase, number, and special character")
                    continue
                confirm = getpass("Confirm password: ")
                if password != confirm:
                    print("Passwords don't match!")
                    secure_password_cleanup(password)
                    secure_password_cleanup(confirm)
                    continue
                break
                
            result = user_manager.create_user(username, password)
            secure_password_cleanup(password)
            secure_password_cleanup(confirm)
            
            if result['status'] == 'success':
                print("\nAccount created successfully! Please login.")
            else:
                print(f"\nError: {result['message']}")
                
        elif choice == '3':
            print("Goodbye!")
            break
            
        else:
            print("Invalid choice! Please enter 1-3")

if __name__ == "__main__":
    import os
    main()