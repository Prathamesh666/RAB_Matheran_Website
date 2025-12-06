from flask import Flask, render_template, request, redirect, url_for, flash, abort, Response
from flask_pymongo import PyMongo
from bson.objectid import ObjectId
from datetime import datetime, timezone
import config, os
from werkzeug.security import check_password_hash
from flask_login import LoginManager, login_user, logout_user, login_required, UserMixin
import smtplib
from email.message import EmailMessage
from werkzeug.utils import secure_filename
import gridfs
from Email_Notification import *
import base64

app = Flask(__name__)
app.config["MONGO_URI"] = config.MONGO_URI # type: ignore
app.config["SECRET_KEY"] = config.SECRET_KEY # type: ignore

mongo = PyMongo(app)
db = mongo.db  # Ensure this line comes after app is fully configured

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login" # type: ignore

# Simple User class for Flask-Login
class AdminUser(UserMixin):
    def __init__(self, admin_doc):
        self.id = str(admin_doc["_id"])
        self.username = admin_doc["username"]

@login_manager.user_loader
def load_user(user_id):
    admin_doc = db.admins.find_one({"_id": ObjectId(user_id)}) # type: ignore
    if admin_doc:
        return AdminUser(admin_doc)
    return None

# List of gallery images (exact filenames)
GALLERY_CATEGORIES = {
    "entrances": {
        "title": "Entrances",
        "images": [
            "Entrance_1.0.jpeg",
            "Entrance_1.1.jpeg"
        ]
    },
    "hotel_view": {
        "title": "Hotel View",
        "images": [
            "Hotel_View_1.0.jpeg",
            "Hotel_View_1.1.jpeg",
            "Hotel_View_1.2.jpeg",
            "Hotel_View_2.0.jpeg",
            "Hotel_View_2.1.jpeg",
            "Hotel_View_2.2.jpeg",
            "Hotel_View_3.jpeg"
        ]
    },
    "outside": {
        "title": "Outside Views",
        "images": [
            "Outside_Hotel_Railway_Track.jpeg",
            "Outside_Road_Track_Before_Hotel.jpeg",
            "Welcome_To_Matheran.jpeg"
        ]
    },
    "signs": {
        "title": "Signboards",
        "images": [
            "Ranchoddas_Arogya_Bhavan.jpeg"
        ]
    }
}

@app.route("/")
def index():
    # Build combined list from entrances then hotel_view
    combined = []
    for key in ("entrances", "hotel_view", "signs"):
        imgs = GALLERY_CATEGORIES.get(key, {}).get("images", [])
        for im in imgs:
            if im not in combined:
                combined.append(im)
    # Limit to max 10
    carousel_images = combined[:10]
    return render_template("index.html", images=carousel_images, page_class="home-page")

@app.route("/about")
def about():
    return render_template("about.html")

PER_PAGE = 8  # images per page for category pages

@app.route("/gallery")
def gallery():
    cats = list(db.categories.find()) # type: ignore
    categories = []
    for c in cats:
        sample = c.get("images", [])[:3]
        categories.append({
            "key": c["key"],
            "title": c["title"],
            "sample": sample,
            "count": len(c.get("images", []))
        })
    return render_template("gallery.html", categories=categories)
    
@app.route("/gallery/<category>")
def gallery_category(category):
    meta = db.categories.find_one({"key": category}) # type: ignore
    if not meta:
        abort(404)
    page = int(request.args.get("page", 1))
    images = meta.get("images", [])
    total = len(images)
    pages = (total + PER_PAGE - 1) // PER_PAGE
    start = (page - 1) * PER_PAGE
    end = start + PER_PAGE
    page_images = images[start:end]
    return render_template("gallery_category.html", category=category, title=meta["title"], images=page_images, page=page, pages=pages, total=total)

# ------------------ ADMIN GALLERY EDIT ------------------
# Gallery & Feedback allowed extentions
ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'gif'}

def allowed_file(filename):
    ext_ok = '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
    print("Checking file:", filename, "Allowed:", ext_ok)
    return ext_ok

@app.route("/gallery/edit", methods=["GET", "POST"])
@login_required
def gallery_edit():
    if request.method == "POST":
        action = request.form.get("action")
        category_id = request.form.get("category_id")
        title = request.form.get("title")
        key = request.form.get("key")

        # Add category
        if action == "add_category":
            db.categories.insert_one({ # type: ignore
                "title": title,
                "key": key,
                "images": [],
                "created_at": datetime.now(timezone.utc)
            })
            flash("Category added.", "success")

        # Delete category
        elif action == "delete_category" and category_id:
            db.categories.delete_one({"_id": ObjectId(category_id)}) # pyright: ignore[reportOptionalMemberAccess]
            flash("Category deleted.", "info")

        # Add image (upload file)
        elif action == "add_image" and category_id and "file" in request.files:
            file = request.files["file"]
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename) # type: ignore
                
                db.categories.update_one( # type: ignore
                    {"_id": ObjectId(category_id)},
                    {"$push": {"images": filename}}
                )
                flash("Image uploaded and added.", "success")
            else:
                flash("Invalid file type.", "danger")

        # Delete image (remove from DB and filesystem)
        elif action == "delete_image" and category_id:
            filename = request.form.get("filename")
            db.categories.update_one( # type: ignore
                {"_id": ObjectId(category_id)},
                {"$pull": {"images": filename}}
            )
            flash("Image deleted.", "info")

        return redirect(url_for("gallery_edit"))

    cats = list(db.categories.find().sort("created_at", -1)) # type: ignore
    for c in cats:
        c["images"] = sorted(c.get("images", []))
    return render_template("gallery_edit.html", categories=cats)

# Booking create with validation and optional email confirmation
@app.route("/booking", methods=["GET", "POST"])
def booking():
    if request.method == "POST":
        name = request.form.get("name")
        phone = request.form.get("phone")
        email = request.form.get("email")
        check_in = request.form.get("check_in")
        check_out = request.form.get("check_out")
        guests = int(request.form.get("guests", 1))
        note = request.form.get("note", "")

        # Server-side validation
        if not check_in or not check_out:
            flash("Check-in and check-out dates are required.", "danger")
            return redirect(url_for("booking"))
        try:
            ci = datetime.strptime(check_in, "%Y-%m-%d").date()
            co = datetime.strptime(check_out, "%Y-%m-%d").date()
        except Exception:
            flash("Invalid dates provided.", "danger")
            return redirect(url_for("booking"))

        if ci >= co:
            flash("Check-out date must be after check-in date.", "danger")
            return redirect(url_for("booking"))

        booking_doc = {
            "name": name,
            "phone": phone,
            "email": email,
            "check_in": check_in,
            "check_out": check_out,
            "guests": guests,
            "note": note,
            "created_at": datetime.now(timezone.utc),
            "status": "Pending"
        }
        result = db.bookings.insert_one(booking_doc) # type: ignore
        booking_id = str(result.inserted_id)
        flash(f"Booking created successfully. Booking ID: {booking_id}", "success")
        
        # Optional email creation for guest
        def booking_pending(email, name, booking_id, check_in, check_out):
            subject = "Booking Created - Shri Ranchoddas Hindu Arogya Bhavan"
            plain_body = (
                f"Dear {name},\n\nYour booking (ID: {booking_id}) is generated in the system and is currently pending acceptance "
                f"for {check_in} to {check_out} at Shri Ranchoddas Hindu Arogya Bhavan Guest House.\n\n"
                f"Kindly wait for further confirmation mail.\n\nThanks for your cooperation\n\n"
                f"Regards,\nShri Ranchoddas Hindu Arogya Bhavan From Matheran Hill Station"
            )
        
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
                <img src="cid:RAG_Logo" alt="Ranchoddas Arogya Bhavan Logo" />
                </div>
                <p>Dear {name},</p>
                <p>Your booking (ID: {booking_id}) is generated in the system and is currently pending acceptance
                for Check-In: {check_in} to Check-Out: {check_out} at Shri Ranchoddas Hindu Arogya Bhavan Guest House.</p>
                <p>Kindly wait for further confirmation mail.</p>
                <p>Thanks for your cooperation.</p>
                <p>Regards,<br>Shri Ranchoddas Hindu Arogya Bhavan<br>From Matheran Hill Station</p>
            </div>
            </body>
            </html>
            """

            logo_path = "static/images/icons/RAG_Logo.png"
            logo_data = None
            if os.path.exists(logo_path):
                with open(logo_path, "rb") as img:
                    logo_data = base64.b64encode(img.read()).decode()

            sender_key = os.getenv("SENDER_API_KEY")

            if sender_key:
                # --- Production: Sender API ---
                payload = {
                    "from": {"email": os.getenv("ADMIN_EMAIL"), "name": "Ranchoddas Bhavan"},
                    "to": [{"email": email}],
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
                        print("✅ Booking pending email sent via Sender API")
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
                    msg["To"] = email
                    msg.set_content(plain_body)
                    msg.add_alternative(html_body, subtype="html")
        
                    if logo_data:
                        msg.get_payload()[1].add_related( # type: ignore
                            base64.b64decode(logo_data), maintype="image", subtype="png", cid="RAG_Logo"
                        )

                    with smtplib.SMTP(config.SMTP_HOST, config.SMTP_PORT) as server: # type: ignore
                        server.starttls()
                        if config.SMTP_USER is not None and config.SMTP_PASS is not None: # type: ignore
                            server.login(config.SMTP_USER, config.SMTP_PASS) # type: ignore
                            server.send_message(msg)
                    print("✅ Booking pending email sent via SMTP")
                except Exception as e:
                    print("❌ Failed via SMTP:", e)
                    
        booking_pending(email, name, booking_id, check_in, check_out)

        # 🔔 Notify admin by email
        if config.SMTP_HOST and getattr(config, "ADMIN_EMAIL", None): # type: ignore
            try:
                admin_msg = EmailMessage()
                admin_msg["Subject"] = f"New Booking Alert - ID {booking_id}"
                admin_msg["From"] = config.SMTP_USER # type: ignore
                admin_msg["To"] = config.ADMIN_EMAIL # type: ignore
                admin_msg.set_content(
                    f"A new booking has been created.\n\n"
                    f"Booking ID: {booking_id}\n"
                    f"Name: {name}\n"
                    f"Phone: {phone}\n"
                    f"Email: {email}\n"
                    f"Check-in: {check_in} → Check-out: {check_out}\n"
                    f"Guests: {guests}\n"
                    f"Note: {note}\n\n"
                    f"Please check the bookings list on the website to update the status."
                )
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
                """
                admin_msg.add_alternative(html_body, subtype="html")
                # Attach logo image inline
                with open("static/images/icons/RAG_Logo.png", "rb") as img:
                    admin_msg.get_payload()[1].add_related(img.read(), maintype="image", subtype="png", cid="RAG_Logo") # type: ignore
                    
                with smtplib.SMTP(config.SMTP_HOST, config.SMTP_PORT) as server: # type: ignore
                    server.starttls()
                    if config.SMTP_USER is not None and config.SMTP_PASS is not None: # type: ignore
                        server.login(config.SMTP_USER, config.SMTP_PASS) # type: ignore
                    server.send_message(admin_msg)
            except Exception:
                app.logger.exception("Failed to send admin notification email")

        # 📱 Optional: Notify admin by SMS (Twilio)
        if getattr(config, "TWILIO_SID", None) and getattr(config, "ADMIN_PHONE", None):
            try:
                from twilio.rest import Client
                client = Client(config.TWILIO_SID, config.TWILIO_AUTH_TOKEN) # type: ignore
                client.messages.create(
                    body=f"Dear Admin You Have A New Booking Alert.\n\n"
                    f"Booking ID: {booking_id}\n"
                    f"Name: {name}\n"
                    f"Phone: {phone}\n"
                    f"Email: {email}\n"
                    f"Check-in: {check_in} to Check-out: {check_out}\n"
                    f"Guests: {guests}\n"
                    f"Note: {note}\n\n"
                    f"Please check the bookings list on the website to update the status.",
                    from_=config.TWILIO_PHONE, # type: ignore
                    to=config.ADMIN_PHONE if config.ADMIN_PHONE is not None else "" # type: ignore
                )
            except Exception:
                app.logger.exception("Failed to send SMS notification")

        return redirect(url_for("bookings_list"))
    return render_template("booking.html")

# Bookings list protected for admin
@app.route("/bookings")
@login_required
def bookings_list():
    bookings = list(db.bookings.find().sort("created_at", 1)) # type: ignore
    return render_template("bookings_list.html", bookings=bookings)

@app.route("/booking/accept/<booking_id>", methods=["POST"])
@login_required
def booking_accept(booking_id):
    booking = db.bookings.find_one({"_id": ObjectId(booking_id)}) # type: ignore
    if not booking:
        abort(404)

    db.bookings.update_one({"_id": ObjectId(booking_id)}, {"$set": {"status": "Accepted"}}) # type: ignore
    flash("Booking accepted.", "success")

    # Send confirmation email only now
    email = booking.get("email")
    name = booking.get("name")
    check_in = booking.get("check_in")
    check_out = booking.get("check_out")
    booking_id = str(booking["_id"])
    
    # Booking Confirmation mail to guest
    if config.SMTP_HOST and email: # type: ignore
        try:
            msg = EmailMessage()
            msg["Subject"] = "Booking Confirmation - Shri Ranchoddas Hindu Arogya Bhavan"
            msg["From"] = config.SMTP_USER # type: ignore
            msg["To"] = email
            msg.set_content(
                f"Dear {name},\n\nYour booking (ID: {booking_id}) has been accepted "
                f"for Check-In: {check_in} to Check-Out: {check_out}.\n\n"
                f"We Hope you find our Guest House comfortable and pleasant.\n\n"
                f"Regards,\nShri Ranchoddas Hindu Arogya Bhavan\nMatheran Hill Station"
            )
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
            """
            msg.add_alternative(html_body, subtype="html")
            # Attach logo image inline
            with open("static/images/icons/RAG_Logo.png", "rb") as img:
                msg.get_payload()[1].add_related(img.read(), maintype="image", subtype="png", cid="RAG_Logo") # type: ignore
            
            with smtplib.SMTP(config.SMTP_HOST, config.SMTP_PORT) as server: # type: ignore
                server.starttls()
                if config.SMTP_USER is not None and config.SMTP_PASS is not None: # type: ignore
                            server.login(config.SMTP_USER, config.SMTP_PASS) # type: ignore
                server.send_message(msg)
        except Exception:
            app.logger.exception("Failed to send confirmation email")

    return redirect(url_for("bookings_list"))

@app.route("/booking/reject/<booking_id>", methods=["POST"])
@login_required
def booking_reject(booking_id):
    booking = db.bookings.find_one({"_id": ObjectId(booking_id)}) # type: ignore
    if not booking:
        abort(404)

    db.bookings.update_one({"_id": ObjectId(booking_id)}, {"$set": {"status": "Rejected"}}) # type: ignore
    flash("Booking rejected.", "danger")

    # Optional: notify customer of rejection
    email = booking.get("email")
    name = booking.get("name")
    check_in = booking.get("check_in")
    check_out = booking.get("check_out")
    booking_id = str(booking["_id"])
    
    # Booking Rejection mail to guests
    if config.SMTP_HOST and email: # type: ignore
        try:
            msg = EmailMessage()
            msg["Subject"] = "Booking Update - Shri Ranchoddas Hindu Arogya Bhavan"
            msg["From"] = config.SMTP_USER # type: ignore
            msg["To"] = email
            msg.set_content(
                f"Dear {name},\n\nWe regret to inform you that your booking (ID: {booking_id}) hs been rejected "
                f"for Check-In: {check_in} to Check-Out: {check_out} due to certain reasons "
                f"(Contact Us to know the reason or further availability from the website).\n\n"
                f"Regards,\nShri Ranchoddas Hindu Arogya Bhavan\nMatheran Hill Station"
            )
            # HTML body with inline logo
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
            """
            msg.add_alternative(html_body, subtype="html")
            # Attach logo image inline
            with open("static/images/icons/RAG_Logo.png", "rb") as img:
                msg.get_payload()[1].add_related(img.read(), maintype="image", subtype="png", cid="RAG_Logo") # type: ignore
                    
            with smtplib.SMTP(config.SMTP_HOST, config.SMTP_PORT) as server: # type: ignore
                server.starttls()
                if config.SMTP_USER is not None and config.SMTP_PASS is not None: # type: ignore
                    server.login(config.SMTP_USER, config.SMTP_PASS) # type: ignore
                server.send_message(msg)
        except Exception:
            app.logger.exception("Failed to send rejection email")

    return redirect(url_for("bookings_list"))

@app.route("/booking/edit/<booking_id>", methods=["GET", "POST"])
@login_required
def booking_edit(booking_id):
    booking = db.bookings.find_one({"_id": ObjectId(booking_id)}) # type: ignore
    if not booking:
        abort(404)
    if request.method == "POST":
        name = request.form.get("name")
        phone = request.form.get("phone")
        email = request.form.get("email")
        check_in = request.form.get("check_in")
        check_out = request.form.get("check_out")
        guests = int(request.form.get("guests", 1))
        status = request.form.get("status", "Pending")
        note = request.form.get("note", "")

        if not check_in or not check_out:
            flash("Check-in and check-out dates are required.", "danger")
            return redirect(url_for("booking_edit", booking_id=booking_id))
        try:
            ci = datetime.strptime(check_in, "%Y-%m-%d").date()
            co = datetime.strptime(check_out, "%Y-%m-%d").date()
        except Exception:
            flash("Invalid dates provided.", "danger")
            return redirect(url_for("booking_edit", booking_id=booking_id))

        if ci >= co:
            flash("Check-out date must be after check-in date.", "danger")
            return redirect(url_for("booking_edit", booking_id=booking_id))

        updated = {
            "name": name,
            "phone": phone,
            "email": email,
            "check_in": check_in,
            "check_out": check_out,
            "guests": guests,
            "status": status,
            "note": note
        }
        # Notify customer based on status
        if status.lower() == "accepted":
            booking_accept(booking_id)
        elif status.lower() == "rejected":
            booking_reject(booking_id)
        else:
            booking_pending(email, name, booking_id, check_in, check_out) # type: ignore
            
        flash("Booking updated successfully.", "success")
        return redirect(url_for("bookings_list"))
    return render_template("booking_edit.html", booking=booking)

@app.route("/booking/delete/<booking_id>", methods=["POST"])
@login_required
def booking_delete(booking_id):
    db.bookings.delete_one({"_id": ObjectId(booking_id)}) # type: ignore
    flash("Booking deleted.", "info")
    return redirect(url_for("bookings_list"))

#app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(__file__), 'static', 'images', 'feedback_gallery')
fs = gridfs.GridFS(db) # type: ignore

@app.route("/feedback", methods=["GET", "POST"])
def feedback():
    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        rating = int(request.form.get("rating", 0))
        comments = request.form.get("comments", "")

        if rating < 0 or rating > 10:
            flash("Rating must be between 0 and 10.", "danger")
            return redirect(url_for("feedback"))

        photo_ids = []
        if 'photos' in request.files:
            photos = request.files.getlist('photos')
            for photo in photos:
                if photo and allowed_file(photo.filename):
                    file_id = fs.put(photo, filename=secure_filename(photo.filename)) # type: ignore
                    photo_ids.append(str(file_id))

        db.feedbacks.insert_one({ # type: ignore
            "name": name,
            "rating": rating,
            "comments": comments,
            "photos": photo_ids,   # store GridFS IDs
            "created_at": datetime.now(timezone.utc)
        })
        
        # Notify Thanks email for the feedback to guests
        if config.SMTP_HOST and email: # type: ignore
            try:
                msg = EmailMessage()
                msg["Subject"] = "Feedback Response - Shri Ranchoddas Hindu Arogya Bhavan"
                msg["From"] = config.SMTP_USER # type: ignore
                msg["To"] = email
                msg.set_content(
                f"Dear {name},\n\nThank you for your feedback\n\n"
                f"Your thoughts help us improve our hospitality.\n"
                f"📍 Location: Before Union Bank & Local Market, Matheran Hill Station\n"
                f"🌐 Website: www.ranchoddasbhavan.com"
                )
                # HTML body with inline logo
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
                <img src="cid:RAG_Logo" alt="Ranchoddas Arogya Bhavan Logo" />
                </div>
                    <h2>Thank you for your feedback</h2>
                    <p>Your thoughts help us improve our hospitality.</p>
                    <p>📍 Location: Before Union Bank & Local Market, Matheran Hill Station<br>
                        🌐 Website: <a href="https://www.ranchoddasbhavan.com">www.ranchoddasbhavan.com</a></p>
                </div>
                </body>
                </html>
                """
                msg.add_alternative(html_body, subtype="html")
                # Attach logo image inline
                with open("static/images/icons/RAG_Logo.png", "rb") as img:
                    msg.get_payload()[1].add_related(img.read(), maintype="image", subtype="png", cid="RAG_Logo") # type: ignore
                    
                with smtplib.SMTP(config.SMTP_HOST, config.SMTP_PORT) as server: # type: ignore
                    server.starttls()
                    if config.SMTP_USER is not None and config.SMTP_PASS is not None: # type: ignore
                        server.login(config.SMTP_USER, config.SMTP_PASS) # type: ignore
                    server.send_message(msg)
            except Exception:
                app.logger.exception("Failed to send return feedback email")

        flash("Thank you for your feedback.", "success")
        return redirect(url_for("feedbacks_list"))

    return render_template("feedback.html")

# Route to stream photos from GridFS
@app.route("/feedback/photo/<file_id>")
def feedback_photo(file_id):
    try:
        file = fs.get(ObjectId(file_id))
    except Exception:
        abort(404)
    # Detect mimetype from filename if needed
    return Response(file.read(), mimetype="image/jpeg")

@app.route("/feedbacks")
@login_required
def feedbacks_list():
    feedbacks = list(db.feedbacks.find().sort("created_at", 1)) # type: ignore
    return render_template("feedbacks_list.html", feedbacks=feedbacks)

@app.route("/feedback/edit/<fb_id>", methods=["GET", "POST"])
@login_required
def feedback_edit(fb_id):
    fb = db.feedbacks.find_one({"_id": ObjectId(fb_id)}) # type: ignore
    if not fb:
        abort(404)

    if request.method == "POST":
        name = request.form.get("name")
        rating = int(request.form.get("rating", 0))
        comments = request.form.get("comments", "")

        photo_ids = fb.get("photos", [])

        if 'photos' in request.files:
            photos = request.files.getlist('photos')
            for photo in photos:
                if photo and allowed_file(photo.filename):
                    file_id = fs.put(photo, filename=secure_filename(photo.filename)) # type: ignore
                    photo_ids.append(str(file_id))

        db.feedbacks.update_one( # type: ignore
            {"_id": ObjectId(fb_id)},
            {"$set": {
                "name": name,
                "rating": rating,
                "comments": comments,
                "photos": photo_ids
            }}
        )

        flash("Feedback updated.", "success")
        return redirect(url_for("feedbacks_list"))

    return render_template("feedback_edit.html", fb=fb)

@app.route("/feedback/delete/<fb_id>", methods=["POST"])
@login_required
def feedback_delete(fb_id):
    db.feedbacks.delete_one({"_id": ObjectId(fb_id)}) # type: ignore
    flash("Feedback deleted.", "info")
    return redirect(url_for("feedbacks_list"))

@app.route("/contact", methods=["GET", "POST"])
def contact():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        message = request.form.get("message", "").strip()

        # Validation: all fields required
        if not name:
            flash("Name is required.", "danger")
            return redirect(url_for("contact"))
        if not email or "@" not in email:
            flash("A valid email address is required.", "danger")
            return redirect(url_for("contact"))
        if not message:
            flash("Message cannot be empty.", "danger")
            return redirect(url_for("contact"))

        # Save to MongoDB
        db.contacts.insert_one({ # type: ignore
            "name": name,
            "email": email,
            "message": message,
            "created_at": datetime.now(timezone.utc)
        })
        
        # 🔔 Contact form submittion alert Notify admin by email with logo and reply buttons
        if config.SMTP_HOST and getattr(config, "ADMIN_EMAIL", None): # type: ignore
            try:
                admin_msg = EmailMessage()
                admin_msg["Subject"] = f"New Contact Form Submission from {name}"
                admin_msg["From"] = config.SMTP_USER # type: ignore
                admin_msg["To"] = config.ADMIN_EMAIL # type: ignore
                admin_msg["Reply-To"] = email
                # Plain text fallback
                admin_msg.set_content(f"New contact form submission from {name} ({email}):\n\n{message}")
                booking_url = url_for('reply_generic', reply_type='booking', guest_email=email, _external=True)
                feedback_url = url_for('reply_generic', reply_type='feedback', guest_email=email, _external=True)
                location_url = url_for('reply_generic', reply_type='location', guest_email=email, _external=True)
                html_body = f"""
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
                """
                admin_msg.add_alternative(html_body, subtype="html")
                # Attach logo image inline
                with open("static/images/icons/RAG_Logo.png", "rb") as img:
                    admin_msg.get_payload()[1].add_related(img.read(), maintype="image", subtype="png", cid="RAG_Logo") # type: ignore

                # Send email    
                with smtplib.SMTP(config.SMTP_HOST, config.SMTP_PORT) as server: # type: ignore
                        server.starttls()
                        if config.SMTP_USER is not None and config.SMTP_PASS is not None: # type: ignore
                            server.login(config.SMTP_USER, config.SMTP_PASS) # type: ignore
                        server.send_message(admin_msg)

                app.logger.info("Admin notification email sent successfully.")
            except Exception:
                app.logger.exception("Failed to send admin notification email")

        flash("Thank you for contacting us. We'll get back to you soon.", "success")
        return redirect(url_for("contact"))

    return render_template("contact.html")

def send_html_reply(to_email, subject, body_html):
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = config.SMTP_USER # type: ignore
    msg["To"] = to_email

    msg.set_content(f"Dear visitor, From Ranchoddas Arogya Bhavan. This is an HTML email. Please view in a modern client.")
    msg.add_alternative(body_html, subtype="html")

    # Attach logo image inline
    with open("static/images/icons/RAG_Logo.png", "rb") as img:
        msg.get_payload()[1].add_related(img.read(), maintype="image", subtype="png", cid="RAG_Logo") # type: ignore

    with smtplib.SMTP(config.SMTP_HOST, config.SMTP_PORT) as server: # type: ignore
        server.starttls()
        if config.SMTP_USER is not None and config.SMTP_PASS is not None: # type: ignore
            server.login(config.SMTP_USER, config.SMTP_PASS) # type: ignore
        server.send_message(msg)

@app.route("/reply/<reply_type>/<guest_email>", methods=["GET", "POST"])
def reply_generic(reply_type, guest_email):
    replies = {
        "booking": {
            "subject": "Booking Response",
            "body_html": """
            <div class="card">
                <div class="logo">
                <img src="cid:RAG_Logo" alt="Ranchoddas Arogya Bhavan Logo" />
                </div>
            <h2>Thank you for your booking inquiry</h2>
            <p>   --Amin_Response_Space_Paragraph--   </p>
            <p>We appreciate your interest in Shri Ranchoddas Arogya Bhavan.</p>
            <p>📍 Location: Before Union Bank & Local Market, Matheran Hill Station<br>
                🌐 Website: <a href="https://www.ranchoddasbhavan.com">www.ranchoddasbhavan.com</a></p>
            </div>
            """
        },
        "feedback": {
            "subject": "Feedback Response",
            "body_html": """
            <div class="card">
                <div class="logo">
                <img src="cid:RAG_Logo" alt="Ranchoddas Arogya Bhavan Logo" />
                </div>
            <h2>Thank you for your feedback</h2>
            <p>   --Amin_Response_Space_Paragraph--   </p>
            <p>Your thoughts help us improve our hospitality.</p>
            <p>📍 Location: Before Union Bank & Local Market, Matheran Hill Station<br>
                🌐 Website: <a href="https://www.ranchoddasbhavan.com">www.ranchoddasbhavan.com</a></p>
            </div>
            """
        },
        "location": {
            "subject": "Location Details",
            "body_html": """
            <div class="card">
                <div class="logo">
                <img src="cid:RAG_Logo" alt="Ranchoddas Arogya Bhavan Logo" />
                </div>
            <h2>Our Location</h2>
            <p>   --Amin_Response_Space_Paragraph--   </p>
            <p>📍 Location: Before Union Bank & Local Market, Matheran Hill Station</p>
            <p>📍 <a href="https://goo.gl/maps/xyz123">View on Google Maps</a><br>
                🌐 Website: <a href="https://www.ranchoddasbhavan.com">www.ranchoddasbhavan.com</a></p>
            </div>
            """
        }
    }

    if reply_type not in replies:
        flash("Invalid reply type.", "danger")
        return redirect(url_for("contact"))

    template = replies[reply_type]

    if request.method == "POST":
        subject = request.form["subject"]
        body_html = request.form["body_html"]
        send_html_reply(guest_email, subject, body_html)
        flash(f"{reply_type.capitalize()} reply sent to guest.", "success")
        return redirect(url_for("contact"))

    return render_template("reply_to_contact.html", guest_email=guest_email, subject=template["subject"],
                        body_html=template["body_html"])

# Admin login/logout
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        admin_doc = db.admins.find_one({"username": username}) # type: ignore
        if admin_doc and check_password_hash(admin_doc["password_hash"], password): # type: ignore
            user = AdminUser(admin_doc)
            login_user(user)
            flash("Logged in successfully.", "success")
            return redirect(url_for("gallery_edit"))
        flash("Invalid credentials.", "danger")
    return render_template("login.html")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Logged out.", "info")
    return redirect(url_for("index"))

@app.errorhandler(404)
def page_not_found(e):
    return render_template("404.html"), 404

if __name__ == "__main__":
    #app.run(host='0.0.0.0', ssl_context=('cert.pem', 'key.pem'), debug=True) 
    #app.run(host='0.0.0.0', debug=True)
    port = int(os.environ.get("PORT", 5000))  # Render sets PORT automatically
    app.run(host="0.0.0.0", port=port, debug=False)