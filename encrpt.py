from cryptography.fernet import Fernet
import os

KEYFILE = ("fernet.key")

def generate_key():
    key = Fernet.generate_key()
    with open(KEYFILE,"wb") as f:
        f.write(key)
    return key


def load_key():
    if os.path.exists(KEYFILE):
        with open(KEYFILE, "rb") as f:
            return f.read()
    return generate_key()


def get_fernet():
    key = load_key()
    return Fernet(key)

def encrypt_bytes(data_bytes: bytes) -> bytes:
    f = get_fernet()
    return f.encrypt(data_bytes)

def decrypt_bytes(token: bytes) -> bytes:
    f = get_fernet()
    return f.decrypt(token)
