"""PyInstaller entry point. Uses an absolute import (a relative import would
fail when PyInstaller runs this as the top-level script)."""
import sys

from rtsp_streamer.app import main

if __name__ == "__main__":
    sys.exit(main())
