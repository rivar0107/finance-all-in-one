"""测试增强层适配器（Tushare / Alpaca / Finnhub / FMP / Twelve Data）"""

import os
from unittest import mock

import pandas as pd
import pytest

from sources.alpaca import Adapter as AlpacaAdapter
from sources.finnhub import Adapter as FinnhubAdapter
from sources.fmp import Adapter as FMPAdapter
from sources.tushare import Adapter as TushareAdapter
from sources.twelve_data import Adapter as TwelveDataAdapter


# ─── Tushare ───
class TestTushareAdapter:
    def test_is_available_without_key(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            assert TushareAdapter.is_available() is False

    @mock.patch("sources.tushare._pro")
    @mock.patch("sources.tushare._ts")
    def test_fetch_quote_mock(self, mock_ts, mock_pro):
        mock_pro.daily_basic.return_value = pd.DataFrame({"ts_code": ["600519.SH"], "pe": [28.5]})
        df = TushareAdapter.fetch_quote("600519")
        assert not df.empty
        assert "pe" in df.columns

    @mock.patch("sources.tushare._pro")
    @mock.patch("sources.tushare._ts")
    def test_fetch_kline_mock(self, mock_ts, mock_pro):
        mock_pro.daily.return_value = pd.DataFrame({
            "trade_date": ["20250101", "20250102"],
            "open": [100.0, 101.0],
            "close": [101.0, 102.0],
        })
        df = TushareAdapter.fetch_kline("600519")
        assert not df.empty
        assert "trade_date" in df.columns

    @mock.patch("sources.tushare._pro")
    @mock.patch("sources.tushare._ts")
    def test_fetch_financial_mock(self, mock_ts, mock_pro):
        mock_pro.income.return_value = pd.DataFrame({"ts_code": ["600519.SH"], "total_revenue": [1e9]})
        df = TushareAdapter.fetch_financial("600519", report_type="income")
        assert not df.empty

    def test_to_ts_code(self):
        assert TushareAdapter._to_ts_code("600519") == "600519.SH"
        assert TushareAdapter._to_ts_code("000001") == "000001.SZ"
        assert TushareAdapter._to_ts_code("sh600519") == "600519.SH"
        assert TushareAdapter._to_ts_code("600519.SH") == "600519.SH"


# ─── Alpaca ───
class TestAlpacaAdapter:
    def test_is_available_without_key(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            assert AlpacaAdapter.is_available() is False

    @mock.patch("sources.alpaca._get_alpaca")
    def test_fetch_quote_mock(self, mock_get_alpaca):
        mock_client = mock.Mock()
        mock_client.get_latest_quote.return_value = {"bp": 150.0, "ap": 150.5}
        mock_get_alpaca.return_value.REST.return_value = mock_client
        with mock.patch.dict(os.environ, {"ALPACA_API_KEY": "test", "ALPACA_SECRET_KEY": "test"}):
            df = AlpacaAdapter.fetch_quote("AAPL")
        assert not df.empty
        assert "bp" in df.columns

    @mock.patch("sources.alpaca._get_alpaca")
    def test_fetch_kline_mock(self, mock_get_alpaca):
        mock_bars = mock.Mock()
        mock_bars.df = pd.DataFrame({"open": [100.0], "close": [101.0]})
        mock_client = mock.Mock()
        mock_client.get_bars.return_value = mock_bars
        mock_get_alpaca.return_value.REST.return_value = mock_client
        with mock.patch.dict(os.environ, {"ALPACA_API_KEY": "test", "ALPACA_SECRET_KEY": "test"}):
            df = AlpacaAdapter.fetch_kline("AAPL")
        assert not df.empty
        assert "open" in df.columns


# ─── Finnhub ───
class TestFinnhubAdapter:
    def test_is_available_without_key(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            assert FinnhubAdapter.is_available() is False

    @mock.patch("sources.finnhub._client")
    @mock.patch("sources.finnhub._finnhub")
    def test_fetch_quote_mock(self, mock_fh, mock_client):
        mock_client.quote.return_value = {"c": 150.0, "d": 1.5, "dp": 1.01}
        df = FinnhubAdapter.fetch_quote("AAPL")
        assert not df.empty
        assert "c" in df.columns

    @mock.patch("sources.finnhub._client")
    @mock.patch("sources.finnhub._finnhub")
    def test_fetch_news_mock(self, mock_fh, mock_client):
        mock_client.company_news.return_value = [
            {"datetime": 1234567890, "headline": "Test News", "source": "Bloomberg"}
        ]
        df = FinnhubAdapter.fetch_news("AAPL")
        assert not df.empty
        assert "headline" in df.columns


# ─── FMP ───
class TestFMPAdapter:
    def test_is_available_without_key(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            assert FMPAdapter.is_available() is False

    @mock.patch("sources.fmp.requests.get")
    def test_fetch_quote_mock(self, mock_get):
        mock_get.return_value.json.return_value = [{"symbol": "AAPL", "price": 150.0}]
        mock_get.return_value.raise_for_status = mock.Mock()
        with mock.patch.dict(os.environ, {"FMP_API_KEY": "test_key"}):
            df = FMPAdapter.fetch_quote("AAPL")
        assert not df.empty
        assert "price" in df.columns

    @mock.patch("sources.fmp.requests.get")
    def test_fetch_financial_mock(self, mock_get):
        mock_get.return_value.json.return_value = [{"symbol": "AAPL", "revenue": 1e11}]
        mock_get.return_value.raise_for_status = mock.Mock()
        with mock.patch.dict(os.environ, {"FMP_API_KEY": "test_key"}):
            df = FMPAdapter.fetch_financial("AAPL", report_type="income")
        assert not df.empty
        assert "revenue" in df.columns

    def test_fetch_empty_on_error(self):
        # 无 Key 时应返回空 DataFrame
        with mock.patch.dict(os.environ, {}, clear=True):
            df = FMPAdapter.fetch_quote("AAPL")
            assert df.empty


# ─── Twelve Data ───
class TestTwelveDataAdapter:
    def test_is_available_without_key(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            assert TwelveDataAdapter.is_available() is False

    @mock.patch("sources.twelve_data._client")
    @mock.patch("sources.twelve_data._td")
    def test_fetch_quote_mock(self, mock_td, mock_client):
        mock_resp = mock.Mock()
        mock_resp.as_json.return_value = {"symbol": "AAPL", "close": "150.0"}
        mock_client.quote.return_value = mock_resp
        df = TwelveDataAdapter.fetch_quote("AAPL")
        assert not df.empty
        assert "close" in df.columns

    @mock.patch("sources.twelve_data._client")
    @mock.patch("sources.twelve_data._td")
    def test_fetch_kline_mock(self, mock_td, mock_client):
        mock_ts = mock.Mock()
        mock_ts.as_pandas.return_value = pd.DataFrame({"open": [100.0], "close": [101.0]})
        mock_client.time_series.return_value = mock_ts
        df = TwelveDataAdapter.fetch_kline("AAPL")
        assert not df.empty
        assert "open" in df.columns
