"""测试数据归一化"""

import pandas as pd
import pytest

from core.normalizer import normalize_kline, normalize_quote, normalize_financial


class TestNormalizeKline:
    def test_normalize_tencent_kline(self):
        raw = pd.DataFrame({
            "date": ["2025-01-01", "2025-01-02"],
            "open": [100.0, 101.0],
            "high": [102.0, 103.0],
            "low": [99.0, 100.0],
            "close": [101.0, 102.0],
            "volume": [10000, 20000],
        })
        result = normalize_kline(raw, "tencent")
        assert list(result.columns) == ["date", "open", "high", "low", "close", "volume"]
        assert len(result) == 2

    def test_normalize_yfinance_kline(self):
        raw = pd.DataFrame({
            "Date": ["2025-01-01", "2025-01-02"],
            "Open": [100.0, 101.0],
            "High": [102.0, 103.0],
            "Low": [99.0, 100.0],
            "Close": [101.0, 102.0],
            "Volume": [10000, 20000],
        })
        result = normalize_kline(raw, "yfinance")
        assert "date" in result.columns
        assert "open" in result.columns
        assert "close" in result.columns

    def test_empty_dataframe(self):
        result = normalize_kline(pd.DataFrame(), "tencent")
        assert result.empty
        assert list(result.columns) == ["date", "open", "high", "low", "close", "volume"]

    def test_pct_chg_calculation(self):
        raw = pd.DataFrame({
            "date": ["2025-01-01"],
            "open": [100.0],
            "high": [102.0],
            "low": [99.0],
            "close": [101.0],
            "volume": [10000],
            "pre_close": [100.0],
        })
        result = normalize_kline(raw, "ftshare")
        assert "pct_chg" in result.columns
        assert result["pct_chg"].iloc[0] == 1.0


class TestNormalizeQuote:
    def test_normalize_tencent_quote(self):
        raw = pd.DataFrame({
            "name": ["贵州茅台"],
            "price": ["1775.00"],
            "volume": ["12345"],
        })
        result = normalize_quote(raw, "tencent")
        assert result["price"].iloc[0] == 1775.0
        assert result["volume"].iloc[0] == 12345.0

    def test_empty_quote(self):
        result = normalize_quote(pd.DataFrame(), "sina")
        assert result.empty


class TestNormalizeFinancial:
    def test_column_snake_case(self):
        raw = pd.DataFrame({
            "营业收入": [100, 200],
            "Net Profit": [10, 20],
            "TotalAssets": [500, 600],
        })
        result = normalize_financial(raw, "ftshare")
        assert "营业收入" in result.columns  # 中文保持不变
        assert "net_profit" in result.columns
        assert "total_assets" in result.columns
