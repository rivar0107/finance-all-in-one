"""雪球适配器 (pysnowball)

覆盖：组合净值、组合调仓、北向资金、实时快讯
"""

from typing import Optional

import pandas as pd

# 懒加载
_xq = None


def _get_xq():
    global _xq
    if _xq is None:
        import pysnowball
        _xq = pysnowball
    return _xq


class XueqiuAdapter:
    """雪球数据适配器"""

    name = "xueqiu"
    requires_key = False

    @classmethod
    def is_available(cls) -> bool:
        try:
            _get_xq()
            return True
        except ImportError:
            return False

    @classmethod
    def fetch_portfolio_nav(
        cls,
        symbol: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        **kwargs,
    ) -> pd.DataFrame:
        """获取雪球组合净值历史。"""
        xq = _get_xq()
        try:
            # pysnowball 返回 dict，含 "list" 字段
            resp = xq.cube_nav_daily(symbol)
            data = resp.get("list", []) if isinstance(resp, dict) else []
            df = pd.DataFrame(data)
            if df.empty:
                return df

            # 常见字段映射
            rename_map = {
                "date": "date",
                "nav": "nav",
                "b_nav": "benchmark_nav",
                "daily_gain": "daily_return",
                "month_gain": "month_return",
            }
            df = df.rename(columns={k: v for k, v in rename_map.items() if k in df.columns})

            # 时间过滤
            if start_date and "date" in df.columns:
                df = df[df["date"] >= start_date]
            if end_date and "date" in df.columns:
                df = df[df["date"] <= end_date]
            return df
        except Exception:
            return pd.DataFrame()

    @classmethod
    def fetch_portfolio_rebalancing(
        cls,
        symbol: str,
        count: int = 20,
        page: int = 1,
        **kwargs,
    ) -> pd.DataFrame:
        """获取组合调仓记录。"""
        xq = _get_xq()
        try:
            resp = xq.cube_rebalancing_history(symbol, count=count, page=page)
            data = resp.get("list", []) if isinstance(resp, dict) else []
            return pd.DataFrame(data)
        except Exception:
            return pd.DataFrame()

    @classmethod
    def fetch_northbound_flow(cls, **kwargs) -> pd.DataFrame:
        """获取北向资金（沪深港通）流向。"""
        xq = _get_xq()
        try:
            resp = xq.northbound_flow()
            # 返回通常是 dict，含 "data" 或 "items"
            if isinstance(resp, dict):
                data = resp.get("data") or resp.get("items") or resp.get("list", [])
            elif isinstance(resp, list):
                data = resp
            else:
                data = []
            return pd.DataFrame(data) if isinstance(data, list) else pd.DataFrame()
        except Exception:
            return pd.DataFrame()

    @classmethod
    def fetch_fast_news(cls, limit: int = 20, **kwargs) -> pd.DataFrame:
        """获取实时快讯。"""
        xq = _get_xq()
        try:
            resp = xq.news_flash(limit=limit)
            if isinstance(resp, dict):
                data = resp.get("items") or resp.get("list", [])
            elif isinstance(resp, list):
                data = resp
            else:
                data = []
            return pd.DataFrame(data) if isinstance(data, list) else pd.DataFrame()
        except Exception:
            return pd.DataFrame()

    @classmethod
    def fetch(cls, data_type: str, **kwargs) -> pd.DataFrame:
        if data_type == "portfolio_nav":
            return cls.fetch_portfolio_nav(**kwargs)
        if data_type == "portfolio_rebalancing":
            return cls.fetch_portfolio_rebalancing(**kwargs)
        if data_type == "northbound_flow":
            return cls.fetch_northbound_flow(**kwargs)
        if data_type == "fast_news":
            return cls.fetch_fast_news(**kwargs)
        return pd.DataFrame()


Adapter = XueqiuAdapter
