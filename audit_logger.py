
from datetime import datetime
from cryptography.fernet import Fernet
import csv
from reportlab.platypus import SimpleDocTemplate, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from key_generator import load_fernet_key
from pathlib import Path

LOG_FILE = "audit.log"

def log_event(*, event, detail, base_path):
    base_path = Path(base_path)
    if not base_path.exists():
        raise RuntimeError(
            f"Invalid base_path passed to log_event(): {base_path}"
        )
    
    AUDIT_KEY = load_fernet_key(base_path)
    fernet = Fernet(AUDIT_KEY)
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entry = f"[{timestamp}] {event} | {detail}"

    encrypted = fernet.encrypt(entry.encode())

    with open(LOG_FILE, "ab") as f:
        f.write(encrypted + b"\n")

def read_audit_log(base_path: path):
    AUDIT_KEY = load_fernet_key(base_path)
    fernet = Fernet(AUDIT_KEY)
    
    entries = []
    with open(LOG_FILE, "rb") as f:
        for line in f:
            try:
                entries.append(fernet.decrypt(line.strip()).decode())
            except Exception:
                pass
    return entries

def export_audit_csv(base_path: path, filename="audit_report.csv"):
    rows = read_audit_log(base_path)

    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Timestamp", "Event", "Details"])

        for row in rows:
            ts, rest = row.split("] ", 1)
            event, detail = rest.split(" | ", 1)
            writer.writerow([ts.strip("["), event, detail])

def export_audit_pdf(base_path: path, filename="audit_report.pdf"):
    doc = SimpleDocTemplate(filename)
    styles = getSampleStyleSheet()
    content = []

    for line in read_audit_log(base_path):
        content.append(Paragraph(line, styles["Normal"]))

    doc.build(content)

