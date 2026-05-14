"""测试 TTLCache"""

import time

import pytest

from core.cache import TTLCache


class TestTTLCache:
    def test_get_set(self):
        cache = TTLCache(default_ttl=60)
        cache.set("value1", "key", data_type="stock_quote")
        assert cache.get("key", data_type="stock_quote") == "value1"

    def test_ttl_expiration(self):
        cache = TTLCache(default_ttl=-1)
        cache.set("value1", "key")
        assert cache.get("key") is None

    def test_different_data_types(self):
        cache = TTLCache()
        cache.set("v1", "k", data_type="stock_quote")
        cache.set("v2", "k", data_type="stock_kline")
        assert cache.get("k", data_type="stock_quote") == "v1"
        assert cache.get("k", data_type="stock_kline") == "v2"

    def test_clear(self):
        cache = TTLCache()
        cache.set("v1", "k", data_type="stock_quote")
        cache.clear()
        assert cache.get("k", data_type="stock_quote") is None

    def test_stats(self):
        cache = TTLCache(default_ttl=300)
        cache.set("v1", "k1", data_type="stock_quote")
        cache.set("v2", "k2", data_type="stock_kline")
        stats = cache.stats()
        assert stats["total_keys"] == 2
        assert stats["valid_keys"] == 2
