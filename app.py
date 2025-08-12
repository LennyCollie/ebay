print("\U0001F7E2 App wird gestartet …")

import os
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from flask_sqlalchemy import SQLAlchemy
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

# -------------------------
# Public Seiten
# -------------------------
@app.get("/public")
def public_home():
    return render_template("public_home.html")

@app.get("/pricing")
def public_pricing():
    return render_template("public_pricing.html")

@app.get("/debug")
def debug_simple():
    return {"alive": True}

# -------------------------
# Hauptseiten (Login nötig)
# -------------------------
@app.route('/')
@login_required
def home():
    return redirect(url_for("dashboard"))

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template("dashboard.html", user=current_user)

# -------------------------
# Auth
# -------------------------
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

@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Abgemeldet.")
    return redirect(url_for("login"))

# -------------------------
# Suche (nur Premium)
# -------------------------
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
        api_url = "https://ebay-agent-cockpit.onrender.com/search"
        response = requests.get(api_url, params={"q": query}, timeout=10)
        response.raise_for_status()
        results = response.json()
    except Exception as e:
        return render_template("ebay_results.html", results=[], query=query, error=str(e))

    return render_template("ebay_results.html", results=results, query=query)

# -------------------------
# Premium / Stripe Checkout
# -------------------------
@app.route('/premium')
@login_required
def premium():
    premium_price = os.getenv("PREMIUM_PRICE", "5.00")
    return render_template('premium.html', price=premium_price)

@app.route("/checkout", methods=["GET","POST"])
def public_checkout():
    if request.method == "POST":
        email = (request.form.get("email") or "").strip()
        try:
            session = stripe.checkout.Session.create(
                mode="subscription",
                line_items=[{"price": os.getenv("STRIPE_PRICE_PRO"), "quantity": 1}],
                customer_email=email,
                success_url=os.getenv("STRIPE_SUCCESS_URL", url_for("checkout_success", _external=True)),
                cancel_url=os.getenv("STRIPE_CANCEL_URL", url_for("public_pricing", _external=True)),
                allow_promotion_codes=True,
            )
            return redirect(session.url, code=303)
        except Exception as e:
            flash(f"Stripe-Fehler: {e}", "danger")
            return redirect(url_for("public_checkout"))
    return render_template("public_checkout.html")

@app.get("/checkout/success")
def checkout_success():
    return render_template("checkout_success.html")

# -------------------------
# Debug-Route für Stripe
# -------------------------
@app.get("/_debug/stripe")
def debug_stripe():
    price_id = os.getenv("STRIPE_PRICE_PRO")
    result = {
        "STRIPE_SECRET_KEY_set": bool(os.getenv("STRIPE_SECRET_KEY")),
        "STRIPE_PUBLIC_KEY_set": bool(os.getenv("STRIPE_PUBLIC_KEY")),
        "STRIPE_PRICE_PRO": price_id,
        "can_list_prices": False,
        "price_exists": False,
        "error": None
    }
    try:
        stripe.Price.list(limit=1)
        result["can_list_prices"] = True
        if price_id:
            try:
                stripe.Price.retrieve(price_id)
                result["price_exists"] = True
            except Exception as e:
                result["error"] = str(e)
    except Exception as e:
        result["error"] = str(e)
    return result

# -------------------------
# Einstellungen
# -------------------------
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

# -------------------------
# Stripe Webhook
# -------------------------
@app.route("/webhook", methods=["POST"])
def stripe_webhook():
    payload = request.data
    sig_header = request.headers.get("Stripe-Signature", "")
    try:
        event = stripe.Webhook.construct_event(payload, sig_header, endpoint_secret)
    except stripe.error.SignatureVerificationError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 400

    if event["type"] == "checkout.session.completed":
        session_obj = event["data"]["object"]
        email = session_obj.get("customer_email")
        user = User.query.filter_by(email=email).first()
        if user:
            user.is_premium = True
            db.session.commit()

    return jsonify({"status": "success"}), 200

# -------------------------
# Error Handler
# -------------------------
@app.errorhandler(404)
def page_not_found(e):
    return render_template("404.html"), 404

# -------------------------
# Start
# -------------------------
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 10000)))
