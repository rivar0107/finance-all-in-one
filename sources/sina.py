"""新浪财经适配器 (hq.sinajs.cn)

HTTP 直连型，速度极快，稳定性最高，经典免费接口。
覆盖：A股/港股/美股
"""

import re
from typing import Optional

import pandas as pd
import requests

from config import REQUEST_TIMEOUT


class SinaAdapter:
    """新浪财经数据适配器"""

    name = "sina"
    requires_key = False
    env_var = None

    BASE_URL = "https://hq.sinajs.cn/list="

    # 新浪实时行情字段索引（A股，逗号分隔）
    # var hq_str_sh600519="贵州茅台,1775.00,1760.00,1772.00,..."
    A_SHARE_FIELDS = [
        "name", "open", "pre_close", "price", "high", "low",
        "bid", "ask", "volume", "amount",
        "bid_vol_1", "bid_1", "bid_vol_2", "bid_2",
        "bid_vol_3", "bid_3", "bid_vol_4", "bid_4",
        "bid_vol_5", "bid_5",
        "ask_vol_1", "ask_1", "ask_vol_2", "ask_2",
        "ask_vol_3", "ask_3", "ask_vol_4", "ask_4",
        "ask_vol_5", "ask_5",
        "date", "time",
    ]

    @classmethod
    def is_available(cls) -> bool:
        """HTTP 直连型始终可用。"""
        return True

    @classmethod
    def _to_sina_code(cls, symbol: str, market: str) -> str:
        """转换为新浪代码格式。"""
        s = str(symbol).strip().upper()
        if s.startswith(("SH", "SZ", "BJ", "HK", "GB_")):
            return s.lower()
        if s.startswith("US"):
            return s.lower().replace("us", "gb_", 1)
        if ".HK" in s:
            return s.lower().replace(".HK", "")

        if market == "a_share":
            if s.startswith(("6", "68", "88", "51", "50", "56", "58", "11", "12")):
                return f"sh{s}"
            return f"sz{s}"
        if market == "hk":
            return f"hk{s.zfill(5)}"
        if market == "us":
            return f"gb_{s.lower()}"
        return s

    @classmethod
    def fetch_quote(cls, symbol: str, market: str = "a_share", **kwargs) -> pd.DataFrame:
        """获取实时行情。"""
        code = cls._to_sina_code(symbol, market)
        url = f"{cls.BASE_URL}{code}"
        headers = {"Referer": "https://finance.sina.com.cn"}
        resp = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT)
        resp.encoding = "gbk"
        text = resp.text

        rows = []
        for line in text.strip().split(";"):
            line = line.strip()
            if not line:
                continue
            match = re.search(r'var hq_str_[^=]+="([^"]*)"', line)
            if not match:
                continue
            raw = match.group(1)
            if not raw:
                continue
            parts = raw.split(",")

            row = {"symbol": code}
            if market == "a_share" and len(parts) >= 32:
                for i, field in enumerate(cls.A_SHARE_FIELDS):
                    if i < len(parts):
                        row[field] = parts[i]
            else:
                # 通用处理：前几个字段按常见位置映射
                row["name"] = parts[0] if len(parts) > 0 else ""
                row["price"] = parts[3] if len(parts) > 3 else parts[1] if len(parts) > 1 else None
                row["open"] = parts[1] if len(parts) > 1 else None
                row["pre_close"] = parts[2] if len(parts) > 2 else None
                row["high"] = parts[4] if len(parts) > 4 else None
                row["low"] = parts[5] if len(parts) > 5 else None
                row["volume"] = parts[8] if len(parts) > 8 else None
                row["amount"] = parts[9] if len(parts) > 9 else None
                row["bid"] = parts[6] if len(parts) > 6 else None
                row["ask"] = parts[7] if len(parts) > 7 else None
                row["date"] = parts[-2] if len(parts) > 2 else None
                row["time"] = parts[-1] if len(parts) > 1 else None

            rows.append(row)

        if not rows:
            return pd.DataFrame()

        df = pd.DataFrame(rows)
        # 数值转换
        for col in ["price", "open", "high", "low", "pre_close", "bid", "ask",
                    "volume", "amount", "bid_1", "ask_1"]:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")

        # 计算涨跌额和涨跌幅
        if "price" in df.columns and "pre_close" in df.columns:
            df["change"] = df["price"] - df["pre_close"]
            df["pct_change"] = (df["change"] / df["pre_close"] * 100).round(2)

        # 买一量/卖一量
        if "bid_vol_1" in df.columns:
            df["bid_vol"] = pd.to_numeric(df["bid_vol_1"], errors="coerce")
        if "ask_vol_1" in df.columns:
            df["ask_vol"] = pd.to_numeric(df["ask_vol_1"], errors="coerce")

        return df

    @classmethod
    def fetch_kline(cls, symbol: str, market: str = "a_share", **kwargs) -> pd.DataFrame:
        """新浪无免费 K 线接口，返回空。"""
        return pd.DataFrame()


# 模块级暴露
Adapter = SinaAdapter
