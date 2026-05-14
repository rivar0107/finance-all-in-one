"""测试 Router"""

import os
from unittest import mock

import pytest

from core.router import Router


class TestRouter:
    def test_route_a_share_quote(self):
        sources = Router.get_sources("stock_quote", "a_share")
        assert sources[0] == "tencent"
        assert "sina" in sources

    def test_route_a_share_kline(self):
        sources = Router.get_sources("stock_kline", "a_share")
        assert sources[0] == "ftshare"
        assert "tencent" in sources

    def test_route_a_share_minute_kline(self):
        sources = Router.get_sources("stock_minute_kline", "a_share")
        assert sources[0] == "ths"

    def test_route_a_share_depth(self):
        sources = Router.get_sources("stock_depth", "a_share")
        assert sources[0] == "ths"
        assert "mootdx" in sources

    def test_route_a_share_ticks(self):
        sources = Router.get_sources("stock_ticks", "a_share")
        assert sources[0] == "mootdx"

    def test_route_us_quote_without_key(self):
        sources = Router.get_sources("stock_quote", "us")
        assert sources[0] == "tencent"
        assert "sina" in sources

    def test_route_us_quote_with_alpaca_key(self):
        with mock.patch.dict(os.environ, {"ALPACA_API_KEY": "test_key"}):
            sources = Router.get_sources("stock_quote", "us")
            assert sources[0] == "alpaca"
            assert "tencent" in sources

    def test_resolve_market_a_share(self):
        assert Router.resolve_market("600519") == "a_share"
        assert Router.resolve_market("000001") == "a_share"
        assert Router.resolve_market("sh600519") == "a_share"

    def test_resolve_market_hk(self):
        assert Router.resolve_market("00700") == "hk"
        assert Router.resolve_market("hk00700") == "hk"

    def test_resolve_market_us(self):
        assert Router.resolve_market("AAPL") == "us"
        assert Router.resolve_market("TSLA") == "us"

    def test_resolve_data_type_quote(self):
        assert Router.resolve_data_type("茅台今天多少钱") == "stock_quote"
        assert Router.resolve_data_type("查询实时行情") == "stock_quote"

    def test_resolve_data_type_kline(self):
        assert Router.resolve_data_type("近30天K线") == "stock_kline"
        assert Router.resolve_data_type("历史走势") == "stock_kline"

    def test_resolve_data_type_financial(self):
        assert Router.resolve_data_type("资产负债表") == "stock_financial"

    def test_resolve_data_type_macro(self):
        assert Router.resolve_data_type("中国CPI") == "china_macro"
