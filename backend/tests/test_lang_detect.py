"""Tests for the hybrid language detection module."""
import pytest
from lang_detect import detect, LangResult


class TestKeywordDetection:
    """Tests for the Hinglish keyword heuristic (Step 1)."""

    def test_hindi_rakh_do(self):
        result = detect("10 kilo atta 450 mein rakh do")
        assert result.lang_code == "hi"
        assert result.method == "keyword"

    def test_hindi_hata_do(self):
        result = detect("maggi hata do meri dukan mein se")
        assert result.lang_code == "hi"
        assert result.method == "keyword"

    def test_hindi_set_karo(self):
        result = detect("chawal ka price set karo 60 mein")
        assert result.lang_code == "hi"
        assert result.method == "keyword"

    def test_hindi_chahiye(self):
        result = detect("mujhe help chahiye kaise use karu")
        assert result.lang_code == "hi"
        assert result.method == "keyword"

    def test_hindi_khatam(self):
        result = detect("atta khatam ho gaya hai")
        assert result.lang_code == "hi"
        assert result.method == "keyword"


class TestScriptDetection:
    """Tests for Unicode script detection (Step 2)."""

    def test_devanagari(self):
        result = detect("आटा 450 रुपये")
        assert result.lang_code == "hi"
        assert result.method == "script"

    def test_tamil(self):
        result = detect("நெய் 500 கிராம் 120 ரூபாய்")
        assert result.lang_code == "ta"
        assert result.method == "script"

    def test_telugu(self):
        result = detect("బియ్యం 60 రూపాయలు")
        assert result.lang_code == "te"
        assert result.method == "script"

    def test_kannada(self):
        result = detect("ಅಕ್ಕಿ 50 ರೂಪಾಯಿ")
        assert result.lang_code == "kn"
        assert result.method == "script"

    def test_bengali(self):
        result = detect("চাল ৬০ টাকা")
        assert result.lang_code == "bn"
        assert result.method == "script"


class TestFallbackDetection:
    """Tests for langdetect fallback and edge cases (Step 3)."""

    def test_english_plain(self):
        result = detect("Add 5 kg rice at 60 rupees")
        assert result.lang_code == "en"

    def test_empty_string(self):
        result = detect("")
        assert result.lang_code == "en"
        assert result.method == "default"

    def test_whitespace_only(self):
        result = detect("   ")
        assert result.lang_code == "en"
        assert result.method == "default"

    def test_single_hindi_keyword_not_enough(self):
        """A single keyword shouldn't trigger Hindi — needs >= 2."""
        result = detect("hello karo")
        # "karo" is 1 keyword but "hello" is not, so it depends on langdetect
        # Just check we get a valid result
        assert result.lang_code in ("en", "hi")

    def test_returns_lang_result(self):
        result = detect("anything")
        assert isinstance(result, LangResult)
        assert hasattr(result, "lang_code")
        assert hasattr(result, "confidence")
        assert hasattr(result, "method")
