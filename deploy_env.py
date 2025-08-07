import os

env_path = ".env"

# Abbruch, wenn Datei schon existiert
if os.path.exists(env_path):
    print(f"❌ '{env_path}' existiert bereits – nichts geändert.")
    exit()

# Beispielwerte – diese musst du anpassen oder leer lassen
env_vars = {
    "API_SECRET_KEY": "your-secret-key",
    "SQLALCHEMY_DATABASE_URI": "postgresql://user:pass@host/dbname",
    "EBAY_APP_ID": "your-ebay-app-id",
    "EBAY_CERT_ID_PRD": "your-ebay-cert-id",
    "SENDER_EMAIL": "you@example.com",
    "EMAIL_PASSWORD": "your-email-password",
    "STRIPE_SECRET_KEY": "sk_test_yourkey",
    "STRIPE_PRICE_ID": "price_12345",
}

# Schreiben der .env Datei
with open(env_path, "w") as f:
    for key, value in env_vars.items():
        f.write(f"{key}={value}\n")

print(f"✅ '{env_path}' erfolgreich erstellt.")