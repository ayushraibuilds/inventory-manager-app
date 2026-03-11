"""Tests for voice processor module (mocked — no real Twilio/Groq calls)."""
import pytest
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock
from voice_processor import VoiceProcessor


class TestVoiceProcessor:
    """Tests for the VoiceProcessor class."""

    def test_instance_created(self):
        vp = VoiceProcessor()
        assert vp is not None

    @patch("voice_processor.get_env_value")
    def test_download_requires_credentials(self, mock_get_env):
        """Missing Twilio credentials should raise ValueError."""
        mock_get_env.return_value = ""
        vp = VoiceProcessor()
        with pytest.raises(ValueError, match="Missing TWILIO"):
            vp._download_twilio_media_sync("https://example.com/audio.ogg", "/tmp/test.ogg")

    @patch("voice_processor.get_env_value")
    @patch("voice_processor.requests.get")
    def test_download_success(self, mock_get, mock_get_env):
        """Successful download writes file."""
        mock_get_env.side_effect = lambda key, default="": {
            "TWILIO_ACCOUNT_SID": "AC_test",
            "TWILIO_AUTH_TOKEN": "token_test",
        }.get(key, default)
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.iter_content.return_value = [b"audio-chunk"]
        mock_get.return_value = mock_response

        import tempfile, os
        with tempfile.NamedTemporaryFile(suffix=".ogg", delete=False) as f:
            tmp = f.name

        try:
            vp = VoiceProcessor()
            vp._download_twilio_media_sync("https://api.twilio.com/audio.ogg", tmp)
            with open(tmp, "rb") as f:
                assert f.read() == b"audio-chunk"
        finally:
            os.unlink(tmp)

    @patch("voice_processor.get_env_value")
    @patch("voice_processor.requests.get")
    def test_download_failure_raises(self, mock_get, mock_get_env):
        """Non-200 response from Twilio raises."""
        mock_get_env.side_effect = lambda key, default="": {
            "TWILIO_ACCOUNT_SID": "AC_test",
            "TWILIO_AUTH_TOKEN": "token_test",
        }.get(key, default)
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.text = "Not Found"
        mock_get.return_value = mock_response

        vp = VoiceProcessor()
        with pytest.raises(Exception, match="Failed to download"):
            vp._download_twilio_media_sync("https://api.twilio.com/bad.ogg", "/tmp/test.ogg")


class TestTranscribeAudio:
    """Tests for the async transcribe_audio method."""

    @patch("voice_processor.AsyncGroq")
    @patch("voice_processor.get_env_value")
    @patch.object(VoiceProcessor, "_download_twilio_media_sync")
    def test_transcription_pipeline(self, mock_download, mock_get_env, mock_groq_cls):
        """Full transcription pipeline with mocks."""
        mock_get_env.side_effect = lambda key, default="": {
            "GROQ_API_KEY": "test-key",
        }.get(key, default)

        # Write fake audio to the temp file
        def fake_download(url, path):
            with open(path, "wb") as f:
                f.write(b"fake-audio")
        mock_download.side_effect = fake_download

        # Mock Groq async
        mock_transcription = MagicMock()
        mock_transcription.text = "add 5 kg atta at 45 rupees"
        mock_client = MagicMock()
        mock_client.audio.transcriptions.create = AsyncMock(return_value=mock_transcription)
        mock_groq_cls.return_value = mock_client

        vp = VoiceProcessor()
        result = asyncio.run(vp.transcribe_audio("https://api.twilio.com/audio.ogg"))
        assert result == "add 5 kg atta at 45 rupees"

    @patch("voice_processor.get_env_value")
    @patch.object(VoiceProcessor, "_download_twilio_media_sync")
    def test_missing_groq_key_raises(self, mock_download, mock_get_env):
        """Missing GROQ_API_KEY should raise ValueError."""
        mock_get_env.return_value = ""
        mock_download.side_effect = lambda url, path: open(path, "wb").close()

        vp = VoiceProcessor()
        with pytest.raises(ValueError, match="Missing GROQ_API_KEY"):
            asyncio.run(vp.transcribe_audio("https://api.twilio.com/audio.ogg"))
