"""RTSP URL construction and credential redaction.

``build_rtsp_url`` normalizes user input into exactly one ``rtsp://`` prefix.
``redact_url`` masks the password so credentials never reach logs.
"""
from __future__ import annotations

import re

_SCHEME = "rtsp://"
# matches the userinfo segment "//user:password@" and captures the password
_CRED_RE = re.compile(r"(//[^:/@]+:)([^@/]+)(@)")


def build_rtsp_url(user_input: str) -> str:
    text = user_input.strip()
    if not text:
        raise ValueError("stream URL must not be empty")
    if text.lower().startswith(_SCHEME):
        text = text[len(_SCHEME):]
    return _SCHEME + text


def redact_url(url: str) -> str:
    return _CRED_RE.sub(r"\1***\3", url)
