$s=(New-Object -COM WScript.Shell).CreateShortcut("$env:USERPROFILE\Desktop\GitHub Backup.lnk")
$s.TargetPath="powershell.exe"
$s.Arguments="-ExecutionPolicy Bypass -File `"$PSScriptRoot\github_backup.ps1`""
$s.WorkingDirectory="$PSScriptRoot"
$s.Save()
Write-Host 'Shortcut erstellt auf Desktop.'