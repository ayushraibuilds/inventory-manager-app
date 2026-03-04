"""Tests for image processor module (mocked — no actual API calls)."""
import pytest
from unittest.mock import patch, MagicMock
from image_processor import _parse_vision_response, process_product_image


class TestParseVisionResponse:
    """Tests for parsing the Vision model's text response."""

    def test_parse_valid_json(self):
        text = '{"items": [{"name": "Atta", "price_inr": "45", "quantity": 10, "unit": "kg", "category": "Grocery"}]}'
        result = _parse_vision_response(text)
        assert len(result["items"]) == 1
        assert result["items"][0]["name"] == "Atta"

    def test_parse_json_in_markdown(self):
        text = '''Here are the products:
```json
{"items": [{"name": "Rice", "price_inr": "60", "quantity": 5, "unit": "kg", "category": "Grocery"}]}
```
'''
        result = _parse_vision_response(text)
        assert len(result["items"]) == 1

    def test_parse_multiple_items(self):
        text = '{"items": [{"name": "Atta", "price_inr": "45", "quantity": 10, "unit": "kg", "category": "Grocery"}, {"name": "Dal", "price_inr": "120", "quantity": 5, "unit": "kg", "category": "Grocery"}]}'
        result = _parse_vision_response(text)
        assert len(result["items"]) == 2

    def test_parse_invalid_json(self):
        text = "I can see some products on the shelf but cannot format them properly"
        result = _parse_vision_response(text)
        assert result == {"items": []}

    def test_parse_empty_items(self):
        text = '{"items": []}'
        result = _parse_vision_response(text)
        assert result["items"] == []

    def test_parse_json_with_surrounding_text(self):
        text = 'Based on the image, I identified: {"items": [{"name": "Sugar", "price_inr": "45", "quantity": 1, "unit": "kg", "category": "Grocery"}]} That is all.'
        result = _parse_vision_response(text)
        assert len(result["items"]) == 1
        assert result["items"][0]["name"] == "Sugar"


class TestProcessProductImage:
    """Tests for the full pipeline (mocked)."""

    @patch("image_processor._call_vision_api")
    @patch("image_processor._download_twilio_image")
    def test_full_pipeline(self, mock_download, mock_vision):
        mock_download.return_value = b"fake image bytes"
        mock_vision.return_value = {
            "items": [
                {"name": "Atta", "price_inr": "45", "quantity": 10, "unit": "kg", "category": "Grocery"},
                {"name": "Dal", "price_inr": "120", "quantity": 5, "unit": "kg", "category": "Grocery"},
            ]
        }

        result = process_product_image("https://example.com/image.jpg", "en")
        assert len(result) == 2
        assert result[0]["name"] == "Atta"
        assert result[0]["price_inr"] == "45"
        assert result[0]["quantity"] == 10

    @patch("image_processor._call_vision_api")
    @patch("image_processor._download_twilio_image")
    def test_empty_image_result(self, mock_download, mock_vision):
        mock_download.return_value = b"fake image bytes"
        mock_vision.return_value = {"items": []}

        result = process_product_image("https://example.com/image.jpg", "en")
        assert result == []

    @patch("image_processor._download_twilio_image")
    def test_download_failure(self, mock_download):
        mock_download.side_effect = Exception("Download failed")

        with pytest.raises(Exception, match="Download failed"):
            process_product_image("https://example.com/image.jpg", "en")
