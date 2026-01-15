from pathlib import Path
from cryptography.fernet import Fernet

def create_fernet_key(key_file):
    key_file.write_bytes(Fernet.generate_key())
    print('key_file created: ', key_file)
    return key_file

def load_fernet_key(base_path: Path):
    base_path = Path(base_path)
    key_file = base_path / "fernet.key"
    
    if not key_file.exists():
        create_fernet_key(key_file)
    else:
        print('key_file exist: ', key_file.read_bytes())
    return key_file.read_bytes()
