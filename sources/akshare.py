"""AKShare 适配器

开源 Python 库，接口极多，覆盖 A 股/港股/美股/期货/期权/加密货币/宏观等。
数据源为东方财富、新浪财经、腾讯财经等公开财经网站。
限制：接口可能因目标网站变动而失效，需做好异常处理。
"""

from typing import Optional

import pandas as pd

from config import REQUEST_TIMEOUT

# 懒加载 akshare，避免未安装时导入失败
_ak = None


def _get_akshare():
    global _ak
    if _ak is None:
        import akshare as ak

        _ak = ak
    return _ak


class AKShareAdapter:
    """AKShare 数据适配器"""

    name = "akshare"
    requires_key = False

    @classmethod
    def is_available(cls) -> bool:
        try:
            _get_akshare()
            return True
        except ImportError:
            return False

    @classmethod
    def _to_ak_code(cls, symbol: str, market: str = "a_share") -> str:
        """转换为 AKShare 代码格式。A 股纯数字，港股 hkxxx。"""
        s = str(symbol).strip().lower()
        if s.startswith("sh") or s.startswith("sz"):
            s = s[2:]
        if market == "hk":
            return f"hk{s.lstrip('0')}"
        return s.zfill(6)

    @classmethod
    def fetch_quote(cls, symbol: str, market: str = "a_share", **kwargs) -> pd.DataFrame:
        """获取实时行情。"""
        ak = _get_akshare()
        code = cls._to_ak_code(symbol, market)

        if market == "a_share":
            # 获取全市场快照后过滤
            df = ak.stock_zh_a_spot_em()
            df = df[df["代码"] == code]
            return df
        elif market == "hk":
            df = ak.stock_hk_spot_em()
            df = df[df["代码"] == code.lstrip("hk")]
            return df
        else:
            return pd.DataFrame()

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
        """获取 K 线数据。"""
        ak = _get_akshare()
        code = cls._to_ak_code(symbol, market)

        period_map = {"daily": "daily", "weekly": "weekly", "monthly": "monthly"}
        ak_period = period_map.get(period, "daily")

        if start_date is None:
            import datetime
            start_date = (datetime.date.today() - datetime.timedelta(days=limit * 2)).strftime("%Y%m%d")
        else:
            start_date = start_date.replace("-", "")
        if end_date is None:
            import datetime
            end_date = datetime.date.today().strftime("%Y%m%d")
        else:
            end_date = end_date.replace("-", "")

        if market == "a_share":
            df = ak.stock_zh_a_hist(
                symbol=code,
                period=ak_period,
                start_date=start_date,
                end_date=end_date,
                adjust="qfq",
            )
            return df
        elif market == "hk":
            df = ak.stock_hk_hist(
                symbol=code.lstrip("hk"),
                period=ak_period,
                start_date=start_date,
                end_date=end_date,
            )
            return df
        else:
            return pd.DataFrame()

    @classmethod
    def fetch_financial(cls, symbol: str, report_type: str = "income", **kwargs) -> pd.DataFrame:
        """获取财务数据。"""
        ak = _get_akshare()
        code = cls._to_ak_code(symbol, "a_share")

        if report_type == "income":
            return ak.stock_financial_report_sina(stock=code, symbol="利润表")
        elif report_type == "balance":
            return ak.stock_financial_report_sina(stock=code, symbol="资产负债表")
        elif report_type == "cashflow":
            return ak.stock_financial_report_sina(stock=code, symbol="现金流量表")
        else:
            return ak.stock_financial_analysis_indicator(symbol=code)

    @classmethod
    def fetch_sector_flow(cls, **kwargs) -> pd.DataFrame:
        """获取板块资金流向。"""
        ak = _get_akshare()
        try:
            df = ak.stock_sector_fund_flow_rank()
            return df
        except Exception:
            return pd.DataFrame()

    @classmethod
    def fetch_futures_quote(cls, symbol: str, **kwargs) -> pd.DataFrame:
        """获取期货实时行情。"""
        ak = _get_akshare()
        try:
            df = ak.futures_zh_realtime(symbol=symbol)
            return df
        except Exception:
            return pd.DataFrame()

    @classmethod
    def fetch_futures_kline(cls, symbol: str, period: str = "daily", **kwargs) -> pd.DataFrame:
        """获取期货 K 线。"""
        ak = _get_akshare()
        try:
            df = ak.futures_zh_daily(symbol=symbol)
            return df
        except Exception:
            return pd.DataFrame()

    @classmethod
    def fetch_option_chain(cls, underlying: str, **kwargs) -> pd.DataFrame:
        """获取期权链。"""
        ak = _get_akshare()
        try:
            # 50ETF 期权
            if underlying in ("510050", "510300"):
                df = ak.option_cffex_300etf_spot()
                return df
            return pd.DataFrame()
        except Exception:
            return pd.DataFrame()

    @classmethod
    def fetch_macro(cls, indicator: str = "gdp", **kwargs) -> pd.DataFrame:
        """获取宏观经济数据。"""
        ak = _get_akshare()
        try:
            if indicator == "gdp":
                return ak.macro_china_gdp()
            elif indicator == "cpi":
                return ak.macro_china_cpi()
            elif indicator == "ppi":
                return ak.macro_china_ppi()
            elif indicator == "pmi":
                return ak.macro_china_pmi()
            elif indicator == "lpr":
                return ak.macro_china_lpr()
            elif indicator == "money_supply":
                return ak.macro_china_money_supply()
            else:
                return pd.DataFrame()
        except Exception:
            return pd.DataFrame()

    @classmethod
    def fetch(cls, data_type: str, **kwargs) -> pd.DataFrame:
        """通用 fallback 方法。"""
        if "kline" in data_type:
            return cls.fetch_kline(**kwargs)
        if "quote" in data_type:
            return cls.fetch_quote(**kwargs)
        return pd.DataFrame()


Adapter = AKShareAdapter
