"""Financial Modeling Prep (FMP) 适配器

需配置 FMP_API_KEY（fmp.io 注册免费获取）。
覆盖：美股实时行情、财务报表、关键指标
"""

import os
import pandas as pd
import requests

from config import REQUEST_TIMEOUT


class FMPAdapter:
    """FMP 数据适配器"""

    name = "fmp"
    requires_key = True

    BASE_URL = "https://financialmodelingprep.com/api/v3"

    @classmethod
    def _get_api_key(cls) -> str:
        return os.environ.get("FMP_API_KEY", "")

    @classmethod
    def is_available(cls) -> bool:
        return bool(cls._get_api_key())

    @classmethod
    def _request(cls, endpoint: str, params: dict = None):
        """发送 GET 请求。"""
        key = cls._get_api_key()
        url = f"{cls.BASE_URL}{endpoint}"
        query = dict(params) if params else {}
        query["apikey"] = key
        resp = requests.get(url, params=query, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        return resp.json()

    @classmethod
    def fetch_quote(cls, symbol: str, **kwargs) -> pd.DataFrame:
        """获取实时行情。"""
        try:
            data = cls._request(f"/quote/{symbol.upper()}")
            return pd.DataFrame(data) if isinstance(data, list) else pd.DataFrame()
        except Exception:
            return pd.DataFrame()

    @classmethod
    def fetch_kline(
        cls,
        symbol: str,
        period: str = "daily",
        limit: int = 50,
        **kwargs,
    ) -> pd.DataFrame:
        """获取历史价格。"""
        try:
            path_map = {
                "daily": f"/historical-price-full/{symbol.upper()}",
                "weekly": f"/historical-price-full/{symbol.upper()}?serietype=line",
                "monthly": f"/historical-price-full/{symbol.upper()}?serietype=line",
            }
            path = path_map.get(period, path_map["daily"])
            data = cls._request(path)
            hist = data.get("historical", []) if isinstance(data, dict) else []
            df = pd.DataFrame(hist)
            if not df.empty:
                df = df.head(limit)
            return df
        except Exception:
            return pd.DataFrame()

    @classmethod
    def fetch_financial(cls, symbol: str, report_type: str = "income", **kwargs) -> pd.DataFrame:
        """获取财务报表。"""
        try:
            type_map = {
                "income": f"/income-statement/{symbol.upper()}",
                "balance": f"/balance-sheet-statement/{symbol.upper()}",
                "cash_flow": f"/cash-flow-statement/{symbol.upper()}",
            }
            endpoint = type_map.get(report_type)
            if not endpoint:
                return pd.DataFrame()
            data = cls._request(endpoint)
            return pd.DataFrame(data) if isinstance(data, list) else pd.DataFrame()
        except Exception:
            return pd.DataFrame()

    @classmethod
    def fetch_fundamentals(cls, symbol: str, **kwargs) -> pd.DataFrame:
        """获取关键指标。"""
        try:
            data = cls._request(f"/key-metrics/{symbol.upper()}")
            return pd.DataFrame(data) if isinstance(data, list) else pd.DataFrame()
        except Exception:
            return pd.DataFrame()

    @classmethod
    def fetch(cls, data_type: str, **kwargs) -> pd.DataFrame:
        if "kline" in data_type:
            return cls.fetch_kline(**kwargs)
        if "quote" in data_type:
            return cls.fetch_quote(**kwargs)
        if data_type in ("stock_financial", "us_fundamentals"):
            return cls.fetch_financial(**kwargs)
        if data_type == "us_fundamentals":
            return cls.fetch_fundamentals(**kwargs)
        return pd.DataFrame()


Adapter = FMPAdapter
