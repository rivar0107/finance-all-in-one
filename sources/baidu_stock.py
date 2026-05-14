"""百度股市通适配器 (gupiao.baidu.com)

HTTP 直连型，支持前复权/后复权/不复权。
覆盖：A 股日 K 线
"""

from typing import Optional

import pandas as pd
import requests

from config import REQUEST_TIMEOUT


class BaiduAdapter:
    """百度股市通数据适配器"""

    name = "baidu_stock"
    requires_key = False

    BASE_URL = "https://gupiao.baidu.com/api/stocks/stockdaybar"

    @classmethod
    def is_available(cls) -> bool:
        return True

    @classmethod
    def _to_baidu_code(cls, symbol: str, market: str = "a_share") -> str:
        """转换为百度代码格式：sh600519 / sz000001。"""
        s = str(symbol).strip().lower()
        if s.startswith(("sh", "sz")):
            return s
        s = s.zfill(6)
        if s.startswith(("6", "68", "88", "51", "50", "56", "58", "11", "12")):
            return f"sh{s}"
        return f"sz{s}"

    @classmethod
    def fetch_kline(
        cls,
        symbol: str,
        market: str = "a_share",
        period: str = "daily",
        limit: int = 50,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        **kwargs,
    ) -> pd.DataFrame:
        """获取日 K 线（支持复权）。"""
        code = cls._to_baidu_code(symbol, market)

        # 复权类型
        adjust = kwargs.get("adjust", "front")  # front / no / hfq
        fq_map = {"front": "front", "qfq": "front", "no": "no", "hfq": "hfq", "back": "hfq"}
        fq_type = fq_map.get(adjust, "front")

        params = {
            "stock_code": code,
            "count": limit,
            "fq_type": fq_type,
        }
        resp = requests.get(cls.BASE_URL, params=params, timeout=REQUEST_TIMEOUT)
        data = resp.json()

        # 百度返回格式: {"mashData": [{"date": "20250101", "kline": {"open": 100, "high": 102, "low": 99, "close": 101, "volume": 12345}, "ma5": {...}}, ...]}
        mash_data = data.get("mashData", [])
        rows = []
        for item in mash_data:
            kline = item.get("kline", {})
            if kline:
                rows.append(
                    {
                        "date": item.get("date"),
                        "open": kline.get("open"),
                        "high": kline.get("high"),
                        "low": kline.get("low"),
                        "close": kline.get("close"),
                        "volume": kline.get("volume"),
                    }
                )

        return pd.DataFrame(rows)


Adapter = BaiduAdapter
