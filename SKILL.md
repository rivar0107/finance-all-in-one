---
name: finance-all-in-one
description: 免费金融数据统一获取层，支持 A/HK/US 股票、期货、期权、基金、宏观、资讯等全市场数据查询。自动路由 + 分级降级，零门槛使用。返回结构化 DataFrame 并标注数据来源。也可被其他 Skill 通过 import 或 CLI 调用。
metadata:
  {
    "openclaw": {
      "requires": {
        "env": ["TUSHARE_TOKEN", "ALPACA_API_KEY", "ALPACA_SECRET_KEY", "FINNHUB_API_KEY", "FMP_API_KEY", "TWELVE_DATA_API_KEY", "JRJ_API_KEY", "EM_API_KEY"]
      },
      "install": [
        {
          "id": "pip-deps",
          "kind": "python",
          "package": "pandas requests rich akshare efinance yfinance thsdk mootdx baostock pysnowball",
          "label": "核心层依赖"
        },
        {
          "id": "pip-enhanced",
          "kind": "python",
          "package": "tushare alpaca-trade-api finnhub-python fmpsdk twelvedata",
          "label": "增强层依赖（按需）"
        }
      ],
      "cli": {
        "entry": "python3 {baseDir}/cli.py",
        "args": ["--data-type", "--symbol", "--symbols", "--market", "--period", "--limit", "--start-date", "--end-date", "--output", "--no-cache"]
      }
    }
  }
---

# Finance All-in-One

**Finance All-in-One** 是一个纯数据获取型 Skill，专注为用户提供**免费的**股票、期货、期权、基金、宏观经济及金融资讯等全市场数据查询能力。

- **核心任务**：根据用户意图，自动选择最优免费数据源，获取并归一化输出结构化数据
- **非核心任务（明确不做）**：技术分析、评分、买卖信号、交易下单、投研报告生成
- **设计哲学**："数据层透明、来源可追溯、降级无感知"

## 功能范围

### 支持查询的对象

- 股票（A 股、港股、美股）
- ETF、指数、基金
- 期货、期权
- 宏观经济指标（中国/美国）
- 新闻、公告、研报
- 雪球组合、北向资金

### 支持查询的数据类型

- **实时行情**（现价、涨跌幅、盘口、PE/PB/市值）
- **K 线数据**（日线/周线/月线/分钟线）
- **财务数据**（利润表、资产负债表、现金流量表）
- **板块/资金**（板块资金流向、龙虎榜、融资融券）
- **股东/股本**（十大股东、十大流通股东、股东户数、股权质押、股本变动）
- **业绩/预告**（业绩快报、业绩预告）
- **可转债**（可转债基础数据、可转债列表）
- **期货/期权**（行情、K线、持仓、期权链）
- **宏观数据**（GDP、CPI、PMI、LPR、非农数据等）
- **资讯**（新闻搜索、公告列表、研报列表、实时快讯）

### 输出格式

- 默认返回结构化表格（Markdown）
- 支持 JSON / CSV 输出（CLI 方式）
- 每条结果标注数据来源和降级提示

---

## 触发条件

当用户询问以下类型问题时调用此 Skill：

- "茅台今天多少钱？"
- "查询 600519 的实时行情"
- "贵州茅台近 30 天日线"
- "平安银行资产负债表"
- "半导体板块资金流向"
- "腾讯控股行情"
- "AAPL 近一年 K 线"
- "螺纹钢期货行情"
- "中国最新 CPI"
- "搜一下人工智能相关新闻"
- "茅台的十大股东是谁"
- "平安银行股权质押情况"
- "查询 600519 业绩快报"
- "可转债列表"
- "某雪球组合净值"

---

## 使用方法

### 自然语言查询（用户直接提问）

用户直接输入查询意图，Skill 自动解析并返回数据：

```
用户: 茅台今天多少钱？
→ 调用 get_stock_quote("600519") → 返回实时行情表格

用户: 贵州茅台近 30 天 K 线
→ 调用 get_stock_kline("600519", limit=30) → 返回 K 线数据

用户: 查询 AAPL 实时行情
→ 调用 get_stock_quote("AAPL", market="us") → 返回美股行情
```

### 程序化调用（其他 Skill 调用）

#### 路径 A：Python import（同进程，推荐）

```python
from finance_all_in_one.api import get_stock_quote, get_stock_kline, batch_fetch_with_fallback

# 单条查询
result = get_stock_quote("600519")
print(result.to_json(indent=2))

# 批量查询
results = batch_fetch_with_fallback(
    symbols=["600519", "000001", "00700"],
    data_type="stock_quote",
    max_workers=3,
)
for r in results:
    print(f"{r.market} | {r.source} | {len(r.data)} rows")
```

#### 路径 B：CLI 子进程（跨 Skill，解耦）

```bash
# 单条查询
python3 skills/finance-all-in-one/cli.py \
  --data-type stock_quote \
  --symbol 600519 \
  --market a_share \
  --output json

# 批量查询（逗号分隔）
python3 skills/finance-all-in-one/cli.py \
  --data-type stock_quote \
  --symbols 600519,000001,00700 \
  --output json
```

---

## 数据源与路由

本 Skill 使用**多层数据源 + 自动降级**机制：

|层级|数据源|是否需要 Key|特点|
|------|--------|-------------|------|
|HTTP 核心层|腾讯财经、新浪财经|否|毫秒级，稳定性最高|
|HTTP 核心层|网易、搜狐、百度、东方财富|否|历史 K 线、复权、分时、换手率|
|库封装核心层|AKShare、efinance、yfinance|否|pip 安装即用，覆盖广|
|库封装核心层|同花顺(thsdk)、mootdx|否|盘口、Tick、分钟 K 线、大单、竞价异动|
|库封装核心层|Baostock|否|A 股历史 K 线（支持复权）、季频财务数据|
|库封装核心层|雪球(pysnowball)|否|组合净值、调仓记录、北向资金|
|可选增强层|FTShare、Tushare、Alpaca、Finnhub、FMP 等|是（免费注册）|深度数据、美股实时、宏观、新闻|

**降级示例**：

- 查询 A 股实时行情：腾讯 -> 新浪 -> FTShare -> efinance -> Tushare(有Key) -> AKShare
- 查询 A 股 K 线：FTShare -> 腾讯 -> 网易 -> AKShare -> Baostock -> Tushare(有Key)
- 查询美股实时行情（有 Alpaca Key）：Alpaca -> Twelve Data -> 腾讯 -> 新浪 -> yfinance
- 查询美股实时行情（无 Key）：腾讯 -> 新浪 -> yfinance
- 查询股东/质押/股本/业绩/可转债：FTShare（独有数据能力，暂无替代源）

---

## 依赖安装

```bash
# 核心依赖（必须）
pip3 install pandas requests rich

# 库封装核心层（强烈建议）
pip3 install akshare efinance yfinance thsdk mootdx baostock pysnowball

# 可选增强层（按需）
pip3 install tushare alpaca-trade-api finnhub-python fmpsdk tiingo httpx
```

---

## 环境变量（可选增强层）

```bash
export TUSHARE_TOKEN="your_token"
export ALPACA_API_KEY="your_key"
export ALPACA_SECRET_KEY="your_secret"
export FINNHUB_API_KEY="your_key"
export FMP_API_KEY="your_key"
export TWELVE_DATA_API_KEY="your_key"
```

---

## 输出示例

### 实时行情

```text
**数据类型**: stock_quote | **市场**: a_share | **来源**: tencent

|symbol|name|price|change|pct_change|volume|amount|open|high|low|pre_close|pe|pb|
|----------|--------|--------|--------|------------|-----------|-----------|--------|--------|--------|-----------|-------|------|
|sh600519|贵州茅台|1775.0|15.0|0.85|1234500.0|2185000.0|1765.0|1780.0|1760.0|1760.0|28.52|8.15|

---
> 来源：tencent | 条数：1
```

### 降级提示

```text
⚠️ 提示：腾讯财经请求超时（10s），已自动降级至新浪财经。
数据可能存在细微差异，建议稍后重试。
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
数据来源：新浪财经（降级）
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## 边界说明（明确不做）

|不做|理由|
|------|------|
|交易下单|涉及资金安全，超出数据层边界|
|技术分析/评分|用户定位是纯数据获取|
|买卖建议/信号|合规风险，且与数据层无关|
|实时推送/WebSocket|架构复杂度高，非查询场景|
|深度回测|需要大量历史数据和计算资源|

---

## 测试

```bash
pytest tests/ -v
```
