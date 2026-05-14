"""测试 fetcher 降级逻辑"""

from unittest import mock

import pandas as pd
import pytest

from core.exceptions import SourceExhaustedError
from core.fetcher import _normalize, _resolve_method_name, fetch_with_fallback, get_cache
from core.result import FetchResult


class DummyAdapter:
    name = "dummy"

    @classmethod
    def is_available(cls):
        return True

    @classmethod
    def fetch_quote(cls, **kwargs):
        return pd.DataFrame({"price": [100.0]})

    @classmethod
    def fetch_kline(cls, **kwargs):
        return pd.DataFrame({
            "date": ["2025-01-01"],
            "open": [100.0],
            "close": [101.0],
        })

    @classmethod
    def fetch(cls, **kwargs):
        return pd.DataFrame({"data": [1]})


class BrokenAdapter:
    name = "broken"

    @classmethod
    def is_available(cls):
        return True

    @classmethod
    def fetch_quote(cls, **kwargs):
        raise ConnectionError("模拟网络错误")


class TestResolveMethodName:
    def test_stock_quote(self):
        assert _resolve_method_name("stock_quote") == "fetch_quote"

    def test_stock_kline(self):
        assert _resolve_method_name("stock_kline") == "fetch_kline"

    def test_stock_financial(self):
        assert _resolve_method_name("stock_financial") == "fetch_financial"

    def test_stock_holders(self):
        assert _resolve_method_name("stock_holders") == "fetch_stock_holders"

    def test_stock_pledge(self):
        assert _resolve_method_name("stock_pledge") == "fetch_pledge"

    def test_share_change(self):
        assert _resolve_method_name("share_change") == "fetch_share_change"

    def test_performance_express(self):
        assert _resolve_method_name("performance_express") == "fetch_performance"

    def test_performance_forecast(self):
        assert _resolve_method_name("performance_forecast") == "fetch_performance_forecast"

    def test_cb_base(self):
        assert _resolve_method_name("cb_base") == "fetch_cb_base"

    def test_cb_list(self):
        assert _resolve_method_name("cb_list") == "fetch_cb_list"

    def test_unknown(self):
        assert _resolve_method_name("unknown_type") == "fetch"


class TestNormalize:
    def test_list_input(self):
        result = _normalize([{"a": 1}, {"a": 2}], "tencent", "stock_quote")
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 2

    def test_dict_input(self):
        result = _normalize({"a": 1}, "tencent", "stock_quote")
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 1


class TestFetchWithFallback:
    def setup_method(self):
        get_cache().clear()

    @mock.patch("core.fetcher._load_adapter")
    def test_success_first_source(self, mock_load):
        mock_load.return_value = DummyAdapter
        result = fetch_with_fallback(
            symbol="600519",
            data_type="stock_quote",
            market="a_share",
            use_cache=False,
        )
        assert isinstance(result, FetchResult)
        assert result.source == "tencent"  # mock 让 _load_adapter("tencent") 返回 DummyAdapter
        assert not result.data.empty

    @mock.patch("core.fetcher._load_adapter")
    def test_fallback_to_second_source(self, mock_load):
        # 第一次返回 BrokenAdapter，第二次返回 DummyAdapter
        call_count = [0]

        def side_effect(name):
            call_count[0] += 1
            if call_count[0] == 1:
                return BrokenAdapter
            return DummyAdapter

        mock_load.side_effect = side_effect

        # 临时修改路由表，让 broken 和 dummy 都出现在列表中
        with mock.patch("core.fetcher.Router.get_sources", return_value=["broken", "dummy"]):
            result = fetch_with_fallback(
                symbol="600519",
                data_type="stock_quote",
                market="a_share",
                use_cache=False,
            )
            assert result.source == "dummy"
            assert len(result.warnings) > 0
            assert "降级" in result.warnings[0]

    @mock.patch("core.fetcher._load_adapter")
    def test_all_sources_failed(self, mock_load):
        mock_load.return_value = BrokenAdapter
        with mock.patch("core.fetcher.Router.get_sources", return_value=["broken"]):
            with pytest.raises(SourceExhaustedError):
                fetch_with_fallback(
                    symbol="600519",
                    data_type="stock_quote",
                    market="a_share",
                    use_cache=False,
                )

    @mock.patch("core.fetcher._load_adapter")
    def test_cache_hit(self, mock_load):
        mock_load.return_value = DummyAdapter
        # 第一次调用
        r1 = fetch_with_fallback(
            symbol="600519",
            data_type="stock_quote",
            market="a_share",
            use_cache=True,
        )
        # 第二次调用应命中缓存
        r2 = fetch_with_fallback(
            symbol="600519",
            data_type="stock_quote",
            market="a_share",
            use_cache=True,
        )
        assert r2.cached is True
        assert r1.source == r2.source
