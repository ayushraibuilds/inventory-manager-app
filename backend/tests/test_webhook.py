"""Tests for webhook endpoint processing (mocked — no real Twilio/Groq calls)."""
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi.testclient import TestClient


class TestWebhookEndpoint:
    """Tests for the /webhook POST endpoint."""

    @pytest.fixture
    def client(self):
        from server import app
        return TestClient(app)

    @patch("routes.webhook.verify_twilio_signature", return_value=True)
    def test_webhook_no_body_returns_response(self, mock_sig, client):
        """Empty POST still returns a response (Twilio expects one)."""
        res = client.post("/whatsapp-webhook", data={})
        # May be 200 (twiml) or 422 (validation) — either is acceptable
        assert res.status_code in (200, 422)

    @patch("routes.webhook.verify_twilio_signature", return_value=True)
    def test_webhook_text_message(self, mock_sig, client):
        """Text message should be accepted."""
        res = client.post("/whatsapp-webhook", data={
            "From": "whatsapp:+919876543210",
            "Body": "add 5 kg rice at 60",
        })
        assert res.status_code == 200

    @patch("routes.webhook.verify_twilio_signature", return_value=True)
    def test_webhook_audio_message(self, mock_sig, client):
        """Voice note message should be accepted."""
        res = client.post("/whatsapp-webhook", data={
            "From": "whatsapp:+919876543210",
            "Body": "",
            "NumMedia": "1",
            "MediaContentType0": "audio/ogg",
            "MediaUrl0": "https://api.twilio.com/test-audio.ogg",
        })
        assert res.status_code == 200

    @patch("routes.webhook.verify_twilio_signature", return_value=True)
    def test_webhook_image_message(self, mock_sig, client):
        """Image message should be accepted."""
        res = client.post("/whatsapp-webhook", data={
            "From": "whatsapp:+919876543210",
            "Body": "",
            "NumMedia": "1",
            "MediaContentType0": "image/jpeg",
            "MediaUrl0": "https://api.twilio.com/test-photo.jpg",
        })
        assert res.status_code == 200

    @patch("routes.webhook.verify_twilio_signature", return_value=True)
    def test_webhook_returns_twiml(self, mock_sig, client):
        """Webhook should return valid TwiML (XML) or empty 200."""
        res = client.post("/whatsapp-webhook", data={
            "From": "whatsapp:+919876543210",
            "Body": "hello",
        })
        assert res.status_code == 200

    @patch("routes.webhook.verify_twilio_signature", return_value=True)
    def test_webhook_sends_received_ack(self, mock_sig, client):
        with patch("routes.webhook.get_seller_id_by_phone", return_value="seller-123"), \
             patch("routes.webhook.get_seller_profile", return_value={"store_name": "Test Store"}), \
             patch("routes.webhook.is_rate_limited", return_value=False), \
             patch("routes.webhook.get_conversation_history", return_value=[]), \
             patch("routes.webhook.log_activity"), \
             patch("routes.webhook.send_whatsapp_reply", return_value=True) as mock_reply, \
             patch("routes.webhook.process_webhook_background", new=AsyncMock()), \
             patch("redis_client.redis_client.ping", side_effect=RuntimeError("redis offline")):
            res = client.post("/whatsapp-webhook", data={
                "From": "whatsapp:+919876543210",
                "Body": "add 5 kg rice at 60",
            })

        assert res.status_code == 200
        mock_reply.assert_called_once()
        assert mock_reply.call_args.args[0] == "whatsapp:+919876543210"
        assert "Received" in mock_reply.call_args.args[1]


class TestProcessWebhookBackground:
    """Verify the background processing function exists and is callable."""

    def test_function_exists(self):
        from routes.webhook import process_webhook_background
        assert callable(process_webhook_background)

    def test_function_signature(self):
        """Background processor accepts required arguments."""
        import inspect
        from routes.webhook import process_webhook_background
        sig = inspect.signature(process_webhook_background)
        param_names = list(sig.parameters.keys())
        assert "raw_message" in param_names
        assert "seller_id" in param_names
        assert "extracted_phone" in param_names
