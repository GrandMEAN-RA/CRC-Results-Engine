
from twilio.rest import Client
from dotenv import load_dotenv
from pathlib import Path
import os

# Load env ONCE
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")

missing = [
    name for name, value in {
        "TWILIO_ACCOUNT_SID": ACCOUNT_SID,
        "TWILIO_AUTH_TOKEN": AUTH_TOKEN,
    }.items() if not value
]

print("Looking for .env at:", BASE_DIR / ".env")
print("Exists:", (BASE_DIR / ".env").exists())

if missing:
    raise RuntimeError(f"Missing Twilio env vars: {', '.join(missing)}")

client = Client(ACCOUNT_SID, AUTH_TOKEN)

def send_whatsapp(student_name, phone, message):

    msg = client.messages.create(
    from_="whatsapp:+14155238886",
    to=f"whatsapp:{phone}",
    body=message
    )

    print(f"Sending Results document for {student_name.replace('_',"")} to WhatsApp number +{phone}")

    print("Twilio SID:", msg.sid)
    print("Status:", msg.status)
    
    return msg.sid
