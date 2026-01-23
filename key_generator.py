from pathlib import Path
from cryptography.fernet import Fernet
import dropbox
from dropbox.oauth import DropboxOAuth2FlowNoRedirect

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

def setup_dropbox():
    
    APP_KEY = "YOUR_APP_KEY"
    APP_SECRET = "YOUR_APP_SECRET"

    auth_flow = DropboxOAuth2FlowNoRedirect(
        APP_KEY,
        APP_SECRET,
        token_access_type="offline"  # THIS IS THE KEY
    )

    authorize_url = auth_flow.start()
    print("1. Go to:", authorize_url)
    print("2. Click Allow")
    print("3. Copy the authorization code.")

    auth_code = input("Enter authorization code: ").strip()

    oauth_result = auth_flow.finish(auth_code)

    print("ACCESS TOKEN:", oauth_result.access_token)
    print("REFRESH TOKEN:", oauth_result.refresh_token)
