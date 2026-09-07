import os
import json
import base64
from typing import Optional
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend
import secrets

CONFIG_DIR = os.path.join(os.path.dirname(__file__), "config")
os.makedirs(CONFIG_DIR, exist_ok=True)
KEY_FILE = os.path.join(CONFIG_DIR, "secret.key")
PIN_FILE = os.path.join(CONFIG_DIR, "pin.json")


def _derive_key_from_passphrase(passphrase: str, salt: bytes) -> bytes:
    from cryptography.hazmat.primitives.kdf.scrypt import Scrypt
    kdf = Scrypt(salt=salt, length=32, n=2**14, r=8, p=1)
    return kdf.derive(passphrase.encode("utf-8"))


def ensure_keys_initialized():
    if not os.path.exists(KEY_FILE):
        # Generate a random AES-256 key and store with salt
        salt = secrets.token_bytes(16)
        key = secrets.token_bytes(32)
        payload = {"salt": base64.b64encode(salt).decode(), "key": base64.b64encode(key).decode()}
        with open(KEY_FILE, "w") as f:
            json.dump(payload, f)

    if not os.path.exists(PIN_FILE):
        # Default admin PIN '1234' hashed with SHA256
        default_pin_hash = hashes.Hash(hashes.SHA256(), backend=default_backend())
        default_pin_hash.update(b"1234")
        digest = default_pin_hash.finalize()
        with open(PIN_FILE, "w") as f:
            json.dump({"pin_hash": base64.b64encode(digest).decode()}, f)


def _load_key() -> bytes:
    with open(KEY_FILE, "r") as f:
        payload = json.load(f)
    return base64.b64decode(payload["key"])  # 32 bytes for AES-256


def encrypt_bytes(data: bytes) -> bytes:
    key = _load_key()
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    aesgcm = AESGCM(key)
    nonce = secrets.token_bytes(12)
    ct = aesgcm.encrypt(nonce, data, None)
    return nonce + ct


def decrypt_bytes(enc: bytes) -> bytes:
    key = _load_key()
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    aesgcm = AESGCM(key)
    nonce = enc[:12]
    ct = enc[12:]
    return aesgcm.decrypt(nonce, ct, None)


def encrypt_str(s: Optional[str]) -> Optional[str]:
    if s is None:
        return None
    enc = encrypt_bytes(s.encode("utf-8"))
    return base64.b64encode(enc).decode()


def decrypt_str(s: Optional[str]) -> Optional[str]:
    if s is None:
        return None
    enc = base64.b64decode(s.encode())
    dec = decrypt_bytes(enc)
    return dec.decode("utf-8")


def verify_pin(pin: Optional[str]) -> bool:
    if not pin:
        return False
    with open(PIN_FILE, "r") as f:
        payload = json.load(f)
    pin_hash = hashes.Hash(hashes.SHA256(), backend=default_backend())
    pin_hash.update(pin.encode("utf-8"))
    digest = pin_hash.finalize()
    return base64.b64encode(digest).decode() == payload.get("pin_hash")


def update_pin(new_pin: str):
    """Update admin PIN hash securely."""
    pin_hash = hashes.Hash(hashes.SHA256(), backend=default_backend())
    pin_hash.update(new_pin.encode("utf-8"))
    digest = pin_hash.finalize()
    with open(PIN_FILE, "w") as f:
        json.dump({"pin_hash": base64.b64encode(digest).decode()}, f)
