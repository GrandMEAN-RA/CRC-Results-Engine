
from dropbox_service import get_dropbox_client

dbx = get_dropbox_client()
print(dbx.users_get_current_account().name.display_name)
