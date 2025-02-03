# encryption_utils.py
import os
from cryptography.fernet import Fernet

def generate_key(key_file="secret.key"):
    """Generate and store a key for AES encryption (Fernet)."""
    key = Fernet.generate_key()
    with open(key_file, "wb") as f:
        f.write(key)
    return key

def load_key(key_file="secret.key"):
    """Load the previously generated key."""
    return open(key_file, "rb").read()

def encrypt_data(data: bytes, key: bytes) -> bytes:
    """Encrypt bytes using the given key."""
    f = Fernet(key)
    return f.encrypt(data)

def decrypt_data(token: bytes, key: bytes) -> bytes:
    """Decrypt bytes using the given key."""
    f = Fernet(key)
    return f.decrypt(token)
