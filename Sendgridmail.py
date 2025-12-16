import os
import requests
from dotenv import load_dotenv

load_dotenv()

def send_feedback_email(name, recipient_email):
    try:
        # Plain text content
        plain_text = (
            f"Dear {name},\n\n"
            f"Thank you for your feedback.\n\n"
            f"Your thoughts help us improve our hospitality.\n"
            f"📍 Location: Before Union Bank & Local Market, Matheran Hill Station\n"
            f"🌐 Website: https://ranchoddasarogyabhavanmatheran.onrender.com"
        )

        # HTML content
        html_body = f"""
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
                <img src="static/images/icons/RAG_Logo.png" 
                    alt="Ranchoddas Arogya Bhavan Logo" />
            </div>
            <h2>Thank you for your feedback</h2>
            <p>Your thoughts help us improve our hospitality.</p>
            <p>📍 Location: Before Union Bank & Local Market, Matheran Hill Station<br>
                🌐 Website: <a href="https://ranchoddasarogyabhavanmatheran.onrender.com">www.ranchoddasarogyabhavanmatheran.onrender.com</a></p>
        </div>
        </body>
        </html>
        """

        # Load Sender.net API key
        api_key = os.getenv("SENDER_API_KEY")
        if not api_key:
            raise ValueError("SENDER_API_KEY not found in environment variables")

        # Sender.net API endpoint
        url = "https://api.sender.net/v2/email"

        # Prepare payload
        payload = {
            "from": {
                "email": "p397366@gmail.com",  # must be verified in Sender.net
                "name": "Shri Ranchoddas Hindu Arogya Bhavan"
            },
            "to": [
                {"email": recipient_email, "name": name}
            ],
            "subject": "Feedback Response - Shri Ranchoddas Hindu Arogya Bhavan",
            "text": plain_text,
            "html": html_body
        }

        # Send request
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        response = requests.post(url, json=payload, headers=headers)

        if response.status_code in (200, 202):
            print("Email sent successfully")
        else:
            print(f"Failed to send email: {response.status_code} - {response.text}")

    except Exception as e:
        print(f"Error: {e}")

# Example call
send_feedback_email("Pratham", "prathamesh.b220104546@kccollege.edu.in")