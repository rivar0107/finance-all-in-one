"""意图路由：按数据类型和市场确定数据源优先级列表。"""

import os
from typing import List

from config import ROUTING_TABLE, US_ENHANCED_ROUTING, check_enhanced_keys


class Router:
    """路由决策器。"""

    @staticmethod
    def get_sources(data_type: str, market: str) -> List[str]:
        """
        获取指定数据类型和市场的数据源优先级列表。

        Args:
            data_type: 数据类型，如 "stock_quote"
            market: 市场类型，如 "a_share" / "us" / "hk"

        Returns:
            按优先级排序的数据源名称列表
        """
        key = (data_type, market)
        sources = list(ROUTING_TABLE.get(key, []))

        if not sources:
            # 尝试模糊匹配：只按 data_type 匹配任意市场
            for (dt, mk), srcs in ROUTING_TABLE.items():
                if dt == data_type:
                    sources = list(srcs)
                    break

        # 美股增强层动态插入
        if market == "us":
            enhanced = check_enhanced_keys()
            for source_name, route_keys in US_ENHANCED_ROUTING.items():
                if enhanced.get(source_name) and key in route_keys:
                    if source_name not in sources:
                        sources.insert(0, source_name)

        return sources

    @staticmethod
    def resolve_market(symbol: str) -> str:
        """根据代码格式推断市场。"""
        s = str(symbol).upper().strip()
        # 港股：显式前缀、.HK 后缀、或 5 位以下数字（A 股均为 6 位）
        if s.startswith(("HK", "9")) or ".HK" in s:
            return "hk"
        if s.isdigit() and len(s) <= 5:
            return "hk"
        # A 股
        if s.startswith(("SH", "SZ", "BJ", "6", "0", "3", "8", "4", "68", "30")):
            return "a_share"
        if s.isalpha() or (len(s) <= 5 and s.replace(".", "").replace("-", "").isalpha()):
            return "us"
        if "RB" in s or "CU" in s or "AL" in s or "FU" in s:
            return "futures"
        return "a_share"  # 默认 A 股

    @staticmethod
    def resolve_data_type(user_intent: str) -> str:
        """
        将用户意图解析为标准 data_type。
        这是简化版规则解析，完整版应由 LLM 或更复杂的规则驱动。
        """
        intent = user_intent.lower()

        if any(k in intent for k in ("实时", "行情", "多少钱", "价格", "现价", "quote")):
            return "stock_quote"
        if any(k in intent for k in ("k线", "日线", "周线", "月线", "kline", "历史")):
            return "stock_kline"
        if any(k in intent for k in ("分钟", "分时", "intraday", "1m", "5m", "15m")):
            return "stock_minute_kline"
        if any(k in intent for k in ("财务", "利润", "资产", "负债", "现金流", "financial")):
            return "stock_financial"
        if any(k in intent for k in ("板块", "行业", "sector", "fund flow")):
            return "sector_fund_flow"
        if any(k in intent for k in ("龙虎榜", "dragon")):
            return "dragon_tiger"
        if any(k in intent for k in ("融资", "融券", "margin")):
            return "margin_trading"
        if any(k in intent for k in ("ipo", "新股", "new stock")):
            return "ipo_list"
        if any(k in intent for k in ("盘口", "五档", "depth")):
            return "stock_depth"
        if any(k in intent for k in ("逐笔", "tick", "成交明细")):
            return "stock_ticks"
        if any(k in intent for k in ("大单", "主力", "big order")):
            return "stock_big_order"
        if any(k in intent for k in ("竞价", "集合", "auction")):
            return "call_auction"
        if any(k in intent for k in ("日内", "分时走势", "trends")):
            return "stock_intraday"
        if any(k in intent for k in ("问财", "选股", "screen", "wencai")):
            return "wencai_screen"
        if any(k in intent for k in ("etf", "pcf")):
            return "etf_quote"
        if any(k in intent for k in ("指数", "index")):
            return "index_quote"
        if any(k in intent for k in ("基金", "净值", "fund")):
            return "fund_nav"
        if any(k in intent for k in ("期货", "futures")):
            return "futures_quote"
        if any(k in intent for k in ("期权", "option")):
            return "option_chain"
        if any(k in intent for k in ("宏观", "gdp", "cpi", "pmi", "lpr", "macro")):
            return "china_macro"
        if any(k in intent for k in ("新闻", "资讯", "news")):
            return "news_search"
        if any(k in intent for k in ("公告", "announcement")):
            return "announcements"
        if any(k in intent for k in ("研报", "report")):
            return "reports"
        if any(k in intent for k in ("雪球", "组合", "portfolio", "cube")):
            return "portfolio_nav"
        if any(k in intent for k in ("北向", "北水", "northbound")):
            return "northbound_flow"

        return "stock_quote"  # 默认兜底
