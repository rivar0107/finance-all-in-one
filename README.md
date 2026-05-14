# Finance All-in-One

免费金融数据统一获取层，支持 A/HK/US 股票、期货、期权、基金、宏观、资讯等全市场数据查询。

> 当前状态：**Alpha / Preview**。接口仍可能调整，外部免费数据源可能限流、失效或变更字段。建议用于个人研究、学习和 Skill 开发实验，不建议直接用于实盘交易或生产级商业数据服务。

## 免责声明

- 本项目只做数据获取与格式归一化，不提供投资建议、交易信号、收益预测或个股推荐。
- 数据来自腾讯、新浪、FTShare、AKShare、yfinance 等第三方公开或免费接口，数据版权、可用性和使用限制归原始数据源所有。
- 免费金融数据源可能出现延迟、缺失、字段变更、限流、地区不可用等情况。使用者需要自行校验数据准确性。
- FTShare 等数据源适配器仅用于个人研究和学习，请在公开、商业或高频使用前自行确认对应服务条款。
- 使用本项目产生的任何投资、交易、合规或数据授权风险，由使用者自行承担。

## 特性

- **零门槛使用**：核心层无需任何注册或 API Key
- **自动路由 + 降级**：按数据类型自动选择最优数据源，主源失败时无缝降级
- **来源透明**：每条结果标注数据来源，降级时给出提示
- **Skill-to-Skill 调用**：支持 Python import 和 CLI 子进程两种调用方式
- **批量查询**：CLI 和 API 均支持一次查询多只股票
- **TTL 缓存**：按数据类型设置不同缓存时间，减少重复请求

## 使用场景（When to Use / When Not to Use）

本节帮助新用户快速判断：什么问题适合用本 Skill，预期会返回什么结果，以及哪些需求不在能力边界内。

### 推荐使用场景

|场景|典型问题（自然语言）|预期输出|说明|
|------|------|------|------|
|盘中快查（单标的）|`茅台今天多少钱？` / `查询 600519 实时行情`|实时行情表格（price、pct_change、volume 等）+ 来源标注|适合快速看现价与涨跌，不做买卖建议|
|多标的横向对比|`查询 600519,000001,00700 实时行情`|多行对比表格 + 统一字段|适合手动比价、看涨跌幅与成交量|
|阶段走势查看（K 线）|`AAPL 近一年日线` / `腾讯控股近30天K线`|按时间序列返回 OHLCV 数据|适合后续自研分析或导出，不内置技术指标结论|
|财务与基本面拉数|`平安银行资产负债表`|结构化财务表（按报告期）+ 来源|适合做财务数据整理、建模输入|
|宏观指标跟踪|`中国最新 CPI` / `美国最新非农`|最新值、时间、来源（不同源字段可能略有差异）|适合建立宏观观察面板或周报素材|
|资讯与公告检索|`搜索 人工智能 财经新闻` / `某公司公告列表`|新闻/公告列表（标题、时间、链接等）|适合信息收集，不做研报观点生成|
|策略研究数据准备|`导出 600519 近3年日线 CSV`|可导出的结构化数据（JSON/CSV）|适合作为回测、因子研究前置数据层|
|Skill 二次开发调用|Python import 或 CLI 子进程调用|标准化 FetchResult + 降级提示|适合在其他 Skill 或脚本中复用数据能力|

### 首次使用建议（新用户）

建议按以下顺序体验，1 分钟内可完成上手：

1. 先查实时：`查询 600519 实时行情`
2. 再看走势：`改成近30天日线`
3. 最后导出：`导出 JSON` 或 `导出 CSV`

这样可以快速理解本 Skill 的三件核心能力：查询、追问、导出。

### 不适用场景（When Not to Use）

以下需求不建议使用本 Skill，或需要接入其他系统：

- **买卖建议/交易信号**：如“现在该不该买”“给我一个涨停策略”
- **自动交易与下单**：如“直接帮我下单”“自动调仓”
- **完整投研报告生成**：如“直接输出可发布深度研报结论”
- **毫秒级实时推送**：如持续 WebSocket 行情推流与事件驱动撮合

### 使用前预期管理（建议放在产品入口处）

- 免费数据源可能出现延迟、限流、字段变更或短时不可用。
- 系统会自动降级到备用源，并明确提示来源变化。
- 不同数据源口径可能有细微差异；重要决策前请自行交叉校验。

## 快速开始

```bash
# 1. 安装核心依赖
pip3 install -r requirements.txt

# 可选：以可编辑模式安装当前项目
pip3 install -e .

# 2. 进入项目目录
cd finance-all-in-one

# 3. CLI 查询茅台实时行情
python3 cli.py --data-type stock_quote --symbol 600519 --output md

# 4. CLI 批量查询多只股票的实时行情
python3 cli.py --data-type stock_quote --symbols 600519,000001,00700 --output md

# 5. Python 查询
python3 -c "
from api import get_stock_quote
r = get_stock_quote('600519')
print(r.to_markdown())
"
```

## 目录结构

```text
finance-all-in-one/
├── cli.py                 # 程序化 CLI 入口
├── api.py                 # 纯函数 API 聚合
├── config.py              # 路由表与配置
├── core/                  # 核心引擎
│   ├── router.py          # 意图路由
│   ├── fetcher.py         # 统一获取 + 降级
│   ├── normalizer.py      # 数据归一化
│   ├── cache.py           # TTL 缓存
│   ├── result.py          # FetchResult 数据模型
│   └── exceptions.py      # 自定义异常
├── sources/               # 数据源适配器
│   ├── tencent.py         # 腾讯财经
│   ├── sina.py            # 新浪财经
│   └── ...
├── data_types/            # 面向用户的数据接口
│   ├── stock.py           # A股
│   ├── hk.py              # 港股
│   ├── futures.py         # 期货
│   └── ...
└── tests/                 # 测试
```

## 数据源矩阵

|数据类型|P0|P1|P2|P3|P4|
|---------|----|----|----|----|----|
|A股实时行情|腾讯|新浪|FTShare|efinance|AKShare|
|A股K线|FTShare|腾讯|网易|AKShare / Baostock|—|
|A股分钟K线|同花顺(thsdk)|—|—|—|—|
|A股盘口(Level-2)|同花顺(thsdk)|mootdx|—|—|—|
|A股逐笔(Tick)|mootdx|—|—|—|—|
|A股大单流向|同花顺(thsdk)|—|—|—|—|
|A股集合竞价|同花顺(thsdk)|—|—|—|—|
|A股财务|FTShare|网易|AKShare|Baostock|Tushare|
|A股龙虎榜|AKShare|Tushare|—|—|—|
|A股融资融券|FTShare|AKShare|Tushare|—|—|
|A股股东数据|FTShare|—|—|—|—|
|A股股权质押|FTShare|—|—|—|—|
|A股股本变动|FTShare|—|—|—|—|
|A股业绩快报|FTShare|—|—|—|—|
|A股业绩预告|FTShare|—|—|—|—|
|A股可转债基础|FTShare|—|—|—|—|
|A股可转债列表|FTShare|—|—|—|—|
|美股实时|腾讯|新浪|yfinance|Alpaca(有Key)|Twelve Data(有Key)|
|美股K线|yfinance|腾讯|AKShare|Alpaca(有Key)|Twelve Data(有Key)|
|美股基本面|yfinance|FMP(有Key)|—|—|—|
|港股实时|腾讯|新浪|FTShare|yfinance|—|
|期货行情|腾讯|AKShare|同花顺(thsdk)|—|—|
|宏观数据|FTShare|AKShare|Finnhub(有Key)|FMP(有Key)|—|
|新闻搜索|FTShare|—|—|—|—|
|公告/研报|FTShare|—|—|—|—|
|雪球组合净值|雪球(pysnowball)|—|—|—|—|
|北向资金|雪球(pysnowball)|AKShare|—|—|—|

> 注：AKShare 的 A 股实时行情接口（基于东方财富）近期不稳定，已在路由中下调优先级至最后。

## 技术栈

- Python 3.9+
- pandas（数据处理）
- requests（HTTP 直连）
- pytest（测试）

## 测试

```bash
# 单元测试，适合 CI，默认不依赖真实外部接口稳定性
pytest tests -q --ignore=tests/e2e

# 真实外部数据源连通性测试，可能因网络、限流或第三方接口波动而 skip
pytest tests/e2e -q
```

## 数据源稳定性说明

单元测试使用 mock 或本地逻辑验证，应该作为提交前的硬门禁。`tests/e2e/` 会直接访问真实第三方数据源，主要用于人工验收或定期巡检；当外部接口暂不可用、限流或网络异常时，测试会跳过而不是阻塞 CI。

## License

MIT
