"""统一数据获取结果容器"""

import json
from dataclasses import dataclass, field
from typing import Any, Optional

import pandas as pd


@dataclass
class FetchResult:
    """所有数据查询函数统一返回的容器。"""

    data: pd.DataFrame
    source: str
    data_type: str
    market: str
    raw_metadata: Optional[dict] = None
    warnings: list[str] = field(default_factory=list)
    cached: bool = False

    def to_dict(self) -> dict[str, Any]:
        """序列化为字典（供 JSON 输出）。"""
        return {
            "data": json.loads(self.data.to_json(orient="records", force_ascii=False)),
            "source": self.source,
            "data_type": self.data_type,
            "market": self.market,
            "raw_metadata": self.raw_metadata,
            "warnings": self.warnings,
            "cached": self.cached,
            "row_count": len(self.data),
        }

    def to_json(self, **kwargs: Any) -> str:
        """序列化为 JSON 字符串。"""
        return json.dumps(self.to_dict(), ensure_ascii=False, **kwargs)

    def to_csv(self, **kwargs: Any) -> str:
        """序列化为 CSV 字符串。"""
        return self.data.to_csv(index=False, **kwargs)

    def to_markdown(self) -> str:
        """序列化为 Markdown 表格。"""
        try:
            md = self.data.to_markdown(index=False)
        except Exception:
            # tabulate 未安装时回退到简单格式
            md = self._simple_markdown()

        lines = [
            f"**数据类型**: {self.data_type} | **市场**: {self.market} | **来源**: {self.source}",
            "",
            md,
            "",
            "---",
        ]
        if self.warnings:
            for w in self.warnings:
                lines.append(f"> ⚠️ {w}")
            lines.append("---")
        if self.cached:
            lines.append("> 💾 数据来自缓存")
        lines.append(f"> 来源：{self.source} | 条数：{len(self.data)}")
        return "\n".join(lines)

    def _simple_markdown(self) -> str:
        """无 tabulate 时的简易 Markdown 表格。"""
        if self.data.empty:
            return "*无数据*"
        cols = list(self.data.columns)
        header = "| " + " | ".join(str(c) for c in cols) + " |"
        separator = "|" + "|".join(" --- " for _ in cols) + "|"
        rows = []
        for _, row in self.data.head(100).iterrows():
            rows.append("| " + " | ".join(str(v) for v in row.values) + " |")
        return "\n".join([header, separator] + rows)
