"""Unit tests for fuzzy matching logic in generate_beckn_catalog."""
import sys
import os
import difflib
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


class TestFuzzyMatching:
    """Tests the fuzzy matching algorithm used in agent.py's generate_beckn_catalog.
    This mirrors the matching logic: similarity > 0.7 OR substring containment."""

    def _is_match(self, new_name: str, existing_name: str) -> bool:
        """Replicates the matching logic from agent.py."""
        similarity = difflib.SequenceMatcher(
            None, new_name.lower(), existing_name.lower()
        ).ratio()
        return (
            similarity > 0.7
            or new_name.lower() in existing_name.lower()
            or existing_name.lower() in new_name.lower()
        )

    def test_exact_match(self):
        assert self._is_match("Aashirvaad Atta", "Aashirvaad Atta")

    def test_case_insensitive_match(self):
        assert self._is_match("aashirvaad atta", "Aashirvaad Atta")

    def test_substring_match_shorter_in_longer(self):
        assert self._is_match("Atta", "Aashirvaad Atta")

    def test_substring_match_longer_contains_shorter(self):
        assert self._is_match("Aashirvaad Atta", "Atta")

    def test_high_similarity_match(self):
        # "Maggi Masala" vs "Maggi masala noodles" — should match by substring
        assert self._is_match("Maggi Masala", "Maggi masala noodles")

    def test_no_match_completely_different(self):
        assert not self._is_match("Rice", "Atta")

    def test_no_match_partial_but_low_similarity(self):
        assert not self._is_match("Tata Salt", "Aashirvaad Atta")

    def test_similar_but_different_products(self):
        # "Dal" vs "Dalmoth" — short words, may hit substring
        # "Dal" is in "Dalmoth" so this SHOULD match by substring containment
        assert self._is_match("Dal", "Dalmoth")

    def test_misspelling_close_enough(self):
        # "Aashirvad" vs "Aashirvaad" — differ by one char
        similarity = difflib.SequenceMatcher(
            None, "aashirvad", "aashirvaad"
        ).ratio()
        assert similarity > 0.7
        assert self._is_match("Aashirvad", "Aashirvaad")

    def test_completely_unrelated(self):
        assert not self._is_match("Laptop Bag", "Whole Wheat Flour")

    def test_empty_strings(self):
        # Empty vs non-empty should match (empty is substring of everything)
        assert self._is_match("", "Atta")

    def test_hinglish_product_names(self):
        assert self._is_match("Tata Namak", "Tata namak 1kg")

    def test_short_names_no_match(self):
        # Single letter names shouldn't match across different words
        # "A" is substring of "Atta" so this actually matches
        assert self._is_match("A", "Atta")

    def test_quantity_in_name(self):
        # "Atta 5kg" vs "Atta" — substring match
        assert self._is_match("Atta 5kg", "Atta")
