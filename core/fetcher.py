"""统一数据获取封装（降级逻辑）"""

import importlib
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Optional

import pandas as pd

from config import MIN_DATA_THRESHOLD, REQUEST_TIMEOUT
from core.cache import TTLCache
from core.exceptions import SourceExhaustedError
from core.normalizer import normalize_kline, normalize_quote, normalize_financial
from core.result import FetchResult
from core.router import Router

logger = logging.getLogger(__name__)

# 全局缓存实例
_global_cache = TTLCache()


def get_cache() -> TTLCache:
    """获取全局缓存实例（供外部共享）。"""
    return _global_cache


def fetch_with_fallback(
    symbol: str,
    data_type: str,
    market: Optional[str] = None,
    period: str = "daily",
    limit: int = 50,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    use_cache: bool = True,
    **kwargs: Any,
) -> FetchResult:
    """
    核心降级逻辑：按优先级尝试各源，直到成功或全部失败。

    Args:
        symbol: 股票代码或名称
        data_type: 数据类型，如 "stock_quote"
        market: 市场类型，自动推断
        period: K 线周期
        limit: 返回条数
        start_date: 起始日期
        end_date: 结束日期
        use_cache: 是否使用缓存
        **kwargs: 透传给适配器的额外参数

    Returns:
        FetchResult 统一结果容器
    """
    if market is None:
        market = Router.resolve_market(symbol)

    # 缓存 key 生成
    cache_key_args = (symbol, data_type, market, period, limit, start_date, end_date)
    cache_key_kwargs = dict(sorted(kwargs.items()))

    if use_cache:
        cached = _global_cache.get(*cache_key_args, data_type=data_type, **cache_key_kwargs)
        if cached is not None:
            cached.cached = True
            return cached

    # 获取源优先级列表
    sources = Router.get_sources(data_type, market)
    if not sources:
        raise SourceExhaustedError(
            f"未找到 {market} 市场 {data_type} 类型的数据源路由配置。"
        )

    errors: list[str] = []
    warnings: list[str] = []

    for idx, source_name in enumerate(sources):
        adapter = _load_adapter(source_name)
        if adapter is None:
            continue

        if not getattr(adapter, "is_available", lambda: True)():
            continue

        try:
            raw_data = _fetch_from_adapter(
                adapter=adapter,
                source_name=source_name,
                data_type=data_type,
                symbol=symbol,
                market=market,
                period=period,
                limit=limit,
                start_date=start_date,
                end_date=end_date,
                **kwargs,
            )

            if raw_data is None:
                continue
            if isinstance(raw_data, pd.DataFrame) and raw_data.empty:
                if not raw_data.columns.empty and idx == len(sources) - 1:
                    normalized = _normalize(raw_data, source_name, data_type)
                    return FetchResult(
                        data=normalized,
                        source=source_name,
                        data_type=data_type,
                        market=market,
                        warnings=["数据源请求成功，但当前查询条件无返回记录。"],
                    )
                continue

            # 数据量检查
            if isinstance(raw_data, pd.DataFrame) and len(raw_data) < MIN_DATA_THRESHOLD:
                warnings.append(
                    f"源 {source_name} 返回数据仅 {len(raw_data)} 条，低于阈值 {MIN_DATA_THRESHOLD}。"
                )
                # 仍继续，尝试下一个源补充，或如果这是最后一个源也接受
                if idx < len(sources) - 1:
                    continue

            # 归一化
            normalized = _normalize(raw_data, source_name, data_type)

            # 降级警告
            if idx > 0:
                warnings.insert(
                    0, f"主源 {sources[0]} 不可用，已自动降级至 {source_name}。"
                )

            result = FetchResult(
                data=normalized,
                source=source_name,
                data_type=data_type,
                market=market,
                warnings=warnings if warnings else [],
            )

            # 写入缓存
            if use_cache:
                _global_cache.set(result, *cache_key_args, data_type=data_type, **cache_key_kwargs)

            return result

        except Exception as e:
            msg = f"{source_name}: {type(e).__name__}: {e}"
            errors.append(msg)
            logger.warning(msg)
            continue

    # 全部失败
    raise SourceExhaustedError(
        f"所有数据源均无法获取 {market} {data_type} {symbol}。\n"
        f"尝试记录：{'; '.join(errors)}"
    )


def _load_adapter(source_name: str) -> Optional[Any]:
    """动态加载适配器模块。"""
    try:
        module = importlib.import_module(f"sources.{source_name}")
        # 适配器模块应暴露一个 Adapter 类实例或类本身
        adapter = getattr(module, "Adapter", None)
        if adapter is None:
            # 也尝试小写适配器名
            adapter = getattr(module, "adapter", None)
        return adapter
    except ImportError as e:
        logger.debug(f"适配器 {source_name} 加载失败: {e}")
        return None


def _fetch_from_adapter(
    adapter: Any,
    source_name: str,
    data_type: str,
    symbol: str,
    market: str,
    period: str,
    limit: int,
    start_date: Optional[str],
    end_date: Optional[str],
    **kwargs: Any,
) -> Any:
    """调用适配器获取原始数据。"""
    # 构建调用参数
    call_kwargs = {
        "symbol": symbol,
        "market": market,
        "period": period,
        "limit": limit,
        **kwargs,
    }
    if start_date:
        call_kwargs["start_date"] = start_date
    if end_date:
        call_kwargs["end_date"] = end_date

    # 按数据类型分发到适配器的对应方法
    method_name = _resolve_method_name(data_type)
    method = getattr(adapter, method_name, None)
    if method is None:
        # 回退到通用 fetch 方法
        method = getattr(adapter, "fetch", None)
        if method is None:
            raise NotImplementedError(
                f"适配器 {source_name} 未实现 {method_name} 或 fetch 方法"
            )
        call_kwargs["data_type"] = data_type

    return method(**call_kwargs)


def _resolve_method_name(data_type: str) -> str:
    """将 data_type 映射到适配器方法名。"""
    mapping = {
        "stock_quote": "fetch_quote",
        "etf_quote": "fetch_quote",
        "index_quote": "fetch_quote",
        "hk_quote": "fetch_quote",
        "futures_quote": "fetch_quote",
        "option_quote": "fetch_quote",
        "stock_kline": "fetch_kline",
        "stock_minute_kline": "fetch_kline",
        "etf_kline": "fetch_kline",
        "index_kline": "fetch_kline",
        "hk_kline": "fetch_kline",
        "futures_kline": "fetch_kline",
        "stock_financial": "fetch_financial",
        "stock_depth": "fetch_depth",
        "stock_ticks": "fetch_ticks",
        "stock_intraday": "fetch_intraday",
        "sector_fund_flow": "fetch_sector_flow",
        "dragon_tiger": "fetch_dragon_tiger",
        "margin_trading": "fetch_margin",
        "ipo_list": "fetch_ipo",
        "news_search": "fetch_news",
        "announcements": "fetch_announcements",
        "reports": "fetch_reports",
        "china_macro": "fetch_macro",
        "us_macro": "fetch_macro",
        "portfolio_nav": "fetch_portfolio_nav",
        "portfolio_rebalancing": "fetch_portfolio_rebalancing",
        "northbound_flow": "fetch_northbound_flow",
        "fast_news": "fetch_fast_news",
        "stock_holders": "fetch_stock_holders",
        "stock_pledge": "fetch_pledge",
        "share_change": "fetch_share_change",
        "performance_express": "fetch_performance",
        "performance_forecast": "fetch_performance_forecast",
        "cb_base": "fetch_cb_base",
        "cb_list": "fetch_cb_list",
    }
    return mapping.get(data_type, "fetch")


def batch_fetch_with_fallback(
    symbols: list[str],
    data_type: str,
    market: Optional[str] = None,
    max_workers: int = 3,
    **kwargs: Any,
) -> list[FetchResult]:
    """批量获取多个 symbol 的数据。

    Args:
        symbols: 股票代码列表
        data_type: 数据类型
        market: 市场类型（默认自动推断）
        max_workers: 最大并发数（默认 3，避免触发源限流）
        **kwargs: 透传给 fetch_with_fallback 的其他参数

    Returns:
        FetchResult 列表，与 symbols 顺序一致。失败时返回空 DataFrame 的 FetchResult。
    """
    if len(symbols) == 0:
        return []

    results_map: dict[str, FetchResult] = {}

    def _fetch_one(sym: str) -> tuple[str, FetchResult]:
        try:
            return sym, fetch_with_fallback(
                symbol=sym,
                data_type=data_type,
                market=market,
                **kwargs,
            )
        except Exception as e:
            logger.warning(f"批量查询 {sym} 失败: {e}")
            empty = FetchResult(
                data=pd.DataFrame(),
                source="",
                data_type=data_type,
                market=market or Router.resolve_market(sym),
                warnings=[str(e)],
            )
            return sym, empty

    if max_workers > 1 and len(symbols) > 1:
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_sym = {
                executor.submit(_fetch_one, sym): sym for sym in symbols
            }
            for future in as_completed(future_to_sym):
                sym, result = future.result()
                results_map[sym] = result
    else:
        for sym in symbols:
            sym_key, result = _fetch_one(sym)
            results_map[sym_key] = result

    # 保持输入顺序
    return [results_map[sym] for sym in symbols]


def _normalize(raw_data: Any, source_name: str, data_type: str) -> pd.DataFrame:
    """根据数据类型选择归一化函数。"""
    if not isinstance(raw_data, pd.DataFrame):
        # 尝试转换为 DataFrame
        if isinstance(raw_data, list):
            raw_data = pd.DataFrame(raw_data)
        elif isinstance(raw_data, dict):
            raw_data = pd.DataFrame([raw_data])
        else:
            raw_data = pd.DataFrame(raw_data)

    if "kline" in data_type or data_type in ("stock_history", "etf_kline", "index_kline", "hk_kline", "futures_kline"):
        return normalize_kline(raw_data, source_name)
    if "quote" in data_type or data_type in ("stock_quote", "etf_quote", "index_quote", "hk_quote", "futures_quote", "option_quote", "stock_intraday"):
        return normalize_quote(raw_data, source_name)
    if data_type in ("stock_financial", "us_fundamentals"):
        return normalize_financial(raw_data, source_name)

    # 默认：只做列名蛇形化
    return normalize_financial(raw_data, source_name)
