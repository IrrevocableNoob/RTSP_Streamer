# Linux support (experimental)

> **Status: best-effort, not yet tested on real Linux hardware.** The code
> paths exist and the unit suite passes on Ubuntu CI, but live video embedding
> (`set_xwindow`) and the AppImage have not been verified on a desktop. Please
> report what works.

## How it works

- Video is embedded via libvlc's `set_xwindow` (X11), chosen automatically by
  platform (Windows uses `set_hwnd`, macOS `set_nsobject`).
- On Linux the app sets `QT_QPA_PLATFORM=xcb` by default, so it runs under
  **X11 or XWayland** — a single embedding path that works on both X11 and
  Wayland sessions. Override by exporting `QT_QPA_PLATFORM` yourself.
- Config and logs: `$XDG_CONFIG_HOME/RTSP_Streamer` (default
  `~/.config/RTSP_Streamer`). Recordings default to `~/Videos/RTSP_Streamer`.

## Requirements

- **VLC (libvlc) installed:**
  - Debian/Ubuntu: `sudo apt install vlc`
  - Fedora: enable [RPM Fusion](https://rpmfusion.org/), then `sudo dnf install vlc`
  - RHEL/Rocky/Alma: enable EPEL + RPM Fusion, then install `vlc`
  - Arch: `sudo pacman -S vlc`
- An X11 or Wayland desktop session (Wayland runs the app via XWayland).
- `libxcb` and friends (present on essentially all desktops).

## Run from source

```bash
python -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
python -m rtsp_streamer
```

## Prebuilt AppImage

CI builds an AppImage on every push to the `linux` branch. Download it from the
repo's **Actions → linux workflow run → Artifacts** (`RTSP_Streamer-AppImage`),
then:

```bash
chmod +x RTSP_Streamer-x86_64.AppImage
./RTSP_Streamer-x86_64.AppImage
```

The AppImage bundles Python and Qt but **not** VLC — install VLC from your
distro as above. If it fails to start on a Wayland session, try:

```bash
QT_QPA_PLATFORM=xcb ./RTSP_Streamer-x86_64.AppImage
```

## Build the AppImage locally

```bash
./packaging/build-linux.sh      # produces dist/RTSP_Streamer (one-file binary)
```

(The full AppDir + `appimagetool` packaging is in `.github/workflows/linux.yml`.)

## Known unknowns (need real-hardware feedback)

- Whether `set_xwindow` embeds cleanly under your compositor (GNOME/KDE/XFCE).
- Hardware decode via VAAPI/VDPAU (`--avcodec-hw=any` falls back to software).
- AppImage portability across glibc versions (built on current Ubuntu).
- HiDPI / fractional scaling behavior.
