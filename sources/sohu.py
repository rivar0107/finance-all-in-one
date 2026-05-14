"""搜狐财经适配器 (q.stock.sohu.com)

HTTP 直连型，免费源中唯一提供历史换手率。
覆盖：A 股历史日/周/月线
"""

from typing import Optional

import pandas as pd
import requests

from config import REQUEST_TIMEOUT


class SohuAdapter:
    """搜狐财经数据适配器"""

    name = "sohu"
    requires_key = False

    BASE_URL = "http://q.stock.sohu.com/hisHq"

    @classmethod
    def is_available(cls) -> bool:
        return True

    @classmethod
    def _to_sohu_code(cls, symbol: str, market: str = "a_share") -> str:
        """转换为搜狐代码格式：A 股 cn_xxx，指数 zs_xxx。"""
        s = str(symbol).strip().lower()
        if s.startswith("sh"):
            return f"cn_{s[2:]}"
        elif s.startswith("sz"):
            return f"cn_{s[2:]}"
        elif s.startswith("zs_") or s.startswith("sh"):
            return s.replace("sh", "zs_", 1)
        return f"cn_{s.zfill(6)}"

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
        """获取历史 K 线（JSON 格式）。"""
        code = cls._to_sohu_code(symbol, market)

        import datetime

        if end_date is None:
            end_date = datetime.date.today().strftime("%Y%m%d")
        else:
            end_date = end_date.replace("-", "")

        if start_date is None:
            start = datetime.date.today() - datetime.timedelta(days=limit * 2)
            start_date = start.strftime("%Y%m%d")
        else:
            start_date = start_date.replace("-", "")

        period_map = {"daily": "d", "weekly": "w", "monthly": "m"}
        sohu_period = period_map.get(period, "d")

        params = {
            "code": code,
            "start": start_date,
            "end": end_date,
            "period": sohu_period,
            "rt": "json",
        }
        resp = requests.get(cls.BASE_URL, params=params, timeout=REQUEST_TIMEOUT)
        data = resp.json()

        # 搜狐返回格式: [{"status":0,"hq":[["2025-01-01","open","close","change","pct","low","high","volume","amount","turnover"],...]}]
        rows = []
        for item in data:
            if isinstance(item, dict) and item.get("status") == 0:
                hq = item.get("hq", [])
                for row in hq:
                    if len(row) >= 9:
                        rows.append(
                            {
                                "date": row[0],
                                "open": row[1],
                                "close": row[2],
                                "change": row[3],
                                "pct_chg": row[4],
                                "low": row[5],
                                "high": row[6],
                                "volume": row[7],
                                "amount": row[8],
                                "turnover": row[9] if len(row) > 9 else None,
                            }
                        )

        df = pd.DataFrame(rows)
        if not df.empty:
            # 搜狐 volume 单位为"手"，转为"股"
            df["volume"] = pd.to_numeric(df["volume"], errors="coerce") * 100
            # 搜狐 amount 单位为"万元"，转为"元"
            df["amount"] = pd.to_numeric(df["amount"], errors="coerce") * 10000
        return df


Adapter = SohuAdapter
