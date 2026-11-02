import pytest

from rtsp_streamer.urls import build_rtsp_url, redact_url


def test_prepends_scheme():
    assert build_rtsp_url("user:pw@10.0.0.5:554/live") == "rtsp://user:pw@10.0.0.5:554/live"


def test_does_not_double_prefix():
    assert build_rtsp_url("rtsp://10.0.0.5/live") == "rtsp://10.0.0.5/live"


def test_strips_whitespace():
    assert build_rtsp_url("  10.0.0.5/live  ") == "rtsp://10.0.0.5/live"


def test_blank_raises():
    with pytest.raises(ValueError):
        build_rtsp_url("   ")


def test_redacts_password():
    assert redact_url("rtsp://user:secret@10.0.0.5/live") == "rtsp://user:***@10.0.0.5/live"


def test_redact_noop_without_creds():
    assert redact_url("rtsp://10.0.0.5/live") == "rtsp://10.0.0.5/live"
