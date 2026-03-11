"""Tests for the multilingual reply templates module."""
import pytest
from reply_templates import format_reply, get_faq_answer


class TestFormatReply:
    """Tests for format_reply()."""

    def test_english_add(self):
        reply = format_reply("en", "ADD", items="Atta (₹450 × 10 kg)", count=12)
        assert "Atta" in reply
        assert "12" in reply
        assert "✅" in reply

    def test_hindi_add(self):
        reply = format_reply("hi", "ADD", items="आटा (₹450 × 10 kg)", count=12)
        assert "12" in reply
        assert "✅" in reply
        assert "कैटलॉग" in reply

    def test_english_delete(self):
        reply = format_reply("en", "DELETE")
        assert "🗑️" in reply

    def test_hindi_delete(self):
        reply = format_reply("hi", "DELETE")
        assert "🗑️" in reply
        assert "हटा" in reply

    def test_english_unknown(self):
        reply = format_reply("en", "UNKNOWN")
        assert "🤔" in reply

    def test_hindi_unknown(self):
        reply = format_reply("hi", "UNKNOWN")
        assert "🤔" in reply

    def test_fallback_to_english(self):
        """Tamil templates are stubs, should fall back to English."""
        reply = format_reply("ta", "DELETE")
        assert "🗑️" in reply  # Should get the English version

    def test_unknown_language_falls_back(self):
        reply = format_reply("xx", "ADD", items="Rice", count=5)
        assert "Rice" in reply  # English fallback

    def test_missing_format_args_graceful(self):
        """If format args are missing, return template as-is without crashing."""
        reply = format_reply("en", "ADD")  # Missing items and count
        assert reply  # Should return something, not crash

    def test_rate_limited_english(self):
        reply = format_reply("en", "RATE_LIMITED")
        assert "⏳" in reply

    def test_rate_limited_hindi(self):
        reply = format_reply("hi", "RATE_LIMITED")
        assert "⏳" in reply

    def test_received_english(self):
        reply = format_reply("en", "RECEIVED")
        assert "Received" in reply

    def test_received_hindi(self):
        reply = format_reply("hi", "RECEIVED")
        assert "मैसेज" in reply

    def test_onboarding_english(self):
        reply = format_reply("en", "ONBOARDING")
        assert "Welcome" in reply

    def test_onboarding_hindi(self):
        reply = format_reply("hi", "ONBOARDING")
        assert "स्वागत" in reply


class TestFaqAnswers:
    """Tests for get_faq_answer()."""

    def test_english_how_to_use(self):
        answer = get_faq_answer("en", "how_to_use")
        assert "WhatsApp" in answer

    def test_hindi_how_to_use(self):
        answer = get_faq_answer("hi", "how_to_use")
        assert "WhatsApp" in answer

    def test_english_pricing(self):
        answer = get_faq_answer("en", "pricing")
        assert "free" in answer.lower()

    def test_hindi_pricing(self):
        answer = get_faq_answer("hi", "pricing")
        assert "फ्री" in answer

    def test_english_ondc(self):
        answer = get_faq_answer("en", "ondc")
        assert "ONDC" in answer

    def test_unknown_topic_returns_empty(self):
        answer = get_faq_answer("en", "nonexistent_topic")
        assert answer == ""

    def test_unknown_language_falls_back(self):
        answer = get_faq_answer("xx", "pricing")
        assert "free" in answer.lower()  # English fallback
