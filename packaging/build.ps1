# Build a one-file RTSP_Streamer.exe. Run from the repo root inside the venv:
#   .\.venv\Scripts\Activate.ps1
#   .\packaging\build.ps1
# Output: dist\RTSP_Streamer.exe
pyinstaller --noconfirm --clean --onefile --windowed `
  --name RTSP_Streamer --paths src `
  --distpath dist --workpath build/pyi --specpath build `
  packaging/launch.py
