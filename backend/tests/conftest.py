"""Shared test fixtures — mock Supabase and LLM."""
import sys
import os
import pytest
from unittest.mock import MagicMock, patch

# Ensure the backend directory is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


class MockSupabaseResponse:
    """Simulates a Supabase API response."""

    def __init__(self, data=None, error=None):
        self.data = data or []
        self.error = error


class MockSupabaseQuery:
    """Simulates a Supabase query builder chain."""

    def __init__(self, data=None):
        self._data = data or []

    def select(self, *args, **kwargs):
        return self

    def eq(self, *args, **kwargs):
        return self

    def gte(self, *args, **kwargs):
        return self

    def lte(self, *args, **kwargs):
        return self

    def or_(self, *args, **kwargs):
        return self

    def order(self, *args, **kwargs):
        return self

    def limit(self, *args, **kwargs):
        return self

    def insert(self, *args, **kwargs):
        return self

    def upsert(self, *args, **kwargs):
        return self

    def update(self, *args, **kwargs):
        return self

    def delete(self):
        return self

    def in_(self, *args, **kwargs):
        return self

    def execute(self):
        return MockSupabaseResponse(data=self._data)


class MockSupabaseClient:
    """Simulates a Supabase client."""

    def __init__(self, data_map=None):
        self._data_map = data_map or {}

    def table(self, name):
        return MockSupabaseQuery(data=self._data_map.get(name, []))


@pytest.fixture
def mock_supabase():
    """Provides a mock Supabase client that can be configured per-test."""
    client = MockSupabaseClient()
    with patch("db.get_supabase_client", return_value=client):
        yield client


@pytest.fixture
def mock_supabase_with_data():
    """Factory fixture: pass a data_map to seed specific tables."""

    def _factory(data_map):
        client = MockSupabaseClient(data_map=data_map)
        patcher = patch("db.get_supabase_client", return_value=client)
        mock = patcher.start()
        return client, patcher

    return _factory
