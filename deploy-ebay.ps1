# Speicherort: z. B. auf Desktop oder im Projektordner
# Name: deploy-ebay.ps1

# === Einstellungen ===
$sourceDir = "C:\ebay"
$backupBase = "C:\ebay-backup"
$date = Get-Date -Format "yyyy-MM-dd_HHmmss"
$backupDir = "$backupBase-$date"

# === Backup erstellen ===
Copy-Item -Recurse -Force -Path $sourceDir -Destination $backupDir

# === In Backup wechseln ===
Set-Location $backupDir

# === .env löschen, falls vorhanden ===
if (Test-Path ".env") {
    Remove-Item ".env"
    Write-Host ".env entfernt"
}

# === Git vorbereiten ===
git init
git remote add origin https://github.com/LennyCollie/ebay.git
git add .
git commit -m "Automatisches Backup und Push vom $date"

# === Push erzwingen ===
git branch -M main
git push -f origin main

Write-Host "`n✅ Backup und Push abgeschlossen aus $backupDir"