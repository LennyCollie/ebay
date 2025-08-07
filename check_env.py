import os
import sys

print("🔍 Starte Diagnose ...")

# Prüfe Flask
try:
    import flask
    print("✅ Flask ist installiert:", flask.__version__)
except ImportError:
    print("❌ Flask ist NICHT installiert!")
    sys.exit(1)

# Prüfe python-dotenv
try:
    from dotenv import load_dotenv
    print("✅ python-dotenv ist installiert.")
except ImportError:
    print("❌ python-dotenv ist NICHT installiert!")
    sys.exit(1)

# Prüfe .env-Datei
if os.path.exists(".env"):
    print("✅ .env-Datei gefunden.")
else:
    print("⚠️  .env-Datei NICHT gefunden!")

# Versuche app.py zu importieren
try:
    import app
    print("✅ app.py konnte erfolgreich importiert werden.")
except Exception as e:
    print("❌ Fehler beim Importieren von app.py:")
    print(e)
    sys.exit(1)

print("🎉 Alles sieht gut aus!")