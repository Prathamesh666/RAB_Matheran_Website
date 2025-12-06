from dotenv import load_dotenv
import os, secrets
load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
SECRET_KEY = os.getenv("SECRET_KEY", secrets.token_hex(32))

SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASS = os.getenv("SMTP_PASS")

SENDER_API_KEY = os.getenv("SENDER_API_KEY")

TWILIO_SID = os.getenv("TWILIO_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_PHONE = os.getenv("TWILIO_PHONE")

ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL")
ADMIN_PHONE = os.getenv("ADMIN_PHONE")

SERVER_NAME = os.getenv("SERVER_NAME", "ranchoddasbhavan.com")
PREFERRED_URL_SCHEME = os.getenv("PREFERRED_URL_SCHEME", "https")
