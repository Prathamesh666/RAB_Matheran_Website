import os
import base64
from Google import Create_Service, convert_to_RFC_datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from flask import url_for
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import pickle

SCOPES = ['https://mail.google.com/']

def send_via_gmail(notification_type, subject, plain_body, html_body, to_email):
    # Configuration
    CLIENT_SECRET_FILE = 'credentials_web.json'
    API_NAME = 'gmail'
    API_VERSION = 'v1'
    SCOPES = ['https://mail.google.com/']
    
    # Create Gmail API service
    service = Create_Service(CLIENT_SECRET_FILE, API_NAME, API_VERSION, SCOPES)
    #service = get_gmail_service()
    
    results = service.users().settings().sendAs().list(userId="me").execute()
    for alias in results.get("sendAs", []):
        print(alias["sendAsEmail"], alias.get("isPrimary"))

    # Create MIME message
    message = MIMEMultipart("related")
    message["To"] = to_email
    message["From"] = "p397366@gmail.com"
    message["Subject"] = subject

    # Alternative plain + HTML
    alt_part = MIMEMultipart("alternative")
    alt_part.attach(MIMEText(plain_body, "plain"))
    alt_part.attach(MIMEText(html_body, "html"))
    message.attach(alt_part)

    # Attach logo inline
    logo_path = "static/images/icons/RAG_Logo.png"
    if os.path.exists(logo_path):
        with open(logo_path, "rb") as img:
            logo = MIMEImage(img.read(), name="RAG_Logo.png")
            logo.add_header("Content-ID", "<RAG_Logo>")
            logo.add_header("Content-Disposition", "inline", filename="RAG_Logo.png")
            message.attach(logo)

    # Encode message
    raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()

    try:
        sent = service.users().messages().send(
            userId="me", body={"raw": raw_message}
        ).execute()
        print(f"✅ {notification_type} email sent via Gmail API, ID: {sent['id']}")
    except Exception as e:
        import traceback
        print("❌ Failed via Gmail API:", traceback.format_exc())
        
def send_notification(notification_type, booking_id=None, name=None, phone=None, email=None,
                      check_in=None, check_out=None, guests=None, note=None, message=None, to_email=None):

    # --- Subject and Body Maps ---
    subject_map = {
        "admin_alert": f"New Booking Alert From Shri Ranchoddas Hindu Arogya Bhavan - ID {booking_id}",
        "customer_alert": "Booking Created - Shri Ranchoddas Hindu Arogya Bhavan",
        "guest_confirmation": "Booking Confirmation - Shri Ranchoddas Hindu Arogya Bhavan",
        "booking_acceptance": "Booking Accepted - Shri Ranchoddas Hindu Arogya Bhavan",
        "booking_rejection": "Booking Update - Shri Ranchoddas Hindu Arogya Bhavan",
        "booking_pending": "Booking Pending - Shri Ranchoddas Hindu Arogya Bhavan",
        "feedback_response": "Feedback Response - Shri Ranchoddas Hindu Arogya Bhavan",
        "contact_form_alert": f"New Contact Form Submission from {name}"
    }

    plain_body_map = {
        "admin_alert": (
            f"Dear Admin, you have a new booking.\n\n"
            f"Booking ID: {booking_id}\nName: {name}\nPhone: {phone}\nEmail: {email}\n"
            f"Check-in: {check_in} → Check-out: {check_out}\nGuests: {guests}\nNote: {note}"
        ),
        "customer_alert": (
            f"Dear {name},\n\nYour booking (ID: {booking_id}) is generated and pending acceptance "
            f"for {check_in} to {check_out}.\n\nPlease wait for confirmation.\n\nRegards,\nShri Ranchoddas Hindu Arogya Bhavan"
        ),
        "guest_confirmation": (
            f"Dear {name},\n\nYour booking (ID: {booking_id}) has been accepted "
            f"for Check-In: {check_in} to Check-Out: {check_out}.\n\nWe look forward to hosting you!"
        ),
        "booking_acceptance": f"Dear {name},\n\nYour booking (ID: {booking_id}) has been accepted for {check_in} → {check_out}.",
        "booking_rejection": f"Dear {name},\n\nWe regret to inform you that your booking (ID: {booking_id}) was rejected.",
        "booking_pending": f"Dear {name},\n\nYour booking (ID: {booking_id}) is pending acceptance for {check_in} to {check_out}.",
        "feedback_response": f"Dear {name},\n\nThank you for your feedback.\n📍 Matheran Hill Station\n🌐 www.ranchoddasbhavan.com",
        "contact_form_alert": f"New contact form submission from {name} ({email}):\n\n{message}"
    }

    #booking_url = url_for('reply_generic', reply_type='booking', guest_email=email or to_email, _external=True)
    #feedback_url = url_for('reply_generic', reply_type='feedback', guest_email=email or to_email, _external=True)
    #location_url = url_for('reply_generic', reply_type='location', guest_email=email or to_email, _external=True)
    base_url = os.getenv("APP_BASE_URL", "https://ranchoddasarogyabhavanmatheran.onrender.com")
    booking_url = f"{base_url}/reply/booking/{email or to_email}"
    feedback_url = f"{base_url}/reply/feedback/{email or to_email}"
    location_url = f"{base_url}/reply/location/{email or to_email}"

    # Simplified HTML templates (you can reuse your styled versions)
    html_body_map = {
        "admin_alert": f"""
                <html>
                <head>
                    <style>
                        body {{ font-family: Arial, sans-serif; background-color: #f9f9f9; padding: 20px; color: #333; }}
                        .card {{ background: #fff; border-radius: 8px; padding: 20px; box-shadow: 0 2px 6px rgba(0,0,0,0.1); }}
                        .logo {{ text-align: center; margin-bottom: 20px; }}
                        .logo img {{ max-width: 180px; height: auto; border-radius: 8px; }}
                        h2 {{ color: #0b8a61; }}
                    </style>
                </head>
                <body>
                <div class="card">
                    <div class="logo">
                    <img src="cid:RAG_Logo" alt="Ranchoddas Arogya Bhavan Logo" />
                    </div>
                    <h2>New Booking Created</h2>
                    <p>A new booking has been created.</p>
                    <p><strong>Booking ID:</strong> { booking_id }</p>
                    <p><strong>Name:</strong> { name }</p>
                    <p><strong>Phone:</strong> { phone }</p>
                    <p><strong>Email:</strong> { email }</p>
                    <p><strong>Check-in:</strong> { check_in } → <strong>Check-out:</strong> { check_out }</p>
                    <p><strong>Guests:</strong> { guests }</p>
                    <p><strong>Note:</strong> { note }</p>
                    <p>Please check the bookings list on the website to update the status.</p>
                </div>
                </body>
                </html>
                """,
        "customer_alert": f"""
                    <html>
                    <head>
                    <style>
                        body {{ font-family: Arial, sans-serif; background-color: #f9f9f9; padding: 20px; color: #333; }}
                        .card {{ background: #fff; border-radius: 8px; padding: 20px; box-shadow: 0 2px 6px rgba(0,0,0,0.1); }}
                        .logo {{ text-align: center; margin-bottom: 20px; }}
                        .logo img {{ max-width: 180px; height: auto; border-radius: 8px; }}
                        h2 {{ color: #0b8a61; }}
                    </style>
                    </head>
                    <body>
                    <div class="card">
                        <div class="logo">
                        <img src="cid:RAG_Logo" alt="Ranchoddas Arogya Bhavan Logo" />
                        </div>
                        <p>Dear { name },</p>
                        <p>Your booking (ID: { booking_id }) is generated in the system and is currently pending acceptance
                        for Check-In: { check_in } to Check-Out: { check_out } at Shri Ranchoddas Hindu Arogya Bhavan Guest House.
                        </p>
                        <p>Kindly wait for further confirmation mail.</p>
                        <p>Thanks for your cooperation.</p>
                        <p>Regards,<br>Shri Ranchoddas Hindu Arogya Bhavan<br>From Matheran Hill Station</p>
                    </div>
                    </body>
                    </html>
                    """,
        "guest_confirmation": f"""
            <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; background-color: #f9f9f9; padding: 20px; color: #333; }}
                    .card {{ background: #fff; border-radius: 8px; padding: 20px; box-shadow: 0 2px 6px rgba(0,0,0,0.1); }}
                    .logo {{ text-align: center; margin-bottom: 20px; }}
                    .logo img {{ max-width: 180px; height: auto; border-radius: 8px; }}
                    h2 {{ color: #0b8a61; }}
                </style>
            </head>
                <body>
                <div class="card">
                    <div class="logo">
                    <img src="cid:RAG_Logo" alt="Ranchoddas Arogya Bhavan Logo" />
                    </div>
                    <p>Dear {name},</p>
                    <p>We like to inform you that your booking (ID: {booking_id}) has been accepted 
                    for Check-In: {check_in} to Check-Out: {check_out} .<br>
                    We Hope you find our Guest House comfortable and pleasant.</p>
                    <p>Please <a href="https://ranchoddasbhavan.com/contact">contact us</a> to know the reason or check further availability.</p>
                    <p>Regards,<br>Shri Ranchoddas Hindu Arogya Bhavan<br>Matheran Hill Station</p>
                </div>
                </body>
            </html>
            """,
        "booking_acceptance": f"<html><body><h2>Booking Accepted</h2><p>Dear {name}, your booking (ID {booking_id}) has been accepted.</p></body></html>",
        "booking_rejection": f"""
            <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; background-color: #f9f9f9; padding: 20px; color: #333; }}
                    .card {{ background: #fff; border-radius: 8px; padding: 20px; box-shadow: 0 2px 6px rgba(0,0,0,0.1); }}
                    .logo {{ text-align: center; margin-bottom: 20px; }}
                    .logo img {{ max-width: 180px; height: auto; border-radius: 8px; }}
                    h2 {{ color: #0b8a61; }}
                </style>
            </head>
                <body>
                <div class="card">
                    <div class="logo">
                    <img src="cid:RAG_Logo" alt="Ranchoddas Arogya Bhavan Logo" />
                    </div>
                    <p>Dear {name},</p>
                    <p>We regret to inform you that your booking (ID: {booking_id}) has been rejected
                    for Check-In: {check_in} to Check-Out: {check_out} due to certain reasons.</p>
                    <p>Please <a href="https://ranchoddasbhavan.com/contact">contact us</a> to know the reason or check further availability.</p>
                    <p>Regards,<br>Shri Ranchoddas Hindu Arogya Bhavan<br>Matheran Hill Station</p>
                </div>
                </body>
            </html>
            """,
        "booking_pending": f"""
                    <html>
                    <head>
                    <style>
                        body {{ font-family: Arial, sans-serif; background-color: #f9f9f9; padding: 20px; color: #333; }}
                        .card {{ background: #fff; border-radius: 8px; padding: 20px; box-shadow: 0 2px 6px rgba(0,0,0,0.1); }}
                        .logo {{ text-align: center; margin-bottom: 20px; }}
                        .logo img {{ max-width: 180px; height: auto; border-radius: 8px; }}
                        h2 {{ color: #0b8a61; }}
                    </style>
                    </head>
                    <body>
                    <div class="card">
                        <div class="logo">
                        <img src="cid:RAG_Logo" alt="Ranchoddas Arogya Bhavan Logo" />
                        </div>
                        <p>Dear { name },</p>
                        <p>Your booking (ID: { booking_id }) is regenerated in the system and is currently pending acceptance
                        for Check-In: { check_in } to Check-Out: { check_out } at Shri Ranchoddas Hindu Arogya Bhavan Guest House.
                        </p>
                        <p>Kindly wait for further confirmation mail.</p>
                        <p>Thanks for your cooperation.</p>
                        <p>Regards,<br>Shri Ranchoddas Hindu Arogya Bhavan<br>From Matheran Hill Station</p>
                    </div>
                    </body>
                    </html>
                    """,
        "feedback_response": f"""
                <html>
                <head>
                    <style>
                        body {{ font-family: Arial, sans-serif; background-color: #f9f9f9; padding: 20px; color: #333; }}
                        .card {{ background: #fff; border-radius: 8px; padding: 20px; box-shadow: 0 2px 6px rgba(0,0,0,0.1); }}
                        .logo {{ text-align: center; margin-bottom: 20px; }}
                        .logo img {{ max-width: 180px; height: auto; border-radius: 8px; }}
                        h2 {{ color: #0b8a61; }}
                    </style>
                </head>
                <body>
                <div class="card">
                <div class="logo">
                <img src="cid:RAG_Logo" alt="Ranchoddas Arogya Bhavan Logo" />
                </div>
                    <h2>Thank you for your feedback</h2>
                    <p>Your thoughts help us improve our hospitality.</p>
                    <p>📍 Location: Before Union Bank & Local Market, Matheran Hill Station<br>
                        🌐 Website: <a href="https://www.ranchoddasbhavan.com">www.ranchoddasbhavan.com</a></p>
                </div>
                </body>
                </html>
                """,
        "contact_form_alert": f"""
                <html>
                    <head>
                    <style>
                        body {{ font-family: Arial, sans-serif; background-color: #f9f9f9; padding: 20px; color: #333; }}
                        .card {{ background: #fff; border-radius: 8px; padding: 20px; box-shadow: 0 2px 6px rgba(0,0,0,0.1); }}
                        .logo {{ text-align: center; margin-bottom: 20px; }}
                        .logo img {{ max-width: 180px; height: auto; border-radius: 8px; }}
                        h2 {{ color: #0b8a61; }}
                        .btn {{ display: inline-block; margin: 8px 4px; padding: 10px 16px; border-radius: 6px; 
                        text-decoration: none; font-weight: bold; color: #fff; }}
                        .btn-booking {{ background-color: #0b8a61; }}
                        .btn-feedback {{ background-color: #007bff; }}
                        .btn-location {{ background-color: #6c757d; }}
                    </style>
                    </head>
                    <body>
                    <div class="card">
                        <div class="logo">
                        <img src="cid:RAG_Logo" alt="Ranchoddas Arogya Bhavan Logo" />
                        </div>
                        <h2>New Contact Form Submission</h2>
                        <p><strong>Name:</strong> {name}<br>
                        <strong>Email:</strong> {email}<br>
                        <strong>Message:</strong> {message}</p> 
                        <p>Quick reply options:</p>
                        <a href="{booking_url}" class="btn btn-booking">Reply about Booking</a>
                        <a href="{feedback_url}" class="btn btn-feedback">Reply about Feedback</a>
                        <a href="{location_url}" class="btn btn-location">Send Location Info</a>
                        </div>
                    </body>
                </html>
                """,
        }

    subject = subject_map[notification_type]
    plain_body = plain_body_map[notification_type]
    html_body = html_body_map[notification_type]

    # --- Send via Gmail API ---
    send_via_gmail(notification_type, subject, plain_body, html_body, to_email or email or os.getenv("ADMIN_EMAIL"))
    
send_notification(
    notification_type="feedback_response",
    name="Test User",
    to_email='prathameshbhurke666@gmail.com'
)