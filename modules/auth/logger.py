import logging
import os

class AuthLogger:
    def __init__(self, log_file="auth_logs.log"):
        self.logger = logging.getLogger("AuthLogger")
        self.logger.setLevel(logging.INFO)
        
        if not self.logger.handlers:
            fh = logging.FileHandler(log_file)
            formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
            fh.setFormatter(formatter)
            self.logger.addHandler(fh)

    def login(self, user_id):
        self.logger.info(f"Login success: {user_id}")

    def logout(self, user_id, duration):
        self.logger.info(f"Logout/Lock: {user_id}. Session Duration: {duration:.2f}s")

    def failed_auth(self, reason):
        self.logger.warning(f"Failed authentication: {reason}")
        
    def unauthorized_attempt(self):
        self.logger.warning("Unauthorized access attempt blocked. Face did not match.")
