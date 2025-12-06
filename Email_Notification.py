import os, config
from flask import config, url_for
import requests
import base64
import smtplib
from email.message import EmailMessage

def send_notification(notification_type, booking_id=None, name=None, phone=None, email=None,
                    check_in=None, check_out=None, guests=None, note=None, message=None, to_email=None):
    """
    Unified notification sender using Sender API.
    Supports:
    - admin_alert
    - customer_alert (booking created)
    - guest_confirmation
    - booking_acceptance
    - booking_rejection
    - booking_pending
    - feedback_response
    - contact_form_alert
    """

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
            f"Dear Admin, you have a new booking that has been created.\n\n"
            f"Booking ID: {booking_id}\nName: {name}\nPhone: {phone}\nEmail: {email}\n"
            f"Check-in: {check_in} → Check-out: {check_out}\nGuests: {guests}\nNote: {note}"
        ),
        "customer_alert": (
            f"Dear {name},\n\nYour booking (ID: {booking_id}) is generated in the system and is currently pending acceptance "
            f"for {check_in} to {check_out}.\n\nKindly wait for further confirmation mail.\n\n"
            f"Thanks for your cooperation.\n\nRegards,\nShri Ranchoddas Hindu Arogya Bhavan\nMatheran Hill Station"
        ),
        "guest_confirmation": (
            f"Dear {name},\n\nYour booking (ID: {booking_id}) has been accepted "
            f"for Check-In: {check_in} to Check-Out: {check_out}.\n\n"
            f"We hope you find our Guest House comfortable and pleasant.\n\n"
            f"Regards,\nShri Ranchoddas Hindu Arogya Bhavan\nMatheran Hill Station"
        ),
        "booking_acceptance": f"Dear {name},\n\nYour booking (ID: {booking_id}) has been accepted for {check_in} → {check_out}.\nWe look forward to hosting you!",
        "booking_rejection": f"Dear {name},\n\nWe regret to inform you that your booking (ID: {booking_id}) has been rejected for {check_in} → {check_out}.",
        "booking_pending": (f"Dear {name},\n\nYour booking (ID: {booking_id}) is regenerated in the system and is currently pending acceptance "
            f"for {check_in} to {check_out}.\n\nKindly wait for further confirmation mail.\n\n"
            f"Thanks for your cooperation.\n\nRegards,\nShri Ranchoddas Hindu Arogya Bhavan\nMatheran Hill Station"),
        "feedback_response": f"Dear {name},\n\nThank you for your feedback.\nYour thoughts help us improve our hospitality.\n📍 Location: Matheran Hill Station\n🌐 Website: www.ranchoddasbhavan.com",
        "contact_form_alert": f"New contact form submission from {name} ({email}):\n\n{message}"
    }
    
    booking_url = url_for('reply_generic', reply_type='booking', guest_email=email, _external=True)
    feedback_url = url_for('reply_generic', reply_type='feedback', guest_email=email, _external=True)
    location_url = url_for('reply_generic', reply_type='location', guest_email=email, _external=True)

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

    logo_path = "static/images/icons/RAG_Logo.png"
    logo_data = None
    if os.path.exists(logo_path):
        with open(logo_path, "rb") as img:
            logo_data = base64.b64encode(img.read()).decode()
            
    if sender_key := os.getenv("SENDER_API_KEY"):
        # --- Production: Sender API ---
        payload = {
            "from": {"email": os.getenv("ADMIN_EMAIL"), "name": "Ranchoddas Bhavan"},
            "to": [{"email": to_email or email or os.getenv("ADMIN_EMAIL")}],
            "subject": subject,
            "html": html_body,
            "text": plain_body
        }
        if logo_data:
            payload["attachments"] = [{
                "content": logo_data,
                "type": "image/png",
                "filename": "RAG_Logo.png",
                "disposition": "inline",
                "cid": "RAG_Logo"
            }]
        try:
            response = requests.post(
                "https://api.sender.net/v2/email",
                headers={
                    "Authorization": f"Bearer {sender_key}",
                    "Content-Type": "application/json"
                },
                json=payload
            )
            if response.status_code in (200, 202):
                print(f"✅ {notification_type} email sent via Sender API")
            else:
                print("❌ Failed via Sender:", response.status_code, response.text)
        except Exception as e:
            print("❌ Exception via Sender:", e)

    else:
        # --- Local: SMTP ---
        try:
            msg = EmailMessage()
            msg["Subject"] = subject
            msg["From"] = os.getenv("SMTP_USER")
            msg["To"] = to_email or email or os.getenv("ADMIN_EMAIL")
            msg.set_content(plain_body)
            msg.add_alternative(html_body, subtype="html")

            if logo_data:
                msg.get_payload()[1].add_related( # type: ignore
                    base64.b64decode(logo_data), maintype="image", subtype="png", cid="RAG_Logo"
                )

            # Attach logo image inline
                with open("static/images/icons/RAG_Logo.png", "rb") as img:
                    msg.get_payload()[1].add_related(img.read(), maintype="image", subtype="png", cid="RAG_Logo") # type: ignore

            # Send email    
            with smtplib.SMTP(config.SMTP_HOST, config.SMTP_PORT) as server: # type: ignore
                    server.starttls()
                    if config.SMTP_USER is not None and config.SMTP_PASS is not None:  # type: ignore
                        server.login(config.SMTP_USER, config.SMTP_PASS) # type: ignore 
                    server.send_message(msg)
            server.send_message(msg)
            print(f"✅ {notification_type} email sent via SMTP")
        except Exception as e:
            print("❌ Failed via SMTP:", e)