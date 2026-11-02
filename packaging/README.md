# Packaging

Builds a single-file `RTSP_Streamer.exe` with [PyInstaller](https://pyinstaller.org/).
VLC is **not** bundled — the exe uses the system-installed VLC at runtime, same
as running from source. A packaged (frozen) build stores `config.json` and
`app.log` in `%APPDATA%\RTSP_Streamer` rather than beside the exe.

## Build

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt pyinstaller
.\packaging\build.ps1
```

Result: `dist\RTSP_Streamer.exe` (one file, double-click to run).

## Optional: install to C:\rtsp_streamer

`install.ps1` copies the exe to `C:\rtsp_streamer` and makes a desktop shortcut.
The app needs no install — this is only for a fixed location:

```powershell
powershell -ExecutionPolicy Bypass -File .\packaging\install.ps1
```

## Files

- `launch.py` — PyInstaller entry point (absolute import of `rtsp_streamer.app`).
- `build.ps1` — the build command.
- `install.ps1` — optional copy-to-`C:\rtsp_streamer` + desktop shortcut.
