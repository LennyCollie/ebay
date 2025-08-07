print("🟢 App wird gestartet …")
import os
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager, login_user, logout_user, login_required, UserMixin, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
import stripe
import requests

# ENV laden
load_dotenv()

# Stripe konfigurieren
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
endpoint_secret = os.getenv("STRIPE_WEBHOOK_SECRET")

# Flask App & Config
app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "devkey")
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL", "sqlite:///instance/db.sqlite3")

# Datenbank & Login
from models import db, User
db.init_app(app)
login_manager = LoginManager()
login_manager.login_view = "login"
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# Neue Startseite leitet auf Login
@app.route('/')
@login_required
def home():
    return redirect(url_for("dashboard"))

# Dashboard (vorher: home)
@app.route('/dashboard')
@login_required
def dashboard():
    return render_template("dashboard.html", user=current_user)


# Login
@app.route('/login', methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            flash("Login erfolgreich!")
            return redirect(url_for("dashboard"))
        else:
            flash("Ungültige E-Mail oder Passwort.")
            return redirect(url_for("login"))
    return render_template("login.html")


# Registrierung
@app.route('/register', methods=["GET", "POST"])
def register():
    if request.method == "POST":
        email = request.form["email"]
        password = generate_password_hash(request.form["password"])
        user = User(email=email, password=password)
        db.session.add(user)
        db.session.commit()
        flash("Registrierung erfolgreich!")
        return redirect(url_for("login"))
    return render_template("register.html")



@app.route("/search", methods=["GET", "POST"])
@login_required
def search():
    if not current_user.is_premium:
        flash("Nur Premium-Nutzer dürfen diese Funktion nutzen.", "danger")
        return redirect(url_for("dashboard"))

    query = request.args.get("query") if request.method == "GET" else request.form.get("query")
    if not query:
        flash("Bitte gib einen Suchbegriff ein.", "warning")
        return redirect(url_for("dashboard"))

    try:
        # Render-API aufrufen
        api_url = "https://ebay-agent-cockpit.onrender.com/search"
        response = requests.get(api_url, params={"q": query}, timeout=10)
        response.raise_for_status()
        results = response.json()
    except Exception as e:
        return render_template("ebay_results.html", results=[], query=query, error=str(e))

    return render_template("ebay_results.html", results=results, query=query)


@app.route('/premium')
@login_required
def premium():
    premium_price = os.getenv("PREMIUM_PRICE", "5.00")
    return render_template('premium.html', price=premium_price)


# Checkout-Session
@app.route('/create-checkout-session', methods=['POST'])
@login_required
def create_checkout_session():
    try:
        checkout_session = stripe.checkout.Session.create(
            customer_email=current_user.email,
            line_items=[{
                'price': os.getenv("STRIPE_PRICE_ID"),
                'quantity': 1,
            }],
            mode='subscription',
            success_url=url_for('dashboard', _external=True) + '?success=true',
            cancel_url=url_for('dashboard', _external=True) + '?canceled=true',
        )
        return redirect(checkout_session.url, code=303)
    except Exception as e:
        return str(e)


# Einstellungen
@app.route("/settings", methods=["GET", "POST"])
@login_required
def settings():
    message = ""
    if request.method == "POST":
        if "email" in request.form:
            current_user.email = request.form["email"]
            db.session.commit()
            message = "E-Mail wurde aktualisiert."
        elif "password" in request.form:
            current_user.password = generate_password_hash(request.form["password"])
            db.session.commit()
            message = "Passwort wurde aktualisiert."
    return render_template("settings.html", user=current_user, message=message)


# Logout
@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Abgemeldet.")
    return redirect(url_for("login"))


# Stripe Webhook
@app.route("/webhook", methods=["POST"])
def stripe_webhook():
    payload = request.data
    sig_header = request.headers.get("stripe-signature")

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, endpoint_secret)
    except stripe.error.SignatureVerificationError as e:
        print("❌ Signature Error:", e)
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        print("❌ Webhook Fehler:", e)
        return jsonify({"error": str(e)}), 400

    print("✅ Webhook empfangen:", event["type"])

    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        email = session.get("customer_email")
        print("📧 Customer Email aus Session:", email)

        try:
            user = User.query.filter_by(email=email).first()
            if user:
                user.is_premium = True
                db.session.commit()
                print(f"✅ {email} wurde auf Premium gesetzt!")
            else:
                print("⚠️ Kein Benutzer mit dieser E-Mail gefunden:", email)
        except Exception as e:
            print("❌ DB-Fehler:", e)

    return jsonify({"status": "success"}), 200


# Fehlerseite (optional)
@app.errorhandler(404)
def page_not_found(e):
    return render_template("404.html"), 404

from flask import session  # Wichtig: Ganz oben ergänzen, falls noch nicht vorhanden

# 🚪 Logout-Route
@app.route("/logout")
def logout():
    # Sitzung löschen (optional)
    session.clear()

    # Erfolgsmeldung anzeigen
    flash("Du wurdest erfolgreich ausgeloggt.")

    # Zur Login-Seite weiterleiten
    return redirect(url_for("login"))


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 10000)))