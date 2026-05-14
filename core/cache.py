"""TTL 内存缓存"""

import time
from typing import Any, Optional


class TTLCache:
    """简单内存 TTL 缓存，按数据类型设置不同过期时间。"""

    DEFAULT_TTL = 300  # 5 分钟

    TTL_MAP = {
        # 实时行情
        "stock_quote": 60,
        "etf_quote": 60,
        "index_quote": 60,
        "hk_quote": 60,
        "futures_quote": 60,
        "option_quote": 60,
        # K 线/历史
        "stock_kline": 300,
        "stock_minute_kline": 300,
        "etf_kline": 300,
        "index_kline": 300,
        "hk_kline": 300,
        "futures_kline": 300,
        # 财务/宏观
        "stock_financial": 3600,
        "china_macro": 86400,
        "us_macro": 86400,
        # 板块/资金/龙虎榜
        "sector_fund_flow": 120,
        "dragon_tiger": 300,
        # 新闻/公告
        "news_search": 120,
        "announcements": 120,
        "reports": 120,
        "fast_news": 60,
        # 盘口深度
        "stock_depth": 30,
        "stock_ticks": 30,
        "stock_intraday": 60,
        # 列表/基础信息
        "stock_list": 86400,
        "etf_list": 86400,
        "index_list": 86400,
        "fund_list": 86400,
        "futures_list": 86400,
        # 其他
        "portfolio_nav": 300,
        "northbound_flow": 120,
        "margin_trading": 300,
        "ipo_list": 86400,
    }

    def __init__(self, default_ttl: int = DEFAULT_TTL):
        self._cache: dict[str, tuple[Any, float]] = {}
        self._default_ttl = default_ttl

    def _make_key(self, *args, **kwargs) -> str:
        """生成缓存 key。"""
        return str(args) + str(sorted(kwargs.items()))

    def get(self, *args, **kwargs) -> Optional[Any]:
        """获取缓存值，过期返回 None。"""
        key = self._make_key(*args, **kwargs)
        if key not in self._cache:
            return None
        value, expiry = self._cache[key]
        if time.time() <= expiry:
            return value
        del self._cache[key]
        return None

    def set(self, value: Any, *args, **kwargs) -> None:
        """写入缓存，自动按 data_type 取 TTL。"""
        key = self._make_key(*args, **kwargs)
        data_type = kwargs.get("data_type", "")
        ttl = self.TTL_MAP.get(data_type, self._default_ttl)
        self._cache[key] = (value, time.time() + ttl)

    def clear(self) -> None:
        """清空缓存。"""
        self._cache.clear()

    def stats(self) -> dict:
        """返回缓存统计信息。"""
        now = time.time()
        total = len(self._cache)
        expired = sum(1 for _, expiry in self._cache.values() if expiry < now)
        return {"total_keys": total, "expired_keys": expired, "valid_keys": total - expired}
