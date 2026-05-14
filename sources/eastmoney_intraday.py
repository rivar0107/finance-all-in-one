"""东方财富分时适配器 (push2.eastmoney.com)

HTTP 直连型，分钟级粒度，含集合竞价数据。
覆盖：A 股/指数日内分时
"""

from typing import Optional

import pandas as pd
import requests

from config import REQUEST_TIMEOUT


class EastmoneyIntradayAdapter:
    """东方财富分时数据适配器"""

    name = "eastmoney_intraday"
    requires_key = False

    BASE_URL = "https://push2.eastmoney.com/api/qt/stock/trends2/get"

    @classmethod
    def is_available(cls) -> bool:
        return True

    @classmethod
    def _to_secid(cls, symbol: str) -> str:
        """转换为东方财富 secid：1.600519（沪市）、0.000858（深市）。"""
        s = str(symbol).strip()
        if s.lower().startswith("sh"):
            return f"1.{s[2:]}"
        elif s.lower().startswith("sz"):
            return f"0.{s[2:]}"
        s = s.zfill(6)
        if s.startswith(("6", "68", "88", "51", "50", "56", "58", "11", "12")):
            return f"1.{s}"
        return f"0.{s}"

    @classmethod
    def fetch_intraday(
        cls,
        symbol: str,
        market: str = "a_share",
        **kwargs,
    ) -> pd.DataFrame:
        """获取日内分时数据。"""
        secid = cls._to_secid(symbol)

        params = {
            "secid": secid,
            "fields1": "f1,f2,f3,f4,f5,f6,f7,f8,f9,f10,f11,f12,f13",
            "fields2": "f51,f52,f53,f54,f55,f56,f57,f58",
            "iscr": "0",
        }
        resp = requests.get(cls.BASE_URL, params=params, timeout=REQUEST_TIMEOUT)
        data = resp.json()

        # 返回格式: {"data": {"trends": ["09:30,open,price,high,low,volume,amount,avg", ...]}}
        trends = data.get("data", {}).get("trends", [])
        rows = []
        for line in trends:
            parts = line.split(",")
            if len(parts) >= 5:
                rows.append(
                    {
                        "time": parts[0],
                        "open": parts[1],
                        "price": parts[2],
                        "high": parts[3],
                        "low": parts[4],
                        "volume": parts[5] if len(parts) > 5 else None,
                        "amount": parts[6] if len(parts) > 6 else None,
                        "avg": parts[7] if len(parts) > 7 else None,
                    }
                )

        return pd.DataFrame(rows)

    @classmethod
    def fetch_kline(cls, **kwargs) -> pd.DataFrame:
        """东方财富分时接口不提供 K 线。"""
        return pd.DataFrame()

    @classmethod
    def fetch_quote(cls, **kwargs) -> pd.DataFrame:
        """东方财富分时接口不提供实时行情。"""
        return pd.DataFrame()


Adapter = EastmoneyIntradayAdapter
