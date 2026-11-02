from rtsp_streamer.logging_setup import setup_logging


def test_password_redacted_in_log(tmp_path):
    log = tmp_path / "app.log"
    logger = setup_logging(str(log))
    logger.info("connecting %s", "rtsp://u:topsecret@10.0.0.5/live")
    for h in logger.handlers:
        h.flush()
    text = log.read_text(encoding="utf-8")
    assert "topsecret" not in text
    assert "***" in text


def test_password_in_format_string_redacted(tmp_path):
    log = tmp_path / "app.log"
    logger = setup_logging(str(log))
    logger.info("connecting rtsp://u:hunter2@10.0.0.5/live now")
    for h in logger.handlers:
        h.flush()
    text = log.read_text(encoding="utf-8")
    assert "hunter2" not in text
    assert "***" in text
