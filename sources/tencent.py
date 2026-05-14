"""腾讯财经适配器 (qt.gtimg.cn)

HTTP 直连型，毫秒级响应，字段最丰富。
覆盖：A股/港股/美股/期货/外汇/ETF/大宗商品
"""

import re
from typing import Optional

import pandas as pd
import requests

from config import REQUEST_TIMEOUT


class TencentAdapter:
    """腾讯财经数据适配器"""

    name = "tencent"
    requires_key = False
    env_var = None

    BASE_URL = "https://qt.gtimg.cn/q="
    KLINE_URL = "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get"
    FUND_FLOW_URL = "https://qt.gtimg.cn/q=ff_"

    # 实时行情字段索引（按 ~ 分隔）
    # 基于 qt.gtimg.cn 实际返回校准（2026-05-12 抓取 sh600519 验证）
    QUOTE_FIELDS = {
        "name": 1,
        "code": 2,
        "price": 3,
        "pre_close": 4,
        "open": 5,
        "volume": 6,          # 成交量（手）
        "bid": 9,
        "bid_vol": 10,
        "ask": 19,
        "ask_vol": 20,
        "update_time": 30,    # YYYYMMDDHHMMSS
        "change": 31,         # 涨跌额
        "pct_change": 32,     # 涨跌幅%
        "high": 33,
        "low": 34,
        "amount": 37,         # 成交额（万元）
        "turnover": 38,       # 换手率%
        "pe": 39,
        "amplitude": 43,      # 振幅%
        "float_cap": 44,      # 流通市值（亿元）
        "market_cap": 45,     # 总市值（亿元）
        "pb": 46,
        "limit_up": 47,       # 涨停价
        "limit_down": 48,     # 跌停价
    }

    @classmethod
    def is_available(cls) -> bool:
        """HTTP 直连型始终可用（只要有 requests）。"""
        return True

    @classmethod
    def _to_tencent_code(cls, symbol: str, market: str) -> str:
        """转换为腾讯代码格式。"""
        s = str(symbol).strip().upper()
        # 如果已经是腾讯格式，直接返回
        if s.startswith(("SH", "SZ", "BJ", "HK", "US", "HF_", "FX_")):
            return s.lower()
        if ".HK" in s:
            return s.lower().replace(".HK", "")
        if "." in s and market == "us":
            return f"us{s.split('.')[0].upper()}"

        if market == "a_share":
            if s.startswith(("6", "68", "88", "51", "50", "56", "58", "11", "12")):
                return f"sh{s}"
            return f"sz{s}"
        if market == "hk":
            return f"hk{s.zfill(5)}"
        if market == "us":
            return f"us{s.upper()}"
        if market == "futures":
            return s  # 期货代码直接使用
        return s

    @classmethod
    def fetch_quote(cls, symbol: str, market: str = "a_share", **kwargs) -> pd.DataFrame:
        """获取实时行情。"""
        code = cls._to_tencent_code(symbol, market)
        url = f"{cls.BASE_URL}{code}"
        resp = requests.get(url, timeout=REQUEST_TIMEOUT)
        resp.encoding = "gbk"
        text = resp.text

        rows = []
        for line in text.strip().split(";"):
            line = line.strip()
            if not line:
                continue
            match = re.search(r'v_[^=]+="([^"]+)"', line)
            if not match:
                continue
            raw = match.group(1)
            parts = raw.split("~")
            if len(parts) < 10:
                continue

            row = {}
            for field, idx in cls.QUOTE_FIELDS.items():
                if idx < len(parts):
                    val = parts[idx]
                    row[field] = val if val else None
                else:
                    row[field] = None

            row["symbol"] = code
            rows.append(row)

        if not rows:
            return pd.DataFrame()

        df = pd.DataFrame(rows)
        # 数值转换
        numeric_cols = [
            "price", "open", "high", "low", "pre_close", "bid", "ask",
            "bid_vol", "ask_vol", "change", "pct_change", "pe", "pb",
            "volume", "amount", "turnover", "market_cap", "float_cap",
            "amplitude", "limit_up", "limit_down",
        ]
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")

        # 腾讯成交量是"手"，转为股
        if "volume" in df.columns:
            df["volume"] = df["volume"] * 100

        # 成交额从"万元"转为"元"
        if "amount" in df.columns:
            df["amount"] = df["amount"] * 10000

        # 时间格式转换 YYYYMMDDHHMMSS -> datetime
        if "update_time" in df.columns:
            df["update_time"] = pd.to_datetime(df["update_time"], format="%Y%m%d%H%M%S", errors="coerce")

        return df

    @classmethod
    def fetch_kline(cls, symbol: str, market: str = "a_share",
                    period: str = "daily", limit: int = 50,
                    start_date: Optional[str] = None,
                    end_date: Optional[str] = None, **kwargs) -> pd.DataFrame:
        """获取 K 线数据。"""
        code = cls._to_tencent_code(symbol, market)

        # 周期映射
        period_map = {"daily": "day", "weekly": "week", "monthly": "month"}
        tencent_period = period_map.get(period, "day")

        # 时间范围处理
        if end_date is None:
            import datetime
            end_date = datetime.date.today().strftime("%Y-%m-%d")
        if start_date is None:
            import datetime
            # 按 limit 估算起始日期
            days = limit * 2 if tencent_period == "day" else limit * 14
            start = datetime.date.today() - datetime.timedelta(days=days)
            start_date = start.strftime("%Y-%m-%d")

        # 复权类型：默认前复权 qfq
        fq = kwargs.get("adjust", "qfq")

        # 腾讯 K 线接口日期格式必须是 YYYY-MM-DD（保留连字符），limit 必填
        url = (
            f"{cls.KLINE_URL}?param={code},{tencent_period},"
            f"{start_date},{end_date},{limit},{fq}"
        )
        resp = requests.get(url, timeout=REQUEST_TIMEOUT)
        data = resp.json()

        # 解析 JSON
        # 复权时返回字段名为 qfqday/hfqday，不复权时为 day/week/month
        field_map = {
            "day": f"{fq}day" if fq else "day",
            "week": f"{fq}week" if fq else "week",
            "month": f"{fq}month" if fq else "month",
        }
        data_field = field_map.get(tencent_period, tencent_period)

        kline_data = []
        stock_data = data.get("data", {})
        for k in (code, code.lower(), code.upper()):
            if k in stock_data:
                if data_field in stock_data[k]:
                    kline_data = stock_data[k][data_field]
                    break
                # 港股等部分市场不支持复权字段，回退到原始字段名
                fallback_field = tencent_period
                if fallback_field in stock_data[k]:
                    kline_data = stock_data[k][fallback_field]
                    break

        rows = []
        for item in kline_data:
            if isinstance(item, list) and len(item) >= 5:
                rows.append({
                    "date": item[0],
                    "open": item[1],
                    "close": item[2],
                    "high": item[3],
                    "low": item[4],
                    "volume": item[5] if len(item) > 5 else None,
                })
            elif isinstance(item, str):
                # 某些返回是字符串列表
                parts = item.split(" ")
                if len(parts) >= 5:
                    rows.append({
                        "date": parts[0],
                        "open": parts[1],
                        "close": parts[2],
                        "low": parts[3],
                        "high": parts[4],
                        "volume": parts[5] if len(parts) > 5 else None,
                    })

        df = pd.DataFrame(rows)
        if not df.empty and limit:
            df = df.tail(limit).reset_index(drop=True)
        return df


# 模块级暴露
Adapter = TencentAdapter
