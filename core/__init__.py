"""core 层 - 金融数据统一获取引擎"""

from core.cache import TTLCache
from core.exceptions import (
    DataFetchError,
    FinanceAllInOneError,
    InsufficientDataError,
    InvalidSymbolError,
    RateLimitError,
    SourceExhaustedError,
    SourceUnavailableError,
)
from core.fetcher import fetch_with_fallback, get_cache
from core.normalizer import normalize_financial, normalize_kline, normalize_quote
from core.result import FetchResult
from core.router import Router

__all__ = [
    "FetchResult",
    "TTLCache",
    "Router",
    "fetch_with_fallback",
    "get_cache",
    "normalize_kline",
    "normalize_quote",
    "normalize_financial",
    "FinanceAllInOneError",
    "DataFetchError",
    "SourceUnavailableError",
    "SourceExhaustedError",
    "InsufficientDataError",
    "InvalidSymbolError",
    "RateLimitError",
]
