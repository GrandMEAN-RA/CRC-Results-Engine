
import json
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path
from key_generator import load_fernet_key
from cryptography.fernet import Fernet
from audit_logger import log_event
import uuid
import hashlib

def get_machine_fingerprint():
    """
    Generates a stable machine fingerprint (offline-safe).
    """
    mac = uuid.getnode()
    raw = f"CRC-{mac}"
    return hashlib.sha256(raw.encode()).hexdigest()

def create_license(fernet, BASE_PATH: path):
    today = date.today()
    lic_per = 1
    _exp = today + relativedelta(months = lic_per)
    print("creating license!!!")
    
    license_data = {
        "licensed_by": "GrandMEAN Technologies",
        "licensed_to": "GrandMEAN Research & Analytics",
        "short_name": "GrandMEAN-RA",
        "product": "Docs Engine – Document Processing Engine",
        "issued_date": datetime.now().strftime('%Y-%m-%d'),
        "license_period": f"{lic_per}-month" if lic_per == 1 else f'{lic_per}-months', # ✅ 1 MONTH
        "expiry_date": _exp.strftime("%Y-%m-%d"),   
        "grace_notice_days": 30,
        "machine_id": get_machine_fingerprint(),
        "branding": {
        "primary_color": "#0A3D62",
        "footer_text": "Powered by GrandMEAN Technologies © 2025"
      }
    }

    license_data['raw_id'] = f"{license_data['short_name']}-{license_data['machine_id']}"
    print('licence created: ', license_data)
    eula = (f"Docs Engine– Document Processing Engine. \n"
            "Licensed exclusively to: {license_data['licensed to']}. \n\n"
            "This software is licensed for internal institutional use only."
            "Reverse engineering, redistribution, or resale is prohibited. \n\n"
            "Upon license expiration, functionality is limited.")
    
    encrypted = fernet.encrypt(
        json.dumps(license_data).encode("utf-8")
    )

    eula_file = BASE_PATH / "EULA.txt"
    eula_file.write_text(eula, encoding="utf-8")

    license_file = BASE_PATH / "license.lic"
    license_file.write_bytes(encrypted)

    print("✅ License & EULA generated successfully")

    return license_file

def license_exists(BASE_PATH: path) -> bool:
    return (BASE_PATH / "license.lic").exists()

def bootstrap_license(BASE_PATH: path):
    key = load_fernet_key(BASE_PATH)
    fernet = Fernet(key)

    if not license_exists(BASE_PATH):
        INSTALL_MARKER = BASE_PATH / ".installed"
        if not INSTALL_MARKER.exists():
            create_license(fernet, BASE_PATH)
            INSTALL_MARKER.touch()
    else:
        pass
    return fernet

def load_license(fernet, BASE_PATH: path):
    if not license_exists(BASE_PATH):
        print('license not found: ',lic_exists)
        return {"not_found": True, "days_left": 0} # trigger auto-creation
    
    try:
        license_file = BASE_PATH / "license.lic"
        decrypted = fernet.decrypt(license_file.read_bytes())
        print('license found')
        return json.loads(decrypted.decode())
    except Exception:
        log_event(event="LICENSE", detail="License corrupted or tampered", base_path=BASE_PATH)
        return {"not_found": True, "days_left": 0} # corrupted or tampered

def check_license(fernet, BASE_PATH: path):
    _license = load_license(fernet, BASE_PATH)
    print('lic: ',_license)
    today = datetime.now().date()
    print('valid license: ',_license)
    if not _license and _license.get("not_found", True):
        print("i'm here!!!")
        return {"not_found": True, "days_left": 0}

    if _license.get("machine_id") != get_machine_fingerprint():
        log_event(event="LICENSE", detail="Machine mismatch", base_path=BASE_PATH)
        print('mismatched')
        return {"expired": True, "days_left": 0}

    expiry = datetime.strptime(_license["expiry_date"], "%Y-%m-%d").date()
    days_left = (expiry - today).days
    print('returning payload')
    return {
        "license_to": _license.get("licensed_to"),
        "expired": days_left < 0,
        "days_left": max(days_left, 0),
        "notice_days": _license.get("grace_notice_days", 30)
    }

def show_expiry_warning(days_left):
    messagebox.showwarning(
        "License Expiry Warning",
        f"This Docs Engine license will expire in {days_left} day(s).\n\n"
        "Please contact the developer for renewal."
    )

def ensure_license(fernet, BASE_PATH: path):
    status = check_license(fernet, BASE_PATH)
    if status.get("expired"):
        show_expiry_warning(status["days_left"])
        #restrict_features()
    if status.get("machine_mismatch"):
        raise RuntimeError("License machine mismatch")
    return status

RENEWAL_FILE = "doc_engine_renewal.lic"

def apply_license_renewal(fernet, BASE_PATH: Path):
    #today = datetime.now().date()
    renewal_path = BASE_PATH / RENEWAL_FILE
    if not renewal_path.exists():
        log_event(event="LICENSE_RENEWAL", detail="License renewal failed", base_path=BASE_PATH)
        return False

    _license = load_license(fernet, BASE_PATH)
    if not _license or _license.get("not_found", True):
        return False

    try:
        renewal_data = json.loads(
            fernet.decrypt(renewal_path.read_bytes()).decode()
        )

        _license["expiry_date"] = renewal_data["expiry_date"]
        _license["issued_date"] = datetime.now().strftime("%Y-%m-%d")
        
        encrypted = fernet.encrypt(json.dumps(_license).encode())
        _license.write_bytes(encrypted)

        renewal_path.unlink()
        log_event(event="LICENSE_RENEWAL", detail="License renewed successfully", base_path=BASE_PATH)
        return True

    except Exception:
        log_event(event="LICENSE_RENEWAL", detail="Renewal failed", base_path=BASE_PATH)
        return False

def get_branding(fernet, BASE_PATH: Path):
    _license = load_license(fernet, BASE_PATH)

    if not _license or _license.get("not_found", True):
        return {
            "school_name": "Docs Engine",
            "short_name": "Docs Engine",
            "footer_text": "Powered by GrandMEAN Technologies © 2025",
            "primary_color": "#000000",
        }

    branding = _license.get("branding", {})

    return {
        "school_name": _license.get("licensed_to", "Docs Engine"),
        "short_name": _license.get("short_name", "Docs Engine"),
        "footer_text": branding.get("footer_text", ""),
        "primary_color": branding.get("primary_color", "#000000"),
    }


    

