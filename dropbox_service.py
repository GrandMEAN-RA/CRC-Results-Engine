
from pathlib import Path
import dropbox
import os
import time
from tqdm import tqdm
import csv
from dropbox.exceptions import ApiError
from dotenv import load_dotenv

def get_dropbox_client():

    # Load environment variables
    BASE_DIR = Path(__file__).resolve().parent
    load_dotenv(BASE_DIR / ".env")

    APP_KEY = os.getenv("DROPBOX_APP_KEY")
    APP_SECRET = os.getenv("DROPBOX_APP_SECRET")
    REFRESH_TOKEN = os.getenv("DROPBOX_REFRESH_TOKEN")

    missing = [
        name for name, value in {
            "DROPBOX_APP_KEY": APP_KEY,
            "DROPBOX_APP_SECRET": APP_SECRET,
            "DROPBOX_REFRESH_TOKEN": REFRESH_TOKEN,
        }.items() if not value
    ]

    if missing:
        raise RuntimeError(f"Missing Dropbox env vars: {', '.join(missing)}")
        
    return dropbox.Dropbox(
        oauth2_refresh_token=REFRESH_TOKEN,
        app_key=APP_KEY,
        app_secret=APP_SECRET
    )

def ensure_folder_exists(dbx, dropbox_folder):
    try:
        dbx.files_get_metadata(dropbox_folder)
    except ApiError as e:
        if (
            e.error.is_path()
            and e.error.get_path().is_not_found()
        ):
            try:
                dbx.files_create_folder_v2(dropbox_folder)
                print(f"Created Dropbox folder: {dropbox_folder}")
            except ApiError as ce:
                # Folder may already exist due to race condition
                if not (
                    ce.error.is_path()
                    and ce.error.get_path().is_conflict()
                ):
                    raise
        else:
            raise


def get_or_create_shared_link(dbx, path):
    try:
        links = dbx.sharing_list_shared_links(path=path).links
        if links:
            return links[0].url
    except Exception:
        pass

    return dbx.sharing_create_shared_link_with_settings(path).url

def auto_uploader(output_dir, term, academic_session, sfa):

    LOCAL_FOLDER = output_dir
    DROPBOX_FOLDER = (f"/AutoUploads_{term}_{academic_session}" if not sfa else
                        f"/AutoUploads_{term}_{academic_session}_sfa")
        
    CHUNK_SIZE = 4 * 1024 * 1024  # 4MB

    # ---------------------------
    # CONNECT TO DROPBOX
    # ---------------------------
    dbx = get_dropbox_client()

    # Ensure folder exists
    ensure_folder_exists(dbx, DROPBOX_FOLDER)
    print("hereeeeee!")

    # ---------------------------
    # UPLOAD FILES
    # ---------------------------

    def upload_file(local_path, dropbox_path):
        file_size = os.path.getsize(local_path)

        with open(local_path, "rb") as f:
            if file_size <= CHUNK_SIZE:
                dbx.files_upload(
                    f.read(),
                    dropbox_path,
                    mode=dropbox.files.WriteMode.overwrite
                )
                return True

            upload_session = dbx.files_upload_session_start(
                f.read(CHUNK_SIZE)
            )

            cursor = dropbox.files.UploadSessionCursor(
                session_id=upload_session.session_id,
                offset=f.tell()
            )

            commit = dropbox.files.CommitInfo(
                path=dropbox_path,
                mode=dropbox.files.WriteMode.overwrite
            )

            with tqdm(
                total=file_size,
                initial=cursor.offset,
                unit="B",
                unit_scale=True,
                desc=os.path.basename(local_path)
            ) as pbar:
                while f.tell() < file_size:
                    remaining = file_size - f.tell()
                    chunk = f.read(min(CHUNK_SIZE, remaining))

                    if remaining <= CHUNK_SIZE:
                        dbx.files_upload_session_finish(
                            chunk, cursor, commit
                        )
                    else:
                        dbx.files_upload_session_append_v2(
                            chunk, cursor
                        )
                        cursor.offset = f.tell()

                    pbar.update(len(chunk))

        return True

    # ---------------------------
    # MAIN LOOP
    # ---------------------------

    uploaded_links = {}

    for filename in os.listdir(LOCAL_FOLDER):
        local_path = os.path.join(LOCAL_FOLDER, filename)

        if not os.path.isfile(local_path):
            continue

        modified_time = os.path.getmtime(local_path)
        dropbox_path = f"{DROPBOX_FOLDER}/{filename}"

        if time.time() - modified_time >= 86400:
            continue

        success = upload_file(local_path, dropbox_path)
        if not success:
            continue

        link = get_or_create_shared_link(dbx, dropbox_path)
        link = link.replace("&dl=0", "&dl=1")

        uploaded_links[filename] = link
        print(f"Uploaded + linked: {filename} | {link}")


        with open("dropbox_links.csv", "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["filename", "link"])
            writer.writerows([filename,link])

    return uploaded_links
    
