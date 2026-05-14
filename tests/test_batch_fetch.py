"""测试 batch_fetch_with_fallback"""

from unittest import mock

import pandas as pd
import pytest

from core.fetcher import batch_fetch_with_fallback, get_cache
from core.result import FetchResult


class DummyAdapter:
    name = "dummy"

    @classmethod
    def is_available(cls):
        return True

    @classmethod
    def fetch_quote(cls, **kwargs):
        symbol = kwargs.get("symbol", "")
        return pd.DataFrame({"symbol": [symbol], "price": [100.0]})


class BrokenAdapter:
    name = "broken"

    @classmethod
    def is_available(cls):
        return True

    @classmethod
    def fetch_quote(cls, **kwargs):
        raise ConnectionError("模拟网络错误")


class TestBatchFetch:
    def setup_method(self):
        get_cache().clear()

    @mock.patch("core.fetcher._load_adapter")
    def test_batch_two_symbols(self, mock_load):
        mock_load.return_value = DummyAdapter
        results = batch_fetch_with_fallback(
            symbols=["600519", "000001"],
            data_type="stock_quote",
            market="a_share",
            max_workers=1,
            use_cache=False,
        )
        assert len(results) == 2
        assert all(isinstance(r, FetchResult) for r in results)
        assert results[0].data.iloc[0]["symbol"] == "600519"
        assert results[1].data.iloc[0]["symbol"] == "000001"

    @mock.patch("core.fetcher._load_adapter")
    def test_batch_mixed_success_failure(self, mock_load):
        """部分成功、部分失败时，失败项返回空 DataFrame 但不抛异常。"""

        def side_effect(name):
            # 第一次加载 broken，第二次加载 dummy
            if mock_load.call_count == 1:
                return BrokenAdapter
            return DummyAdapter

        mock_load.side_effect = side_effect

        with mock.patch("core.fetcher.Router.get_sources", return_value=["broken", "dummy"]):
            results = batch_fetch_with_fallback(
                symbols=["600519", "000001"],
                data_type="stock_quote",
                market="a_share",
                max_workers=1,
                use_cache=False,
            )
            assert len(results) == 2
            # 600519 第一次调用会失败（broken），然后降级到 dummy 成功
            assert not results[0].data.empty
            # 000001 第二次调用直接加载 dummy 成功
            assert not results[1].data.empty

    def test_batch_empty_symbols(self):
        results = batch_fetch_with_fallback(
            symbols=[],
            data_type="stock_quote",
            market="a_share",
            use_cache=False,
        )
        assert results == []

    @mock.patch("core.fetcher._load_adapter")
    def test_batch_concurrent(self, mock_load):
        """并发模式（max_workers > 1）能正常返回。"""
        mock_load.return_value = DummyAdapter
        results = batch_fetch_with_fallback(
            symbols=["600519", "000001", "00700"],
            data_type="stock_quote",
            market="a_share",
            max_workers=2,
            use_cache=False,
        )
        assert len(results) == 3
        symbols = [r.data.iloc[0]["symbol"] for r in results]
        assert symbols == ["600519", "000001", "00700"]
