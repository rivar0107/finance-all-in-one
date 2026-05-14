"""efinance 适配器

东方财富接口的轻量封装，实时性高，稳定性好。
覆盖：A 股实时行情、K 线
"""

from typing import Optional

import pandas as pd

# 懒加载
_ef = None


def _get_efinance():
    global _ef
    if _ef is None:
        import efinance as ef
        _ef = ef
    return _ef


class EFinanceAdapter:
    """efinance 数据适配器"""

    name = "efinance"
    requires_key = False

    @classmethod
    def is_available(cls) -> bool:
        try:
            _get_efinance()
            return True
        except ImportError:
            return False

    @classmethod
    def _to_ef_code(cls, symbol: str) -> str:
        """efinance 使用纯数字代码。"""
        s = str(symbol).strip().lower()
        if s.startswith("sh") or s.startswith("sz"):
            s = s[2:]
        return s.zfill(6)

    @classmethod
    def fetch_quote(cls, symbol: str, **kwargs) -> pd.DataFrame:
        """获取 A 股实时行情。"""
        ef = _get_efinance()
        code = cls._to_ef_code(symbol)
        try:
            df = ef.stock.get_realtime_quotes()
            df = df[df["股票代码"] == code]
            return df
        except Exception:
            return pd.DataFrame()

    @classmethod
    def fetch_kline(
        cls,
        symbol: str,
        period: str = "daily",
        limit: int = 50,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        **kwargs,
    ) -> pd.DataFrame:
        """获取 A 股 K 线。"""
        ef = _get_efinance()
        code = cls._to_ef_code(symbol)

        freq_map = {"daily": "1", "weekly": "2", "monthly": "3"}
        freq = freq_map.get(period, "1")

        try:
            df = ef.stock.get_quote_history(
                stock_codes=code,
                klt=freq,
            )
            # 按日期范围过滤
            if start_date:
                df = df[df["日期"] >= start_date]
            if end_date:
                df = df[df["日期"] <= end_date]
            if limit:
                df = df.tail(limit)
            return df
        except Exception:
            return pd.DataFrame()


Adapter = EFinanceAdapter
