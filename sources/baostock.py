"""Baostock 适配器

免费 A 股数据接口，支持历史 K 线、财务数据。
特点：无需注册、数据质量高、支持前/后复权。
覆盖：A 股历史 K 线、季频财务数据（盈利/偿债/现金流）
"""

from typing import Optional

import pandas as pd

# 懒加载
_bs = None


def _get_bs():
    global _bs
    if _bs is None:
        import baostock
        _bs = baostock
    return _bs


class BaostockAdapter:
    """Baostock 数据适配器"""

    name = "baostock"
    requires_key = False

    @classmethod
    def is_available(cls) -> bool:
        try:
            _get_bs()
            return True
        except ImportError:
            return False

    @classmethod
    def _to_bs_code(cls, symbol: str) -> str:
        """转换为 baostock 代码格式：sh.xxxxxx / sz.xxxxxx。"""
        s = str(symbol).strip().lower()
        if s.startswith(("sh.", "sz.", "bj.")):
            return s
        if s.startswith("sh"):
            return f"sh.{s[2:].zfill(6)}"
        if s.startswith("sz"):
            return f"sz.{s[2:].zfill(6)}"
        # 纯数字，按前缀推断
        s = s.zfill(6)
        if s.startswith(("6", "68", "88", "51", "50", "56", "58", "11", "12")):
            return f"sh.{s}"
        return f"sz.{s}"

    @classmethod
    def _login_logout(cls):
        """上下文管理器辅助：登录/登出。"""
        bs = _get_bs()
        lg = bs.login()
        if lg.error_code != "0":
            raise RuntimeError(f"Baostock login failed: {lg.error_msg}")
        try:
            yield bs
        finally:
            bs.logout()

    @classmethod
    def fetch_kline(
        cls,
        symbol: str,
        period: str = "daily",
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        adjust: str = "qfq",
        **kwargs,
    ) -> pd.DataFrame:
        """获取历史 K 线数据。"""
        bs = _get_bs()
        code = cls._to_bs_code(symbol)

        period_map = {"daily": "d", "weekly": "w", "monthly": "m"}
        freq = period_map.get(period, "d")

        adjust_map = {"": "3", "qfq": "2", "hfq": "1"}
        adjust_flag = adjust_map.get(adjust, "2")

        if end_date is None:
            import datetime
            end_date = datetime.date.today().strftime("%Y-%m-%d")
        if start_date is None:
            import datetime
            # 按 period 估算天数
            days = 50 * 2 if freq == "d" else 50 * 14
            start_date = (datetime.date.today() - datetime.timedelta(days=days)).strftime("%Y-%m-%d")

        lg = bs.login()
        if lg.error_code != "0":
            return pd.DataFrame()

        try:
            fields = (
                "date,code,open,high,low,close,preclose,volume,amount,"
                "adjustflag,turn,tradestatus,pctChg,isST"
            )
            rs = bs.query_history_k_data_plus(
                code,
                fields,
                start_date=start_date,
                end_date=end_date,
                frequency=freq,
                adjustflag=adjust_flag,
            )
            if rs.error_code != "0":
                return pd.DataFrame()

            rows = []
            while (rs.error_code == "0") and rs.next():
                rows.append(rs.get_row_data())

            df = pd.DataFrame(rows, columns=rs.fields)
            # 数值转换
            numeric_cols = ["open", "high", "low", "close", "preclose", "volume", "amount", "turn", "pctChg"]
            for col in numeric_cols:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors="coerce")
            return df
        finally:
            bs.logout()

    @classmethod
    def fetch_financial(cls, symbol: str, report_type: str = "income", **kwargs) -> pd.DataFrame:
        """获取季频财务数据。

        report_type 映射:
        - income       → 季频盈利能力
        - balance      → 季频偿债能力
        - cash_flow    → 季频现金流量
        - growth       → 季频成长能力
        - operation    → 季频运营能力
        """
        bs = _get_bs()
        code = cls._to_bs_code(symbol)

        type_map = {
            "income": bs.query_profit_data,
            "balance": bs.query_balance_data,
            "cash_flow": bs.query_cash_flow_data,
            "growth": bs.query_growth_data,
            "operation": bs.query_operation_data,
        }
        query_fn = type_map.get(report_type)
        if query_fn is None:
            return pd.DataFrame()

        lg = bs.login()
        if lg.error_code != "0":
            return pd.DataFrame()

        try:
            year = kwargs.get("year")
            quarter = kwargs.get("quarter")
            rs = query_fn(code=code, year=year, quarter=quarter)
            if rs.error_code != "0":
                return pd.DataFrame()

            rows = []
            while (rs.error_code == "0") and rs.next():
                rows.append(rs.get_row_data())
            return pd.DataFrame(rows, columns=rs.fields)
        finally:
            bs.logout()

    @classmethod
    def fetch(cls, data_type: str, **kwargs) -> pd.DataFrame:
        if "kline" in data_type:
            return cls.fetch_kline(**kwargs)
        if data_type == "stock_financial":
            return cls.fetch_financial(**kwargs)
        return pd.DataFrame()


Adapter = BaostockAdapter
