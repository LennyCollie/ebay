
# Prüfe ob Java installiert ist
if (-not (Get-Command java -ErrorAction SilentlyContinue)) {
    Write-Host "❌ Java ist nicht installiert oder nicht im PATH."
    Write-Host "Bitte installiere Java von: https://www.oracle.com/java/technologies/javase-downloads.html"
    exit 1
}

# Git-URL eintragen
$gitUrl = "https://github.com/LennyCollie/ebay.git"
$cleanDir = "$PWD\ebay-clean"

# Repository klonen
Write-Host "📥 Klone das Repository nach $cleanDir ..."
git clone --mirror $gitUrl $cleanDir

# Wechsle ins Verzeichnis
Set-Location $cleanDir

# Lade BFG Repo-Cleaner, falls nicht vorhanden
if (-not (Test-Path "..\bfg.jar")) {
    Invoke-WebRequest "https://repo1.maven.org/maven2/com/madgag/bfg/1.14.0/bfg-1.14.0.jar" -OutFile "..\bfg.jar"
}

# BFG Repo Cleaner starten
Write-Host "🧹 Starte BFG Repo-Cleaner ..."
java -jar ..\bfg.jar --delete-files .env

# Bereinigung finalisieren
git reflog expire --expire=now --all
git gc --prune=now --aggressive

# Push zurück nach GitHub
Write-Host "🚀 Push wird durchgeführt ..."
git push --force

Write-Host "✅ Bereinigung abgeschlossen und gepusht."