# Optional installer: copies RTSP_Streamer.exe to C:\rtsp_streamer and creates
# a desktop shortcut. Put this next to RTSP_Streamer.exe and run it:
#   powershell -ExecutionPolicy Bypass -File .\install.ps1
# The app itself needs no install (it is a single exe); this is only for users
# who want it to live at a fixed location with a shortcut.
$ErrorActionPreference = "Stop"

$dest = "C:\rtsp_streamer"
$exe = Join-Path $PSScriptRoot "RTSP_Streamer.exe"
if (-not (Test-Path $exe)) {
    $exe = Join-Path (Split-Path $PSScriptRoot) "dist\RTSP_Streamer.exe"
}
if (-not (Test-Path $exe)) {
    throw "RTSP_Streamer.exe not found next to this script or in ..\dist"
}

New-Item -ItemType Directory -Force -Path $dest | Out-Null
Copy-Item $exe (Join-Path $dest "RTSP_Streamer.exe") -Force

$shell = New-Object -ComObject WScript.Shell
$lnk = $shell.CreateShortcut(
    (Join-Path ([Environment]::GetFolderPath("Desktop")) "RTSP_Streamer.lnk"))
$lnk.TargetPath = Join-Path $dest "RTSP_Streamer.exe"
$lnk.WorkingDirectory = $dest
$lnk.Save()

Write-Host "Installed to $dest and created a desktop shortcut."
