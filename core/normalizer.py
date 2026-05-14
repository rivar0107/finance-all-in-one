"""数据格式归一化"""

import re
from typing import Optional

import pandas as pd


def normalize_kline(df: pd.DataFrame, source: str) -> pd.DataFrame:
    """将各源 K 线数据归一化为标准 OHLCV 格式。"""
    if df is None or df.empty:
        return pd.DataFrame(columns=["date", "open", "high", "low", "close", "volume"])

    df = df.copy()

    # 统一列名映射
    col_map = _get_kline_col_map(source)
    df = df.rename(columns=col_map)

    # 确保标准字段存在
    for col in ["date", "open", "high", "low", "close", "volume"]:
        if col not in df.columns:
            df[col] = None

    # 日期解析
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"], errors="coerce")

    # 数值转换
    numeric_cols = ["open", "high", "low", "close", "volume", "amount", "pre_close", "turnover"]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # 涨跌幅计算（如有 pre_close 和 close）
    if "pct_chg" not in df.columns and "pre_close" in df.columns and "close" in df.columns:
        df["pct_chg"] = ((df["close"] - df["pre_close"]) / df["pre_close"] * 100).round(2)

    # 按日期排序
    df = df.sort_values("date", ascending=True).reset_index(drop=True)

    return df


def normalize_quote(df: pd.DataFrame, source: str) -> pd.DataFrame:
    """将各源实时行情归一化为标准格式。"""
    if df is None or df.empty:
        return pd.DataFrame()

    df = df.copy()
    col_map = _get_quote_col_map(source)
    df = df.rename(columns=col_map)

    numeric_cols = [
        "price", "change", "pct_change", "volume", "amount",
        "open", "high", "low", "pre_close", "bid", "ask",
        "bid_vol", "ask_vol", "pe", "pb", "market_cap",
    ]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    return df


def normalize_financial(df: pd.DataFrame, source: str) -> pd.DataFrame:
    """归一化财务数据。"""
    if df is None or df.empty:
        return pd.DataFrame()

    df = df.copy()
    # 通用处理：列名统一为蛇形命名
    df.columns = [_to_snake_case(str(c)) for c in df.columns]
    return df


def _get_kline_col_map(source: str) -> dict[str, str]:
    """各源 K 线列名 -> 标准列名。"""
    maps = {
        "tencent": {
            "日期": "date", "开盘": "open", "最高": "high",
            "最低": "low", "收盘": "close", "成交量": "volume",
            "成交额": "amount", "涨跌幅": "pct_chg", "涨跌额": "change",
        },
        "ftshare": {
            "t": "date", "o": "open", "h": "high",
            "l": "low", "c": "close", "v": "volume",
            "trade_date": "date", "open": "open", "high": "high",
            "low": "low", "close": "close", "volume": "volume",
            "amount": "amount", "pct_chg": "pct_chg", "pre_close": "pre_close",
        },
        "netease": {
            "日期": "date", "开盘价": "open", "最高价": "high",
            "最低价": "low", "收盘价": "close", "成交量": "volume",
            "成交金额": "amount", "涨跌幅": "pct_chg", "涨跌额": "change",
            "换手率": "turnover", "总市值": "total_cap", "流通市值": "float_cap",
        },
        "sohu": {
            "date": "date", "open": "open", "high": "high",
            "low": "low", "close": "close", "volume": "volume",
            "change": "change", "chg_percent": "pct_chg", "turnover": "turnover",
        },
        "baidu_stock": {
            "time": "date", "open": "open", "high": "high",
            "low": "low", "close": "close", "volume": "volume",
        },
        "yfinance": {
            "Date": "date", "Open": "open", "High": "high",
            "Low": "low", "Close": "close", "Volume": "volume",
            "Adj Close": "adj_close",
        },
        "akshare": {
            "日期": "date", "开盘": "open", "收盘": "close",
            "最高": "high", "最低": "low", "成交量": "volume",
            "成交额": "amount", "振幅": "amplitude", "涨跌幅": "pct_chg",
            "涨跌额": "change", "换手率": "turnover",
        },
        "ths": {
            "time": "date", "open": "open", "high": "high",
            "low": "low", "close": "close", "volume": "volume",
            "amount": "amount", "avg": "vwap",
        },
        "efinance": {
            "日期": "date", "开盘": "open", "收盘": "close",
            "最高": "high", "最低": "low", "成交量": "volume",
            "成交额": "amount", "振幅": "amplitude", "涨跌幅": "pct_chg",
            "涨跌额": "change", "换手率": "turnover",
        },
    }
    return maps.get(source, {})


def _get_quote_col_map(source: str) -> dict[str, str]:
    """各源实时行情列名 -> 标准列名。"""
    maps = {
        "tencent": {
            "name": "name", "price": "price",
            "change": "change", "chg_percent": "pct_change",
            "volume": "volume", "amount": "amount",
            "open": "open", "high": "high", "low": "low", "pre_close": "pre_close",
            "bid": "bid", "ask": "ask", "bid_vol": "bid_vol", "ask_vol": "ask_vol",
            "pe": "pe", "pb": "pb", "market_cap": "market_cap",
            "update_time": "update_time",
        },
        "sina": {
            "symbol": "symbol", "name": "name", "price": "price",
            "change": "change", "pct_change": "pct_change",
            "volume": "volume", "amount": "amount",
            "open": "open", "high": "high", "low": "low", "pre_close": "pre_close",
            "bid": "bid", "ask": "ask", "bid_vol": "bid_vol", "ask_vol": "ask_vol",
        },
        "ftshare": {
            "symbol": "symbol", "name": "name", "price": "price",
            "change": "change", "pct_change": "pct_change",
            "volume": "volume", "amount": "amount",
            "open": "open", "high": "high", "low": "low", "pre_close": "pre_close",
            "pe": "pe", "pb": "pb", "market_cap": "market_cap",
        },
    }
    return maps.get(source, {})


def _to_snake_case(name: str) -> str:
    """将中文/驼峰列名转为蛇形命名。"""
    # 先替换空格和特殊字符为单下划线
    s1 = re.sub(r"[^\w]", "_", name)
    # 再处理驼峰
    s2 = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", s1)
    s3 = re.sub("([a-z0-9])([A-Z])", r"\1_\2", s2)
    # 合并连续下划线
    return re.sub(r"_+", "_", s3).lower().strip("_")
