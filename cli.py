#!/usr/bin/env python3
"""程序化 CLI 入口 - 供其他 Skill 通过子进程调用。"""

import argparse
import json
import sys
from pathlib import Path

# 将项目根目录加入 sys.path，支持直接运行
_PROJECT_ROOT = Path(__file__).parent.resolve()
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from core.fetcher import batch_fetch_with_fallback, fetch_with_fallback
from core.exceptions import FinanceAllInOneError

DATA_TYPE_CHOICES = [
    "stock_quote", "stock_kline", "stock_minute_kline", "stock_depth",
    "stock_ticks", "stock_intraday", "stock_financial", "stock_big_order",
    "stock_holders", "stock_pledge", "share_change",
    "performance_express", "performance_forecast",
    "cb_base", "cb_list",
    "etf_quote", "etf_kline", "index_kline", "futures_quote",
    "option_chain", "news_search", "portfolio_nav", "northbound_flow",
    "china_macro", "us_macro", "margin_trading", "ipo_list",
    "sector_fund_flow", "dragon_tiger", "call_auction", "wencai_screen",
]

MARKET_CHOICES = ["a_share", "hk", "us", "futures", "options", "macro", "news", "xueqiu"]


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Finance All-in-One CLI - 程序化数据获取入口",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python3 cli.py --data-type stock_quote --symbol 600519
  python3 cli.py --data-type stock_kline --symbol AAPL --market us --limit 30 --output json
  python3 cli.py --data-type stock_quote --symbol 贵州茅台 --output md
        """,
    )
    parser.add_argument("--data-type", required=True, choices=DATA_TYPE_CHOICES,
                        help="数据类型")
    parser.add_argument("--symbol", default=None,
                        help="股票代码或自然语言名称（如：600519 / 贵州茅台 / AAPL）")
    parser.add_argument("--symbols", default=None,
                        help="批量查询：逗号分隔的代码列表（如：600519,000001,00700）")
    parser.add_argument("--market", default=None, choices=MARKET_CHOICES,
                        help="市场类型（默认自动推断）")
    parser.add_argument("--period", default="daily",
                        choices=["daily", "weekly", "monthly", "1m", "5m", "15m", "60m"],
                        help="K 线周期（默认: daily）")
    parser.add_argument("--limit", type=int, default=50,
                        help="返回条数（默认: 50）")
    parser.add_argument("--start-date", help="起始日期（YYYY-MM-DD）")
    parser.add_argument("--end-date", help="结束日期（YYYY-MM-DD）")
    parser.add_argument("--output", default="json", choices=["json", "csv", "md"],
                        help="输出格式（默认: json）")
    parser.add_argument("--no-cache", action="store_true",
                        help="禁用缓存")

    args = parser.parse_args()

    # 批量/单条分发
    if args.symbols:
        symbols = [s.strip() for s in args.symbols.split(",") if s.strip()]
        if not symbols:
            print(json.dumps({"error": "InvalidSymbols", "message": "--symbols 参数为空"}, ensure_ascii=False), file=sys.stderr)
            sys.exit(1)
        try:
            results = batch_fetch_with_fallback(
                symbols=symbols,
                data_type=args.data_type,
                market=args.market,
                period=args.period,
                limit=args.limit,
                start_date=args.start_date,
                end_date=args.end_date,
                use_cache=not args.no_cache,
            )
        except FinanceAllInOneError as e:
            error_payload = {"error": type(e).__name__, "message": str(e), "data_type": args.data_type}
            print(json.dumps(error_payload, ensure_ascii=False, indent=2), file=sys.stderr)
            sys.exit(1)
        except Exception as e:
            error_payload = {"error": type(e).__name__, "message": str(e), "data_type": args.data_type}
            print(json.dumps(error_payload, ensure_ascii=False, indent=2), file=sys.stderr)
            sys.exit(2)

        # 批量输出
        if args.output == "json":
            payload = {
                "batch": True,
                "count": len(results),
                "results": [r.to_dict() for r in results],
            }
            print(json.dumps(payload, ensure_ascii=False, indent=2))
        elif args.output == "csv":
            for idx, r in enumerate(results):
                print(f"# symbol: {symbols[idx]} | source: {r.source} | rows: {len(r.data)}")
                print(r.to_csv())
        elif args.output == "md":
            for idx, r in enumerate(results):
                print(f"\n## {symbols[idx]}\n")
                print(r.to_markdown())
        return

    if not args.symbol:
        print(json.dumps({"error": "MissingArgument", "message": "请提供 --symbol 或 --symbols"}, ensure_ascii=False), file=sys.stderr)
        sys.exit(1)

    try:
        result = fetch_with_fallback(
            symbol=args.symbol,
            data_type=args.data_type,
            market=args.market,
            period=args.period,
            limit=args.limit,
            start_date=args.start_date,
            end_date=args.end_date,
            use_cache=not args.no_cache,
        )
    except FinanceAllInOneError as e:
        error_payload = {
            "error": type(e).__name__,
            "message": str(e),
            "symbol": args.symbol,
            "data_type": args.data_type,
        }
        print(json.dumps(error_payload, ensure_ascii=False, indent=2), file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        error_payload = {
            "error": type(e).__name__,
            "message": str(e),
            "symbol": args.symbol,
            "data_type": args.data_type,
        }
        print(json.dumps(error_payload, ensure_ascii=False, indent=2), file=sys.stderr)
        sys.exit(2)

    # 输出格式化
    if args.output == "json":
        print(result.to_json(indent=2))
    elif args.output == "csv":
        print(result.to_csv())
    elif args.output == "md":
        print(result.to_markdown())


if __name__ == "__main__":
    main()
