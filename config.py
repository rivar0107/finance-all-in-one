"""全局配置：路由表、常量、阈值"""

import os
from typing import Callable

# ─── 超时与阈值 ───
REQUEST_TIMEOUT = 10          # 单次请求超时（秒）
MIN_DATA_THRESHOLD = 1        # 最少返回条数（1 条即可，实时行情常只有 1 行）
MAX_RETRY = 1                 # 单源重试次数

# ─── 增强层环境变量检测 ───
ENHANCED_ENV_VARS = {
    "tushare": "TUSHARE_TOKEN",
    "alpaca": "ALPACA_API_KEY",
    "twelve_data": "TWELVE_DATA_API_KEY",
    "finnhub": "FINNHUB_API_KEY",
    "fmp": "FMP_API_KEY",
    "tiingo": "TIINGO_API_KEY",
    "alpha_vantage": "ALPHA_VANTAGE_API_KEY",
    "jrj": "JRJ_API_KEY",
    "mx_finance": "EM_API_KEY",
}


def check_enhanced_keys() -> dict[str, bool]:
    """返回各增强层 Key 是否已配置。"""
    return {name: os.environ.get(env_var) is not None for name, env_var in ENHANCED_ENV_VARS.items()}


# ─── 路由表：data_type + market -> 源优先级列表 ───
# 格式: (data_type, market): [source_name, ...]
# source_name 对应 sources/ 目录下的适配器模块名
ROUTING_TABLE: dict[tuple[str, str], list[str]] = {
    # ── A 股实时行情 ──
    # 说明：akshare 的 quote 基于东方财富实时接口，e2e 中多次出现 RemoteDisconnected，
    #       优先级下调至 tushare 之后，作为兜底。
    ("stock_quote", "a_share"): ["tencent", "sina", "ftshare", "efinance", "tushare", "akshare"],
    # ── A 股 K 线 ──
    ("stock_kline", "a_share"): [
        "ftshare", "tencent", "netease", "baidu_stock", "akshare", "efinance", "baostock",
        "tushare",
    ],
    # ── A 股分钟 K 线 ──
    ("stock_minute_kline", "a_share"): ["ths"],
    # ── A 股历史(含换手) ──
    ("stock_history", "a_share"): ["sohu", "netease", "akshare"],
    # ── A 股财务 ──
    ("stock_financial", "a_share"): ["ftshare", "netease", "akshare", "baostock", "tushare"],
    # ── A 股板块/行业 ──
    ("sector_fund_flow", "a_share"): ["akshare", "ths"],
    # ── A 股资金流向 ──
    ("stock_fund_flow", "a_share"): ["tencent", "akshare", "ths"],
    # ── A 股龙虎榜 ──
    ("dragon_tiger", "a_share"): ["akshare", "tushare"],
    # ── A 股融资融券 ──
    ("margin_trading", "a_share"): ["ftshare", "akshare", "tushare"],
    # ── A 股股东 ──
    ("stock_holders", "a_share"): ["ftshare"],
    # ── A 股股权质押 ──
    ("stock_pledge", "a_share"): ["ftshare"],
    # ── A 股股本变动 ──
    ("share_change", "a_share"): ["ftshare"],
    # ── A 股业绩快报 ──
    ("performance_express", "a_share"): ["ftshare"],
    # ── A 股业绩预告 ──
    ("performance_forecast", "a_share"): ["ftshare"],
    # ── A 股可转债 ──
    ("cb_base", "a_share"): ["ftshare"],
    ("cb_list", "a_share"): ["ftshare"],
    # ── A 股 IPO ──
    ("ipo_list", "a_share"): ["ftshare", "akshare", "ths"],
    # ── A 股五档盘口 ──
    ("stock_depth", "a_share"): ["ths", "mootdx"],
    # ── A 股逐笔成交 ──
    ("stock_ticks", "a_share"): ["mootdx"],
    # ── A 股大单流向 ──
    ("stock_big_order", "a_share"): ["ths"],
    # ── A 股集合竞价异动 ──
    ("call_auction", "a_share"): ["ths"],
    # ── A 股日内分时 ──
    ("stock_intraday", "a_share"): ["eastmoney_intraday", "ths"],
    # ── A 股问财 NLP ──
    ("wencai_screen", "a_share"): ["ths"],
    # ── ETF ──
    ("etf_quote", "a_share"): ["ftshare", "akshare"],
    ("etf_kline", "a_share"): ["ftshare", "akshare"],
    ("etf_components", "a_share"): ["ftshare", "ths"],
    ("etf_pcf", "a_share"): ["ftshare"],
    # ── 指数 ──
    ("index_quote", "a_share"): ["tencent", "ftshare", "akshare"],
    ("index_kline", "a_share"): ["ftshare", "tencent", "akshare"],
    ("index_weight", "a_share"): ["ftshare", "ths"],
    # ── 基金 ──
    ("fund_nav", "a_share"): ["ftshare", "akshare"],
    ("fund_return", "a_share"): ["ftshare", "akshare"],
    # ── 港股 ──
    ("stock_quote", "hk"): ["tencent", "sina", "ftshare", "yfinance"],
    ("stock_kline", "hk"): ["tencent", "ftshare", "ths", "yfinance"],
    ("hk_valuation", "hk"): ["ftshare"],
    # ── 美股 ──
    ("stock_quote", "us"): ["tencent", "sina", "yfinance"],  # 增强层 alpaca/twelve_data 在 router 中动态插入
    ("stock_kline", "us"): ["yfinance", "tencent", "akshare"],
    ("us_fundamentals", "us"): ["yfinance"],
    ("us_news", "us"): ["finnhub"],
    ("us_economic", "us"): ["ftshare", "finnhub", "fmp"],
    # ── 期货 ──
    ("futures_quote", "futures"): ["tencent", "akshare", "ths"],
    ("futures_kline", "futures"): ["akshare", "ths", "tencent"],
    ("futures_holdings", "futures"): ["akshare"],
    # ── 期权 ──
    ("option_chain", "options"): ["akshare", "efinance"],
    ("option_quote", "options"): ["akshare", "efinance"],
    ("option_expiry", "options"): ["akshare"],
    # ── 宏观 ──
    ("china_macro", "macro"): ["ftshare", "akshare"],
    ("us_macro", "macro"): ["ftshare", "finnhub", "fmp"],
    # ── 新闻 ──
    ("news_search", "news"): ["ftshare"],
    ("announcements", "news"): ["ftshare"],
    ("reports", "news"): ["ftshare"],
    ("fast_news", "news"): ["ths"],
    # ── 雪球 ──
    ("portfolio_nav", "xueqiu"): ["xueqiu"],
    ("northbound_flow", "xueqiu"): ["xueqiu", "akshare"],
}


# 美股增强层动态路由：有 Key 时插入到最前
US_ENHANCED_ROUTING: dict[str, list[tuple[str, str]]] = {
    "alpaca": [("stock_quote", "us")],
    "twelve_data": [("stock_quote", "us"), ("stock_kline", "us")],
    "finnhub": [("us_news", "us")],
    "fmp": [("us_fundamentals", "us")],
}


# 各 data_type 的归一化函数映射
NORMALIZER_MAP: dict[str, Callable] = {}
