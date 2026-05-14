"""网易财经适配器 (quotes.money.163.com)

HTTP 直连型，CSV 格式直接可读，支持自定义字段和日期范围。
覆盖：A 股历史 K 线 + 财务三表
"""

from typing import Optional

import pandas as pd
import requests

from config import REQUEST_TIMEOUT


class NeteaseAdapter:
    """网易财经数据适配器"""

    name = "netease"
    requires_key = False

    BASE_URL = "http://quotes.money.163.com/service/chddata.html"

    @classmethod
    def is_available(cls) -> bool:
        return True

    @classmethod
    def _to_netease_code(cls, symbol: str, market: str = "a_share") -> str:
        """转换为网易代码格式：上海前加 0，深圳前加 1。"""
        s = str(symbol).strip()
        # 去除可能的市场前缀
        if s.lower().startswith("sh"):
            s = s[2:]
        elif s.lower().startswith("sz"):
            s = s[2:]
        s = s.zfill(6)
        if s.startswith(("6", "68", "88", "51", "50", "56", "58", "11", "12")):
            return "0" + s
        return "1" + s

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
        """获取历史 K 线（CSV 格式）。"""
        code = cls._to_netease_code(symbol, market)

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

        # 网易只支持日线
        params = {
            "code": code,
            "start": start_date,
            "end": end_date,
            "fields": "TCLOSE;HIGH;LOW;TOPEN;LCLOSE;CHG;PCHG;TURNOVER;VOTURNOVER;VATURNOVER;TCAP;MCAP",
        }
        resp = requests.get(cls.BASE_URL, params=params, timeout=REQUEST_TIMEOUT)
        resp.encoding = "gbk"

        from io import StringIO

        df = pd.read_csv(StringIO(resp.text))
        if df.empty:
            return pd.DataFrame()

        # 网易 CSV 列名映射
        df = df.rename(
            columns={
                "日期": "date",
                "股票代码": "symbol",
                "名称": "name",
                "收盘价": "close",
                "最高价": "high",
                "最低价": "low",
                "开盘价": "open",
                "前收盘": "pre_close",
                "涨跌额": "change",
                "涨跌幅": "pct_chg",
                "换手率": "turnover",
                "成交量": "volume",
                "成交金额": "amount",
                "总市值": "total_cap",
                "流通市值": "float_cap",
            }
        )
        return df

    @classmethod
    def fetch_financial(
        cls,
        symbol: str,
        report_type: str = "income",
        **kwargs,
    ) -> pd.DataFrame:
        """获取财务数据（主要财务指标/资产负债表/利润表/现金流量表）。"""
        # 映射 report_type 到网易接口后缀
        type_map = {
            "income": "lrb",
            "balance": "zcfzb",
            "cashflow": "xjllb",
            "main": "zycwzb",
        }
        suffix = type_map.get(report_type, "zycwzb")

        s = str(symbol).strip().lower()
        if s.startswith("sh") or s.startswith("sz"):
            s = s[2:]
        s = s.zfill(6)

        url = f"http://quotes.money.163.com/service/{suffix}_{s}.html"
        resp = requests.get(url, timeout=REQUEST_TIMEOUT)
        resp.encoding = "gbk"

        from io import StringIO

        df = pd.read_csv(StringIO(resp.text))
        return df


Adapter = NeteaseAdapter
