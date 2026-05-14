"""mootdx/TDX 适配器

通达信协议，A 股 Level-2 数据。
覆盖：逐笔成交（Tick）历史 + 实时、Level-2 五档盘口、1 分钟 K 线
"""

from typing import Optional

import pandas as pd

from config import REQUEST_TIMEOUT

_mootdx = None


def _get_mootdx():
    global _mootdx
    if _mootdx is None:
        import mootdx
        _mootdx = mootdx
    return _mootdx


class MootdxAdapter:
    """mootdx 数据适配器"""

    name = "mootdx"
    requires_key = False

    @classmethod
    def is_available(cls) -> bool:
        try:
            _get_mootdx()
            return True
        except ImportError:
            return False

    @classmethod
    def _to_mootdx_code(cls, symbol: str) -> str:
        """mootdx 使用纯数字代码，不支持北交所。"""
        s = str(symbol).strip()
        if s.lower().startswith("sh") or s.lower().startswith("sz"):
            s = s[2:]
        return s.zfill(6)

    @classmethod
    def fetch_kline(cls, symbol: str, period: str = "daily", limit: int = 50, **kwargs) -> pd.DataFrame:
        """获取 1 分钟 K 线。"""
        mootdx = _get_mootdx()
        code = cls._to_mootdx_code(symbol)

        try:
            from mootdx.quotes import Quotes
            client = Quotes.factory(market="std")
            # mootdx 的 k 线接口：frequency=1 表示 1 分钟
            df = client.klines(symbol=code, frequency=1, begin=0, offset=limit)
            client.close()
            return df
        except Exception:
            return pd.DataFrame()

    @classmethod
    def fetch_depth(cls, symbol: str, **kwargs) -> pd.DataFrame:
        """获取 Level-2 五档盘口。"""
        mootdx = _get_mootdx()
        code = cls._to_mootdx_code(symbol)

        try:
            from mootdx.quotes import Quotes
            client = Quotes.factory(market="std")
            df = client.snapshot(symbol=code)
            client.close()
            return df
        except Exception:
            return pd.DataFrame()

    @classmethod
    def fetch_ticks(cls, symbol: str, date: Optional[str] = None, **kwargs) -> pd.DataFrame:
        """获取逐笔成交（Tick）历史 + 实时。"""
        mootdx = _get_mootdx()
        code = cls._to_mootdx_code(symbol)

        try:
            from mootdx.quotes import Quotes
            client = Quotes.factory(market="std")
            if date:
                df = client.transactions(symbol=code, date=date, start=0, offset=8000)
            else:
                df = client.transactions(symbol=code, start=0, offset=8000)
            client.close()
            return df
        except Exception:
            return pd.DataFrame()

    @classmethod
    def fetch(cls, data_type: str, **kwargs) -> pd.DataFrame:
        if data_type == "stock_depth":
            return cls.fetch_depth(**kwargs)
        if data_type == "stock_ticks":
            return cls.fetch_ticks(**kwargs)
        if "kline" in data_type:
            return cls.fetch_kline(**kwargs)
        return pd.DataFrame()


Adapter = MootdxAdapter
