"""宏观经济数据接口"""

from core.fetcher import fetch_with_fallback
from core.result import FetchResult


def get_china_gdp() -> FetchResult:
    """中国 GDP。"""
    return fetch_with_fallback(
        symbol="GDP",
        data_type="china_macro",
        market="macro",
        indicator="gdp",
    )


def get_china_cpi() -> FetchResult:
    """中国 CPI。"""
    return fetch_with_fallback(
        symbol="CPI",
        data_type="china_macro",
        market="macro",
        indicator="cpi",
    )


def get_china_ppi() -> FetchResult:
    """中国 PPI。"""
    return fetch_with_fallback(
        symbol="PPI",
        data_type="china_macro",
        market="macro",
        indicator="ppi",
    )


def get_china_pmi() -> FetchResult:
    """中国 PMI。"""
    return fetch_with_fallback(
        symbol="PMI",
        data_type="china_macro",
        market="macro",
        indicator="pmi",
    )


def get_china_lpr() -> FetchResult:
    """中国 LPR。"""
    return fetch_with_fallback(
        symbol="LPR",
        data_type="china_macro",
        market="macro",
        indicator="lpr",
    )


def get_china_money_supply() -> FetchResult:
    """中国货币供应量（M0/M1/M2）。"""
    return fetch_with_fallback(
        symbol="MONEY_SUPPLY",
        data_type="china_macro",
        market="macro",
        indicator="money_supply",
    )


def get_us_economic(indicator: str) -> FetchResult:
    """美国经济数据。

    indicator 示例:
        nonfarm-payroll, cpi-yoy, fed-funds-rate-upper
    """
    return fetch_with_fallback(
        symbol=indicator,
        data_type="us_macro",
        market="macro",
        indicator=indicator,
    )
