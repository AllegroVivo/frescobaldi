from unittest.mock import patch, MagicMock
from PySide6.QtWidgets import QTabWidget, QLabel, QWidget
from frescobaldi import about
import pytest


@pytest.fixture(scope="function")
def setup_translations(monkeypatch):
    def _set_translation(func):
        monkeypatch.setattr("builtins._", func)
    return _set_translation

@patch.object(about, "appinfo")
def test_html_details_and_links(mock_appinfo):
    mock_appinfo.appname = "TestApp"
    mock_appinfo.version = "1.0.0"
    mock_appinfo.maintainer_email = "test@example.com"
    mock_appinfo.maintainer = "Test Maintainer"
    mock_appinfo.url = "https://testapp.local"

    result = about.html()

    assert "TestApp" in result
    assert "Version 1.0.0" in result
    assert "test@example.com" in result
    assert "Test Maintainer" in result
    assert "https://testapp.local" in result

def test_html_omit_translator(setup_translations):
    setup_translations(lambda x: "Translated by Jane Doe." if x == "Translated by Your Name." else x)
    result = about.html()
    assert "<p>Translated by Jane Doe.</p>" in result

    setup_translations(lambda x: x)
    result = about.html()
    assert "Translated by" not in result

@patch("about.appinfo")
def test_about_dialog_defaults(mock_appinfo):
    mock_appinfo.appname = "TestApp"
    parent = QWidget()

    dialog = about.AboutDialog(parent)
    tab_widget = dialog.findChild(QTabWidget)

    assert "TestApp" in dialog.windowTitle()
    assert tab_widget is not None
    assert tab_widget.count() == 3
































