import os
import json
import hashlib
import binascii
import time
from datetime import datetime
import pandas as pd

class UserManager:
    """Handles user authentication with persistent session storage"""
    
    def __init__(self):
        self.users_root = "user_data"
        self.current_user = None
        self.failed_attempts = {}
        self.session_timeout = 1800  # 30 minutes
        self.session_start = None
        os.makedirs(self.users_root, exist_ok=True)
        os.chmod(self.users_root, 0o700)

    def _get_user_folder(self, username: str) -> str:
        """Create and return user-specific folder path"""
        username = "".join(c for c in username.lower() if c.isalnum())
        if not username:
            raise ValueError("Invalid username")
            
        user_folder = os.path.join(self.users_root, f"user_{username}")
        os.makedirs(user_folder, exist_ok=True)
        os.chmod(user_folder, 0o700)
        
        for subdir in ['data', 'graphs', 'reports']:
            subdir_path = os.path.join(user_folder, subdir)
            os.makedirs(subdir_path, exist_ok=True)
            os.chmod(subdir_path, 0o700)
        
        return user_folder

    def _get_session_files(self, username: str) -> dict:
        """Generate paths for all session files"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        user_folder = self._get_user_folder(username)
        
        return {
            'current_json': os.path.join(user_folder, 'data', f"session_{timestamp}.json"),
            'current_csv': os.path.join(user_folder, 'data', f"transactions_{timestamp}.csv"),
            'latest_json': os.path.join(user_folder, 'latest_data.json'),
            'graphs_dir': os.path.join(user_folder, 'graphs'),
            'reports_dir': os.path.join(user_folder, 'reports')
        }

    def _hash_password(self, password: str) -> str:
        """Secure password hashing with PBKDF2-HMAC-SHA512"""
        salt = hashlib.sha256(os.urandom(60)).hexdigest().encode('ascii')
        pwdhash = hashlib.pbkdf2_hmac(
            'sha512',
            password.encode('utf-8'),
            salt,
            100000
        )
        return (salt + binascii.hexlify(pwdhash)).decode('ascii')

    def _verify_password(self, stored_hash: str, provided_password: str) -> bool:
        """Verify password against stored hash"""
        if not stored_hash or len(stored_hash) < 64:
            return False
            
        salt = stored_hash[:64].encode('ascii')
        stored_pwd = stored_hash[64:]
        pwdhash = binascii.hexlify(
            hashlib.pbkdf2_hmac(
                'sha512',
                provided_password.encode('utf-8'),
                salt,
                100000
            )
        ).decode('ascii')
        return pwdhash == stored_pwd

    def create_user(self, username: str, password: str) -> dict:
        """Create new user with organized storage"""
        try:
            username = username.lower().strip()
            
            if not (4 <= len(username) <= 20 and username.isalnum()):
                return {"status": "error", "message": "Username must be 4-20 alphanumeric characters"}
            
            user_folder = self._get_user_folder(username)
            user_file = os.path.join(user_folder, 'latest_data.json')
            if os.path.exists(user_file):
                return {"status": "error", "message": "Username already exists"}
            
            user_data = {
                "username": username,
                "password_hash": self._hash_password(password),
                "created_at": datetime.now().isoformat(),
                "last_login": None,
                "transactions": [],
                "transaction_history": []  # Added for complete history
            }
            
            with open(user_file, 'w') as f:
                json.dump(user_data, f, indent=4)
            os.chmod(user_file, 0o600)
            
            return {"status": "success"}
        except Exception as e:
            return {"status": "error", "message": f"Account creation failed: {str(e)}"}

    def verify_user(self, username: str, password: str) -> dict:
        """Authenticate user and initialize session"""
        username = username.lower().strip()
        attempts, lockout_time = self.failed_attempts.get(username, (0, 0))
        
        if attempts >= 3 and time.time() < lockout_time + 300:
            remaining = int(lockout_time + 300 - time.time())
            return {
                "status": "error",
                "message": f"Account locked. Try again in {remaining//60}m {remaining%60}s"
            }
        
        try:
            user_folder = self._get_user_folder(username)
            latest_file = os.path.join(user_folder, 'latest_data.json')
            
            if not os.path.exists(latest_file):
                return {"status": "error", "message": "Username not found"}
            
            with open(latest_file, 'r') as f:
                user_data = json.load(f)
                
                if not self._verify_password(user_data['password_hash'], password):
                    self.failed_attempts[username] = (attempts + 1, time.time())
                    return {"status": "error", "message": "Incorrect password"}
                
                # Update user data
                user_data['last_login'] = datetime.now().isoformat()
                self.current_user = user_data
                self.session_start = time.time()
                
                # Save updated data (only metadata changes)
                with open(latest_file, 'w') as f:
                    json.dump(user_data, f, indent=4)
                
                return {"status": "success", "user_data": user_data}
                
        except Exception as e:
            return {"status": "error", "message": f"Login failed: {str(e)}"}

    def save_user_data(self, transactions: list = None) -> bool:
        """Save complete user data with session tracking"""
        if not self.current_user:
            return False
            
        try:
            username = self.current_user['username']
            files = self._get_session_files(username)
            
            if transactions is not None:
                # Add new transactions to history
                formatted_transactions = [
                    {
                        **txn,
                        'date': txn['date'].strftime("%Y-%m-%d") 
                        if isinstance(txn['date'], datetime) 
                        else txn['date']
                    }
                    for txn in transactions
                ]
                
                self.current_user['transactions'] = formatted_transactions
                self.current_user['transaction_history'].extend(formatted_transactions)
            
            # Save session snapshot (new file each time)
            with open(files['current_json'], 'w') as f:
                json.dump(self.current_user, f, indent=4)
            os.chmod(files['current_json'], 0o600)
            
            # Save complete current state (overwrites latest)
            with open(files['latest_json'], 'w') as f:
                json.dump(self.current_user, f, indent=4)
            os.chmod(files['latest_json'], 0o600)
            
            # Save CSV version
            if self.current_user.get('transactions'):
                df = pd.DataFrame(self.current_user['transactions'])
                df.to_csv(files['current_csv'], index=False)
                os.chmod(files['current_csv'], 0o600)
            
            return True
        except Exception as e:
            print(f"Error saving user data: {e}")
            return False

    def logout(self):
        """Clean up session data"""
        if self.current_user:
            self.save_user_data()
            self.current_user = None
            self.session_start = None

    def check_session(self) -> bool:
        """Validate active session"""
        if self.current_user and self.session_start:
            if time.time() - self.session_start > self.session_timeout:
                self.logout()
                return False
            return True
        return False