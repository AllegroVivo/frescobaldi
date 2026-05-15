from unittest.mock import patch, MagicMock
from PySide6.QtWidgets import QTabWidget, QLabel
import about
import pytest


@patch("about.appinfo")
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

def test_html_omit_translator():
    result = about.html()
    assert "<p>Translated by Your Name.</p>" not in result


































