"""端到端真实环境验证

直接调用各数据源的真实接口，验证连通性和字段完整性。
网络不通或源不可用时自动跳过，不阻塞 CI。
"""

import socket

import pytest
import requests

from core.fetcher import _load_adapter


def _has_internet() -> bool:
    try:
        socket.create_connection(("8.8.8.8", 53), timeout=3)
        return True
    except OSError:
        return False


def _skip_unstable_source(exc: Exception, source_name: str) -> None:
    transient_errors = (
        requests.exceptions.ConnectionError,
        requests.exceptions.ChunkedEncodingError,
        requests.exceptions.Timeout,
    )
    if isinstance(exc, transient_errors) or type(exc).__name__ == "YFRateLimitError":
        pytest.skip(f"{source_name} 外部接口暂不可用: {type(exc).__name__}")
    raise exc


HAS_INTERNET = _has_internet()


# ─── HTTP 直连型 ───
@pytest.mark.skipif(not HAS_INTERNET, reason="无网络连接")
class TestTencentLive:
    def test_fetch_quote_a_share(self):
        adapter = _load_adapter("tencent")
        df = adapter.fetch_quote("600519")
        assert not df.empty, "腾讯 A 股实时行情返回空"
        assert "price" in df.columns or "name" in df.columns

    def test_fetch_kline_a_share(self):
        adapter = _load_adapter("tencent")
        df = adapter.fetch_kline("600519", limit=5)
        assert not df.empty, "腾讯 A 股 K 线返回空"
        assert "date" in df.columns

    def test_fetch_quote_us(self):
        adapter = _load_adapter("tencent")
        df = adapter.fetch_quote("AAPL", market="us")
        # 美股可能不支持，允许跳过
        if df.empty:
            pytest.skip("腾讯美股行情暂不可用")
        assert "price" in df.columns or "name" in df.columns


@pytest.mark.skipif(not HAS_INTERNET, reason="无网络连接")
class TestSinaLive:
    def test_fetch_quote_a_share(self):
        adapter = _load_adapter("sina")
        df = adapter.fetch_quote("600519")
        assert not df.empty, "新浪 A 股实时行情返回空"


@pytest.mark.skipif(not HAS_INTERNET, reason="无网络连接")
class TestSohuLive:
    def test_fetch_kline_a_share(self):
        adapter = _load_adapter("sohu")
        df = adapter.fetch_kline("600519", limit=5)
        assert not df.empty, "搜狐 A 股 K 线返回空"
        assert "date" in df.columns


@pytest.mark.skipif(not HAS_INTERNET, reason="无网络连接")
class TestEastmoneyIntradayLive:
    def test_fetch_intraday(self):
        adapter = _load_adapter("eastmoney_intraday")
        try:
            df = adapter.fetch_intraday("600519")
        except Exception as e:
            _skip_unstable_source(e, "东方财富分时")
        # 东方财富分时接口不稳定，允许跳过
        if df.empty:
            pytest.skip("东方财富分时接口暂不可用")
        assert "time" in df.columns or "price" in df.columns


# ─── 库封装型（仅在库已安装时测试）───
class TestAkshareLive:
    def setup_method(self):
        adapter = _load_adapter("akshare")
        if adapter is None or not adapter.is_available():
            pytest.skip("akshare 未安装或不可用")
        self.adapter = adapter

    @pytest.mark.skipif(not HAS_INTERNET, reason="无网络连接")
    def test_fetch_quote_a_share(self):
        try:
            df = self.adapter.fetch_quote("600519")
        except Exception as e:
            _skip_unstable_source(e, "akshare A 股实时行情")
        assert not df.empty, "akshare A 股实时行情返回空"

    @pytest.mark.skipif(not HAS_INTERNET, reason="无网络连接")
    def test_fetch_kline_a_share(self):
        try:
            df = self.adapter.fetch_kline("600519", limit=5)
        except Exception as e:
            _skip_unstable_source(e, "akshare A 股 K 线")
        assert not df.empty, "akshare A 股 K 线返回空"


class TestEfinanceLive:
    def setup_method(self):
        adapter = _load_adapter("efinance")
        if adapter is None or not adapter.is_available():
            pytest.skip("efinance 未安装或不可用")
        self.adapter = adapter

    @pytest.mark.skipif(not HAS_INTERNET, reason="无网络连接")
    def test_fetch_quote_a_share(self):
        df = self.adapter.fetch_quote("600519")
        assert not df.empty, "efinance A 股实时行情返回空"


class TestYfinanceLive:
    def setup_method(self):
        adapter = _load_adapter("yfinance")
        if adapter is None or not adapter.is_available():
            pytest.skip("yfinance 未安装或不可用")
        self.adapter = adapter

    @pytest.mark.skipif(not HAS_INTERNET, reason="无网络连接")
    def test_fetch_kline_us(self):
        try:
            df = self.adapter.fetch_kline("AAPL", market="us", limit=5)
        except Exception as e:
            _skip_unstable_source(e, "yfinance 美股 K 线")
        assert not df.empty, "yfinance 美股 K 线返回空"


# ─── 增强层（仅在 Key 配置时测试）───
class TestTushareLive:
    def setup_method(self):
        adapter = _load_adapter("tushare")
        if adapter is None or not adapter.is_available():
            pytest.skip("tushare 未安装或 Key 未配置")
        self.adapter = adapter

    @pytest.mark.skipif(not HAS_INTERNET, reason="无网络连接")
    def test_fetch_quote(self):
        df = self.adapter.fetch_quote("600519")
        assert not df.empty, "tushare 实时行情返回空"


class TestFmplive:
    def setup_method(self):
        adapter = _load_adapter("fmp")
        if adapter is None or not adapter.is_available():
            pytest.skip("FMP Key 未配置")
        self.adapter = adapter

    @pytest.mark.skipif(not HAS_INTERNET, reason="无网络连接")
    def test_fetch_quote(self):
        df = self.adapter.fetch_quote("AAPL")
        assert not df.empty, "FMP 美股行情返回空"
