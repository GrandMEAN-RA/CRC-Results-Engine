
import hashlib

ADMIN_KEY_HASH = hashlib.sha256(
    b"CRC-ADMIN-2025-OVERRIDE"
).hexdigest()

def validate_admin_key(input_key):
    return hashlib.sha256(input_key.encode()).hexdigest() == ADMIN_KEY_HASH
