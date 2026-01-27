
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

if missing:
    raise RuntimeError(f"Missing Twilio env vars: {', '.join(missing)}")

client = Client(ACCOUNT_SID, AUTH_TOKEN)

def send_whatsapp(phone, message):
    
    msg = client.messages.create(
    from_="whatsapp:+14155238886",
    to=f"whatsapp:{phone}",
    body=message
    )
    
    return msg.status

