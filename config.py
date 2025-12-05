import os
import secrets

# Replace with environment variables in production
MONGO_URI = os.environ.get("MONGO_URI", "mongodb+srv://PrathameshBhurke:Prathameshbhurke666@cluster0.ozajm.mongodb.net/hotel_db?retryWrites=true&w=majority&appName=Cluster0")
SECRET_KEY = os.environ.get("SECRET_KEY", secrets.token_hex(16))

# SMTP optional settings for booking confirmation
SMTP_HOST = os.environ.get("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.environ.get("SMTP_PORT", "587"))
SMTP_USER = os.environ.get("SMTP_USER", "p397366@gmail.com")
SMTP_PASS = os.environ.get("SMTP_PASS", "abqh znwb ocgu qotn")

#Twilio optional settings for SMS notifications
TWILIO_SID = os.environ.get("TWILIO_SID", "ACb5b86c7b344d1e068224ccd8621eb798")
TWILIO_AUTH_TOKEN = os.environ.get("TWILIO_AUTH_TOKEN", "31e6a407e10f8ec68895c6e018357239")
TWILIO_PHONE = os.environ.get("TWILIO_PHONE", "+19302075295")

# Admin initial username (create via create_admin.py instead)
ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME", "admin")
ADMIN_EMAIL = os.environ.get("ADMIN_EMAIL", "prathameshbhurke666@gmail.com")
ADMIN_PHONE = os.environ.get("ADMIN_PHONE", "+918433965801")

#URL settings
SERVER_NAME = "ranchoddasbhavan.com"   # or your deployed domain
PREFERRED_URL_SCHEME = "https"         # ensures https links