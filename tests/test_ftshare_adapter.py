"""测试 FTShare 适配器独有数据能力"""

from unittest import mock

import pandas as pd
import pytest

from sources.ftshare import FTShareAdapter


class TestFTShareUniqueCapabilities:
    """FTShare 独有数据：股东、质押、股本变动、业绩、可转债"""

    @mock.patch("sources.ftshare.requests.get")
    def test_fetch_stock_holders_ten(self, mock_get):
        mock_get.return_value.json.return_value = [
            {"holder_name": "贵州茅台集团", "hold_ratio": 54.07}
        ]
        df = FTShareAdapter.fetch_stock_holders("600519", holder_type="ten")
        assert not df.empty
        assert "holder_name" in df.columns

    @mock.patch("sources.ftshare.requests.get")
    def test_fetch_stock_holders_ften(self, mock_get):
        mock_get.return_value.json.return_value = [
            {"holder_name": "香港中央结算", "hold_ratio": 6.82}
        ]
        df = FTShareAdapter.fetch_stock_holders("600519", holder_type="ften")
        assert not df.empty

    @mock.patch("sources.ftshare.requests.get")
    def test_fetch_stock_holders_nums(self, mock_get):
        mock_get.return_value.json.return_value = [
            {"date": "2025-03-31", "holder_nums": 152300}
        ]
        df = FTShareAdapter.fetch_stock_holders("600519", holder_type="nums")
        assert not df.empty

    @mock.patch("sources.ftshare.requests.get")
    def test_fetch_pledge_market_summary(self, mock_get):
        mock_get.return_value.json.return_value = [
            {"date": "2025-05-12", "pledge_count": 1234}
        ]
        df = FTShareAdapter.fetch_pledge()
        assert not df.empty
        mock_get.assert_called_once()
        assert "pledge-summary" in mock_get.call_args[0][0]

    @mock.patch("sources.ftshare.requests.get")
    def test_fetch_pledge_single_stock(self, mock_get):
        mock_get.return_value.json.return_value = [
            {"pledgor": "张三", "pledge_amount": 5000000}
        ]
        df = FTShareAdapter.fetch_pledge("600519")
        assert not df.empty
        assert "pledge-detail" in mock_get.call_args[0][0]

    @mock.patch("sources.ftshare.requests.get")
    def test_fetch_share_change(self, mock_get):
        mock_get.return_value.json.return_value = [
            {"chg_date": "2025-01-15", "chg_reason": "增发", "chg_amount": 1000000}
        ]
        df = FTShareAdapter.fetch_share_change("600519")
        assert not df.empty
        assert "chg_reason" in df.columns

    @mock.patch("sources.ftshare.requests.get")
    def test_fetch_performance_single(self, mock_get):
        mock_get.return_value.json.return_value = [
            {"report_date": "2025-03-31", "revenue": 1500000000}
        ]
        df = FTShareAdapter.fetch_performance("600519", mode="single")
        assert not df.empty
        assert "stock-performance-express" in mock_get.call_args[0][0]

    @mock.patch("sources.ftshare.requests.get")
    def test_fetch_performance_all(self, mock_get):
        mock_get.return_value.json.return_value = [
            {"stock_code": "600519.SH", "report_date": "2025-03-31"}
        ]
        df = FTShareAdapter.fetch_performance(mode="all", year=2025, report_type="q1")
        assert not df.empty

    @mock.patch("sources.ftshare.requests.get")
    def test_fetch_performance_forecast_single(self, mock_get):
        mock_get.return_value.json.return_value = [
            {"report_date": "2025-03-31", "forecast_type": "预增"}
        ]
        df = FTShareAdapter.fetch_performance_forecast("600519", mode="single")
        assert not df.empty

    @mock.patch("sources.ftshare.requests.get")
    def test_fetch_cb_base(self, mock_get):
        mock_get.return_value.json.return_value = [
            {"bond_name": "茅台转债", "conversion_price": 150.0}
        ]
        df = FTShareAdapter.fetch_cb_base("110055")
        assert not df.empty
        assert "cb-base-data" in mock_get.call_args[0][0]

    @mock.patch("sources.ftshare.requests.get")
    def test_fetch_cb_list(self, mock_get):
        mock_get.return_value.json.return_value = [
            {"bond_code": "110055", "bond_name": "茅台转债"}
        ]
        df = FTShareAdapter.fetch_cb_list()
        assert not df.empty
        assert "cb-lists" in mock_get.call_args[0][0]

    # ─── fetch 通用回退 ───
    @mock.patch("sources.ftshare.requests.get")
    def test_fetch_generic_stock_holders(self, mock_get):
        mock_get.return_value.json.return_value = [{"holder_name": "集团"}]
        df = FTShareAdapter.fetch("stock_holders", symbol="600519")
        assert not df.empty

    @mock.patch("sources.ftshare.requests.get")
    def test_fetch_generic_cb_list(self, mock_get):
        mock_get.return_value.json.return_value = [{"bond_code": "110055"}]
        df = FTShareAdapter.fetch("cb_list")
        assert not df.empty

    @mock.patch("sources.ftshare.requests.get")
    def test_fetch_empty_on_error(self, mock_get):
        mock_get.side_effect = ConnectionError("模拟网络错误")
        df = FTShareAdapter.fetch_stock_holders("600519")
        assert df.empty

    @mock.patch("sources.ftshare.requests.get")
    def test_fetch_empty_on_non_200(self, mock_get):
        mock_get.return_value.raise_for_status.side_effect = Exception("500")
        df = FTShareAdapter.fetch_pledge("600519")
        assert df.empty
