"""
tests/test_collector.py
Unit tests for pipeline/collector.py - mocks HTTP, no real network calls.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from unittest.mock import MagicMock, patch
import pytest
import requests
from shared.constants import TARGET_URL


class TestFetchAndSave:

    def test_successful_fetch_writes_html_file(self, tmp_path):
        from pipeline.collector import fetch_and_save
        dest = tmp_path / "doc.html"
        mock_resp = MagicMock()
        mock_resp.text = "<html><body>Hello BS4</body></html>"
        mock_resp.raise_for_status.return_value = None

        with patch("requests.get", return_value=mock_resp):
            result = fetch_and_save(url=TARGET_URL, dest=dest)

        assert result == dest
        assert dest.exists()
        assert "Hello BS4" in dest.read_text(encoding="utf-8")

    def test_returns_destination_path(self, tmp_path):
        from pipeline.collector import fetch_and_save
        dest = tmp_path / "out.html"
        mock_resp = MagicMock()
        mock_resp.text = "<html/>"
        mock_resp.raise_for_status.return_value = None

        with patch("requests.get", return_value=mock_resp):
            result = fetch_and_save(url=TARGET_URL, dest=dest)

        assert isinstance(result, Path)
        assert result == dest

    def test_http_error_raises_and_does_not_write_file(self, tmp_path):
        from pipeline.collector import fetch_and_save
        dest = tmp_path / "out.html"
        mock_resp = MagicMock()
        mock_resp.raise_for_status.side_effect = requests.HTTPError("404 Not Found")

        with patch("requests.get", return_value=mock_resp):
            with pytest.raises(requests.HTTPError):
                fetch_and_save(url=TARGET_URL, dest=dest)

        assert not dest.exists()

    def test_connection_error_propagates(self, tmp_path):
        from pipeline.collector import fetch_and_save
        dest = tmp_path / "out.html"
        with patch("requests.get", side_effect=requests.ConnectionError("unreachable")):
            with pytest.raises(requests.ConnectionError):
                fetch_and_save(url=TARGET_URL, dest=dest)

    def test_creates_parent_directories_automatically(self, tmp_path):
        from pipeline.collector import fetch_and_save
        dest = tmp_path / "nested" / "deep" / "doc.html"
        assert not dest.parent.exists()
        mock_resp = MagicMock()
        mock_resp.text = "<html/>"
        mock_resp.raise_for_status.return_value = None

        with patch("requests.get", return_value=mock_resp):
            fetch_and_save(url=TARGET_URL, dest=dest)

        assert dest.exists()

    def test_saves_with_utf8_encoding(self, tmp_path):
        from pipeline.collector import fetch_and_save
        dest = tmp_path / "doc.html"
        unicode_html = "<html><body>Ưu điểm của BeautifulSoup</body></html>"
        mock_resp = MagicMock()
        mock_resp.text = unicode_html
        mock_resp.raise_for_status.return_value = None

        with patch("requests.get", return_value=mock_resp):
            fetch_and_save(url=TARGET_URL, dest=dest)

        assert dest.read_text(encoding="utf-8") == unicode_html
