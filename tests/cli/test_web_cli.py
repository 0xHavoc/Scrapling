from scrapling.web import read_ui


def test_read_ui_has_html_document():
    content = read_ui()
    assert "<!doctype html>" in content.lower()
    assert "Scrapling Web UI" in content
