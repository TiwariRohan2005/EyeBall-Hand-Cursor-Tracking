import json
import os
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

class UserStorage:
    def __init__(self, file_path=".user_profiles.enc"):
        self.file_path = file_path
        
        password = b"true_eyeball_secret_key_123"
        salt = b"static_salt_for_local"
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password))
        self.fernet = Fernet(key)

    def _read_raw(self):
        if not os.path.exists(self.file_path):
            return {}
        try:
            with open(self.file_path, "rb") as f:
                encrypted_data = f.read()
                if not encrypted_data: return {}
                decrypted_data = self.fernet.decrypt(encrypted_data)
                return json.loads(decrypted_data.decode('utf-8'))
        except Exception:
            return {}

    def _write_raw(self, data_dict):
        json_str = json.dumps(data_dict)
        encrypted_data = self.fernet.encrypt(json_str.encode('utf-8'))
        with open(self.file_path, "wb") as f:
            f.write(encrypted_data)

    def get_all_users(self):
        return self._read_raw()

    def add_user(self, user_id, profile):
        data = self._read_raw()
        data[user_id] = profile
        self._write_raw(data)

    def delete_user(self, user_id):
        data = self._read_raw()
        if user_id in data:
            del data[user_id]
            self._write_raw(data)
            return True
        return False

    def rename_user(self, old_id, new_id):
        data = self._read_raw()
        if old_id in data and new_id not in data:
            data[new_id] = data.pop(old_id)
            self._write_raw(data)
            return True
        return False
