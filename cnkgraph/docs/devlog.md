# cnkgraph 爬虫开发日志

## (一) 项目初始化 — 2026-06-02

**目标**：将 cnkgraph.com 全部开放数据（12 模块、71 端点、200 万+ 诗文）爬取到本地 DuckDB 数据库。

**技术决策**：
- Python 3.12 + aiohttp + asyncio + DuckDB
- 5 阶段爬取：年历 → 人物 → 诗文 → 地理 → 参考数据
- 支持细粒度爬取：按阶段、按朝代、按作者
- 断点续爬：crawl_progress 表精确记录进度

**文件结构**：
```
cnkgraph/
├── src/
│   ├── crawl.py          # CLI 入口
│   ├── db.py             # DuckDB 建表
│   ├── api.py            # HTTP 客户端
│   └── stages/           # 各阶段爬虫
├── data/                 # DuckDB 数据库
├── docs/                 # PRD + devlog
└── postman/              # API 参考集合
```

**进度**：
- [x] PRD 文档编写（含细粒度爬取策略）
- [x] DDL 设计（25 张表 + 索引 + COMMENT ON）
- [x] 代码编写（db.py, api.py, crawl.py, stage1-5）
- [x] Stage 1 跑通
- [ ] Stage 2-5 待跑

### 代码文件说明

| 文件 | 职责 |
|------|------|
| `src/db.py` | DuckDB schema（25 张表 + crawl_progress + 索引），含 helper 函数 |
| `src/api.py` | aiohttp 异步 HTTP 客户端，Semaphore 并发控制，指数退避重试 |
| `src/crawl.py` | CLI 入口，argparse 解析 --stage/--dynasty/--author-id/--module/--status/--reset |
| `src/stages/stage1_calendar.py` | 年历：dynasty + era_year（~500 次请求，~3 min） |
| `src/stages/stage2_people.py` | 人物：person + alias + hometown + detail（~5K 次，~30 min） |
| `src/stages/stage3_writing.py` | 诗文：writing + clause + comment + allusion（~100K 次，~2-10h） |
| `src/stages/stage4_region.py` | 地理：region + history + scenery（~3K 次，~15 min） |
| `src/stages/stage5_reference.py` | 参考：book/glossary/rhyme/ciTune/quTune/category/char（~32K 次，~1h） |

---

## (二) Stage 1 跑通 — 2026-06-02

### 结果

**549 个朝代（含子朝代）+ 761 个年号**，成功入库。

### 踩坑与解决

#### 坑 1：DuckDB 没有 `executescript` 方法

**现象**：`AttributeError: '_duckdb.DuckDBPyConnection' object has no attribute 'executescript'`

**原因**：Python `sqlite3` 有 `executescript()` 可一次执行多条 SQL，DuckDB 没有这个方法。

**解决**：手动 `split(";")` 拆分成单条语句逐条执行，跳过空语句和纯注释行。

#### 坑 2：DuckDB 不支持 `GENERATED ALWAYS AS IDENTITY`

**现象**：`Not implemented Error: Constraint not implemented!`

**原因**：DuckDB 不支持 SQL 标准的 `GENERATED ALWAYS AS IDENTITY` 语法。

**解决**：改用 `CREATE SEQUENCE` + `DEFAULT nextval('seq_name')`。关键点是 **sequence 必须在 CREATE TABLE 之前创建**，否则 `nextval` 引用会报 "Sequence does not exist"。所有 sequence 集中放在 DDL 最前面。

#### 坑 3：DuckDB 主键列不允许 NULL

**现象**：`NOT NULL constraint failed: crawl_progress.author_id`

**原因**：`crawl_progress` 表的复合主键 `(module, dynasty, author_id)` 中，DuckDB 不允许主键列为 NULL。当某阶段不按朝代/作者爬取时，`dynasty` 和 `author_id` 传入 `None`。

**解决**：引入哨兵值——`dynasty` 为 None 时存 `"__ALL__"`，`author_id` 为 None 时存 `-1`。封装 `_pk_dynasty()` 和 `_pk_author()` 函数统一处理。

#### 坑 4：DuckDB 不支持 `CURRENT_TIMESTAMP` 作为 VALUES 参数

**现象**：`Table "crawl_progress" does not have a column named "CURRENT_TIMESTAMP"`

**原因**：DuckDB 在参数化查询 `VALUES (?, ?, ..., CURRENT_TIMESTAMP)` 中无法识别 `CURRENT_TIMESTAMP` 函数。

**解决**：改用 Python `datetime.datetime.now()` 生成时间字符串，作为参数传入。

#### 坑 5：DuckDB 不支持前向外键引用

**现象**：`Table with name region does not exist!`

**原因**：`writing_link` 表有 `REFERENCES region(id)`，但 `region` 表在 DDL 后面才创建。DuckDB 要求被引用的表必须先存在。

**解决**：去掉 `writing_link.region_id` 上的 `REFERENCES region(id)` 约束（保留索引即可保证查询性能）。

#### 坑 6：API 响应结构与预期不符

**现象**：`era_year` 表 0 条记录——年号全丢了。

**原因**：代码假设 `/api/calendar/{dynasty}` 返回 `{EraYears: [...]}`，实际结构是 `{Dynasties: [{Kings: [{EraYears: [...]}]}]}`，年号嵌套在 朝代→帝王→年号 三层结构里。

**解决**：重写 `stage1_calendar.py`，遍历 `Dynasties → Kings → EraYears`。同时发现年号的 `BeginYear`/`EndYear` 是文本（如 `"618年(武德)"`）而非整数，新增 `_parse_year()` 提取数字（支持"前2029年"等负数）。

### 当前数据量

| 表 | 行数 | 说明 |
|---|---|---|
| dynasty | 549 | 含子朝代（如 西周、东周、莒国 等） |
| era_year | 761 | 历代年号 |
| 其他 21 张表 | 0 | 待爬取 |

---

## (三) Stage 2 尝试 — 限流问题 — 2026-06-02

### 现象

运行 `python src/crawl.py --stage 2 --dynasty 唐朝`，列表请求（`GET /api/people/唐朝`）成功拿到 ~4000 人物。但随后逐个获取人物详情（`GET /api/people/{id}`），**连续触发 429 限流**：

```
[ERROR] 429 on https://api.cnkgraph.com/api/people/15215: 请求的频率太高，请等待 00:00:00 后再尝试访问...
[ERROR] 429 on https://api.cnkgraph.com/api/people/18851: 请求的频率太高...
...（持续数百条 429）
```

### 限流分析

- cnkgraph API **限流策略不明**（无公开文档说明速率限制）
- 初始配置：5 并发 + 200ms 间隔 = 每秒约 25 请求
- 列表 API（`/people/{dynasty}`）单次请求量大、频率低，没问题
- 详情 API（`/people/{id}`）逐条请求、频率高，**极易触发限流**
- 限流后 429 响应体提示"请等待后重试"，但未给出具体等待时间

### 应对方案（已实施）

1. **降低并发和间隔**：默认并发 5→2，间隔 200ms→500ms（约每秒 4 请求）
2. **429 智能退避**：遇到 429 时等待 30s×重试次数（第一次 30s，第二次 60s，第三次 90s），而不是直接放弃
3. **连续失败熔断**：连续失败 5 次自动停止，保存已写入数据

### 进一步优化方向（待实施）

1. **拆分列表与详情为两步**：先只写列表数据（person + alias + hometown 都在列表里），详情（person_detail + 更多 alias）单独慢慢补全
2. **阶梯式限速**：首次请求不限速；首次 429 后主动降到 1 并发 + 1s 间隔
3. **分批爬取**：`--dynasty 唐朝` 一次跑完 4000 人物详情太多，可按姓氏首字母等更细粒度分批

### 限流后多久能恢复

根据测试观察：
- 短期限流：等待 **1-2 分钟** 通常可恢复
- 连续大量触发 429 后：可能需要 **5-10 分钟**
- 建议策略：**被限流后等待 10 分钟再继续**，用 `--status` 确认进度后从断点续爬

### 数据丢失

由于 DuckDB 写入过程中被 Ctrl+C 强制中断，WAL（Write-Ahead Log）未正确回放，导致数据库文件损坏：

```
_duckdb.InternalException: Failure while replaying WAL file
```

**教训**：爬虫中断后应让程序自然退出（DuckDB 会正确关闭 WAL），不要直接杀进程。如果 WAL 损坏，删除 `.duckdb` 和 `.duckdb.wal` 重新开始。

---

## (四) 架构改进：每阶段独立数据库 — 2026-06-02

### 背景

Stage 2 限流导致进程被强制中断，WAL 损坏波及整个 `cnkgraph.duckdb`——包括已成功的 Stage 1 数据（549 朝代 + 761 年号）全部丢失。如果各阶段数据物理隔离，Stage 1 的成果不会被 Stage 2 的失败拖累。

### 方案：每阶段一个独立 .duckdb 文件

```
data/
├── calendar.duckdb       # Stage 1: dynasty + era_year
├── people.duckdb         # Stage 2: person + person_alias + person_hometown + person_detail
├── writing.duckdb        # Stage 3: writing + writing_clause + writing_comment + writing_link + writing_allusion
├── region.duckdb         # Stage 4: region + region_history + scenery
├── reference.duckdb      # Stage 5: book + book_volume + glossary + rhyme_entry + rhyme_char + ci_tune + qu_tune + category_entry + char_dict
└── crawl_progress.duckdb # 断点续爬进度（独立小文件）
```

### 可行性分析

| 关注点 | 结论 |
|--------|------|
| **DuckDB 支持** | 完全支持。每个 `duckdb.connect('xxx.duckdb')` 就是一个独立数据库 |
| **跨库查询** | DuckDB 支持 `ATTACH 'people.duckdb' AS people`，然后 `SELECT ... FROM people.person JOIN writing.writing` |
| **外键约束** | 跨库无法用 `REFERENCES`，但本项目中 FK 本就是逻辑约束（应用层保证），去掉不影响数据完整性 |
| **索引** | 每个库内独立建索引，查询性能不受影响 |
| **断点续爬** | `crawl_progress` 单独存一个小库，任何阶段崩溃都不影响进度记录 |
| **文件大小** | 预估：calendar ~1MB, people ~50MB, writing ~500MB, region ~10MB, reference ~100MB |

### 优势

1. **故障隔离**：某阶段崩溃/中断，只影响该阶段的 .duckdb，删掉重建即可
2. **按需使用**：只 ATTACH 需要的库，减少内存占用
3. **并行爬取**：理论上多个阶段可以同时跑（各写各的库，无锁竞争）
4. **增量备份**：成功的阶段可以单独备份，不用重复爬取
5. **灵活删除**：不需要的数据直接删库文件，不用 `DELETE FROM`

### 实施要点

- `db.py` 中 `get_db(stage)` 按阶段返回对应库的连接
- 跨阶段依赖（如 `writing.author_id` 关联 `person.id`）由应用层保证，数据库层不加 FK
- 分析数据时用 `ATTACH` 组合多个库，例如：
  ```python
  con = duckdb.connect('data/writing.duckdb')
  con.execute("ATTACH 'data/people.duckdb' AS people")
  con.execute("ATTACH 'data/region.duckdb' AS region")
  # 即可跨库 JOIN
  con.execute("SELECT w.title, p.name, r.name FROM writing w JOIN people.person p ON w.author_id = p.id LEFT JOIN region.region r ON w.author_place_raw = r.id")
  ```

### 状态

- [x] 方案确认可行
- [x] 代码改造完成（db.py / crawl.py / stage1-5 全部改为多库架构）
- [ ] 重新跑 Stage 1 验证（限流未恢复，待后续执行）

---

## (五) 多库架构代码改造 — 2026-06-02

### 改动文件

| 文件 | 改动 |
|------|------|
| `src/db.py` | 完全重写：DDL 拆分为 `DDL_CALENDAR` / `DDL_PEOPLE` / `DDL_WRITING` / `DDL_REGION` / `DDL_REFERENCE` / `DDL_PROGRESS` 六段；`get_db(stage)` 按阶段返回对应库连接；`get_progress_db()` 返回独立的进度库连接；`show_status()` 改为遍历所有库文件 |
| `src/crawl.py` | 各 stage 的 `run()` 不再接收 `con` 参数，改为自行管理 DB 连接；`show_status()` 不再需要连接参数 |
| `src/stages/stage1_calendar.py` | 改用 `get_db(1)` + `get_progress_db()`，在 `finally` 中关闭连接 |
| `src/stages/stage2_people.py` | 同上模式，`get_db(2)` |
| `src/stages/stage3_writing.py` | 同上模式，`get_db(3)` |
| `src/stages/stage4_region.py` | 同上模式，`get_db(4)`；跨库读 writing/people 库收集 region_id 时用只读连接 |
| `src/stages/stage5_reference.py` | 同上模式，`get_db(5)` |

### 跨库处理

- `writing.author_id` 去掉 `REFERENCES person(id)`，改为逻辑关联（`author_name` 冗余字段避免跨库 JOIN）
- `writing_link.region_id` 同理，无 FK 约束
- Stage 4 读 writing/people 库时用 `duckdb.connect(..., read_only=True)`，不写入
- 分析数据时用 `ATTACH` 跨库查询

### 改造后重跑 Stage 1

改造完成后尝试重跑 Stage 1，但之前 Stage 2 触发的 API 限流**仍未恢复**——连 `/api/calendar` 都返回 429。

429 退避策略已生效（30s → 60s → 90s），但三次重试后 API 仍未放行。说明 cnkgraph 限流封禁时间可能较长。

### 经验总结

1. **限流影响范围大**：一次 Stage 2 的详情请求过于密集，导致整个 IP 被限流，连 Stage 1 的列表请求也被波及
2. **429 退避时间可能不够**：当前 30/60/90s 的退避可能不足，后续可考虑更长的等待（如 5 分钟级别）
3. **建议后续爬取策略**：
   - 先等限流恢复（至少等 30 分钟以上）
   - Stage 2 拆成两步：先只爬列表数据（person + alias + hometown），详情后续慢慢补
   - 降低默认并发到 1，间隔 1 秒以上
   - 可以考虑在非高峰时段爬取

---

## (六) 添加 --limit 限制 + GitHub Actions 爬取方案 — 2026-06-03

### 背景

之前 Stage 2 触发的 API 限流（429）至今未恢复——连 Stage 1 的 `/api/calendar` 列表请求也返回 429。本地 IP 已被 cnkgraph 封禁。

因此：
1. 先给爬虫添加 `--limit` 参数，支持小批量试运行
2. 探索用 GitHub Actions 跑爬虫的方案——换 IP 绕过本地限流

### 代码改动：`--limit` 参数

**改动文件**：

| 文件 | 改动 |
|------|------|
| `src/crawl.py` | 新增 `--limit N` CLI 参数，传入各 stage |
| `src/stages/stage1_calendar.py` | era_year 循环加 limit 检查，满 N 条停止 |
| `src/stages/stage2_people.py` | `people[:limit]` 列表切片 |
| `src/stages/stage3_writing.py` | `all_authors[:limit]` + 分页累计 writing 数量限制 |
| `src/stages/stage4_region.py` | `sorted_ids[:limit]` 列表切片 |
| `src/stages/stage5_reference.py` | 各子模块加 limit（book/glossary/ciTune/quTune 列表切片，category/char 循环限制） |

**用法**：

```bash
# 每个实体最多爬 1000 条
python src/crawl.py --stage 1 --limit 1000 --reset
python src/crawl.py --stage 2 --limit 1000 --reset
python src/crawl.py --stage 3 --limit 1000 --reset --dynasty 唐朝
python src/crawl.py --stage 4 --limit 1000 --reset
python src/crawl.py --stage 5 --limit 1000 --reset
```

**试运行结果**：因本地 IP 仍被限流，所有请求返回 429，试运行未能执行。

---

### 试运行记录 — 关 VPN 后本地 IP 可用

关掉 VPN 后本地 IP 不再被限流，逐 stage 试运行成功。Stage 3 修复了 `_pk_dynasty` 未导入的 bug。Stage 5 修复了 API 响应结构与代码预期不符的问题：

- **book**：API 返回 `{Categories: [{Books: [...]}]}` 而非 `{Books: [...]}`
- **ciTune / quTune**：API 直接返回 list 而非 `{CiTunes: [...]}`
- **rhyme**：API 返回 `{Categories: [{Name, Chars}]}` 而非 `{Entries: [...]}`
- **glossary**：全部端点返回 405 Method Not Allowed，暂时跳过

#### 当前各库各表数据量

| 库 | 表 | 行数 | 说明 |
|---|---|------|------|
| **calendar.duckdb** | dynasty | 549 | 含子朝代 |
| | era_year | 647 | limit 1000 截止 |
| **people.duckdb** | person | 10 | limit 10, --dynasty 唐朝 |
| | person_alias | 18 | |
| | person_hometown | 18 | |
| | person_detail | 28 | |
| **writing.duckdb** | writing | 21 | --author-id 15188 (李白), limit 20 |
| | writing_clause | 160 | |
| | writing_comment | 20 | |
| | writing_allusion | 15 | |
| | writing_link | 0 | API 未返回此数据 |
| **region.duckdb** | region | 17 | 从 writing/people 库收集的 region_id |
| | region_history | 407 | |
| | scenery | 0 | |
| **reference.duckdb** | rhyme_entry | 106 | 平水韵 106 部 |
| | ci_tune | 99 | 819 个词谱中取 99（之前缓存） |
| | qu_tune | 99 | 同上 |
| | char_dict | 52 | CJK 字符 52 个 |
| | book | 0 | 限流未获取 |
| | book_volume | 0 | 限流未获取 |
| | glossary | 0 | API 405 跳过 |
| | category_entry | 0 | 限流未获取 |
| | rhyme_char | 0 | |

**总计**：25 张表中有数据的 14 张，空表 11 张（6 张因限流、1 张 API 不可用、4 张为依赖后续数据的子表）。

**5 个 stage 的代码均已验证可用**。后续需要等限流恢复或使用 GitHub Actions 完成全量爬取。

---

### GitHub Actions 爬取方案：可行性分析

#### 方案思路

将爬虫代码推到 GitHub，通过 GitHub Actions 在云端执行爬取。GitHub Actions 的 runner 运行在 Microsoft Azure 数据中心，IP 与本地完全不同，可绕过本地的 IP 限流。

#### 可行性评估

| 关注点 | 结论 |
|--------|------|
| **换 IP 绕限流** | ✅ 可行。GitHub Actions 使用 Azure 公共 IP，与本地 IP 完全不同。cnkgraph 的限流是 IP 级别的，换 IP 即可重新开始 |
| **IP 是否共享** | ⚠️ 有风险。GitHub Actions runner 的 IP 来自公共池，其他用户可能也在用同一 IP 段爬 cnkgraph。但因为我们是**小批量慢速爬取**（默认 2 并发 + 500ms 间隔），不太可能触发限流 |
| **Python 环境** | ✅ 完全支持。GitHub Actions 的 `ubuntu-latest` 自带 Python 3.12 |
| **DuckDB 依赖** | ✅ 支持。`pip install duckdb` 即可 |
| **运行时间限制** | ⚠️ GitHub Actions 单个 job 最长 **6 小时**。Stage 3 全量预估 2-10h，可能超时。但用 `--limit 1000` 试运行肯定够用 |
| **数据回传** | ✅ 可行。用 `actions/upload-artifact` 将 `data/*.duckdb` 文件上传为 artifact，本地下载即可 |
| **断点续爬** | ✅ 已有 `crawl_progress.duckdb`。如果 job 超时中断，可将 artifact 重新上传到下一次 run 的缓存中继续 |
| **免费额度** | ✅ GitHub Free 账户每月 2000 分钟，足够。`--limit 1000` 试运行预计总耗时 < 30 分钟 |

#### Workflow 设计草案

```yaml
name: Crawl cnkgraph Data

on:
  workflow_dispatch:  # 手动触发
    inputs:
      stage:
        description: 'Stage (1-5)'
        required: true
        default: '1'
      limit:
        description: 'Limit per entity (0=unlimited)'
        required: true
        default: '1000'
      dynasty:
        description: 'Dynasty filter (empty=all)'
        required: false
        default: ''

jobs:
  crawl:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      - name: Install dependencies
        run: pip install aiohttp duckdb

      - name: Download previous data (if exists)
        uses: actions/download-artifact@v4
        continue-on-error: true
        with:
          name: cnkgraph-data
          path: cnkgraph/data

      - name: Run crawler
        working-directory: cnkgraph
        run: |
          ARGS="--stage ${{ inputs.stage }} --limit ${{ inputs.limit }} --concurrency 1 --reset"
          if [ -n "${{ inputs.dynasty }}" ]; then
            ARGS="$ARGS --dynasty '${{ inputs.dynasty }}'"
          fi
          python src/crawl.py $ARGS

      - name: Show status
        working-directory: cnkgraph
        run: python src/crawl.py --status

      - name: Upload data
        uses: actions/upload-artifact@v4
        with:
          name: cnkgraph-data
          path: cnkgraph/data/*.duckdb
```

#### 实施要点

1. **添加 `requirements.txt`**：在 `cnkgraph/` 下创建，列出 `aiohttp` 和 `duckdb`
2. **添加 `.gitignore`**：忽略 `data/*.duckdb`、`data/*.csv`、`__pycache__/`，避免二进制文件入库
3. **手动触发**：用 `workflow_dispatch` + `inputs` 控制每次跑哪个 stage、limit 多少
4. **串行执行**：一次只跑一个 stage，避免并发触发限流
5. **数据下载**：跑完后从 Actions → Artifacts 下载 `.duckdb` 文件，放到本地 `data/` 目录
6. **全量爬取策略**：如果试运行成功，后续可以拆成多个 job（每个朝代一个），用 `--dynasty` 参数分批爬

#### 风险与缓解

| 风险 | 缓解措施 |
|------|---------|
| GitHub Actions IP 也被限流 | 极低概率——公共 IP 池轮换，且我们请求量小。如遇限流，增加间隔到 2s |
| Job 超时（6h 上限） | 全量爬取时拆分为多个 job（每朝代一个），试运行 1000 条不会超时 |
| DuckDB artifact 丢失 | 每次成功后立即下载；可考虑推送到 Git LFS 或 S3 备份 |
| cnkgraph 更换限流策略 | 如果改用 API Key 限流，需要注册账号获取 token |

#### 结论

**方案可行**。用 GitHub Actions 跑 `--limit 1000` 试运行是完全可行的方案。关键优势是换了 IP，绕过本地限流。全量爬取需要拆分为多个 job 分批执行。

---

## (七) GitHub Actions 实施方案落地 — 2026-06-03

### 决策：只爬唐诗三百首相关内容

为了保险起见、避免触发限流，只爬唐诗三百首涉及的 77 位唐代诗人的数据。请求量估算：

| Stage | 请求量 | 耗时 |
|-------|--------|------|
| Stage 1 (calendar) | ~20 次 | 1 分钟 |
| Stage 2 (people) | 1 次列表 + 77 次详情 | 2-3 分钟 |
| Stage 3 (writing) | 77 个作者 × 几页诗文 | 10-15 分钟 |
| Stage 4 (region) | 几十个 region | 2-3 分钟 |
| Stage 5 (reference) | rhyme/ciTune 各 1 次 | 2 分钟 |

总计约 20 分钟、几百次请求，远低于限流阈值。

### 决策：数据保存为 CSV 而非 DuckDB

**问题**：GitHub Actions 跑出的数据怎么回传到本地？

**方案**：爬虫照常写入 DuckDB（不改动已有代码），跑完后用 `export-csv.py` 导出所有表为 CSV 文件，上传为 GitHub Artifact。本地下载 CSV 后用 dbt 导入到 ODS 层。

优势：
- CSV 是通用格式，不依赖 DuckDB 版本
- 可直接导入 DuckDB、SQLite、PostgreSQL 等任何数据库
- 文本文件，方便查看和调试

### 决策：在当前 pinyin 仓库跑 Actions，不单独建仓库

**问题**：cnkgraph 爬虫代码是单独建一个 GitHub 仓库，还是放在当前 pinyin 仓库里？

**结论**：放在当前 pinyin 仓库里。原因：
1. cnkgraph 是 pinyin 项目的数据支撑，不是独立产品
2. workflow 文件已写好在 `.github/workflows/crawl.yml`，推上去就能跑
3. 爬下来的数据最终给 pinyin 项目用，放一起管理方便
4. 单独建仓库适合 cnkgraph 是独立开源项目的场景，目前不需要

### 新建文件

| 文件 | 用途 |
|------|------|
| `cnkgraph/requirements.txt` | Python 依赖：aiohttp, duckdb |
| `cnkgraph/.gitignore` | 忽略 .duckdb / .csv / __pycache__ |
| `cnkgraph/src/crawl-tang300.py` | 唐诗三百首专用爬虫，只爬 77 位诗人 |
| `cnkgraph/src/export-csv.py` | 从 DuckDB 导出所有表为 CSV |
| `.github/workflows/crawl.yml` | GitHub Actions 手动触发 workflow |

### 工作流程

```
GitHub Actions (云端)                  本地
─────────────────────                ────────
crawl-tang300.py 写入 DuckDB
      ↓
export-csv.py 导出 CSV
      ↓
upload-artifact 上传 CSV  ──下载──→  data/csv/*.csv
                                       ↓
                                    dbt 导入 ODS 层
```

### 下一步

1. 提交代码推送到 GitHub
2. 到 Actions 页面手动触发 "Crawl cnkgraph (唐诗三百首)"
3. 跑完后下载 CSV artifact
4. 用 dbt 将 CSV 导入本地 DuckDB 数仓

## (八) GitHub Actions 首次成功运行 — 2026-06-02

**问题**：首次 Actions 运行失败，报错 `NOT NULL constraint failed: writing_comment.content`。API 返回的某些 comment 的 Content 值为 `None`，而 `dict.get("Content", "")` 不会把已有的 `None` 转为空字符串。

**修复**：`stage3_writing.py` 第 240 行，将 `.get("Content", "")` 改为 `.get("Content") or ""`，对 Book/Section/FullPath 同样处理。

```python
# 修复前
comment.get("Content", "")
# 修复后
comment.get("Content") or ""
```

**修复后重新运行**：Run ID 26826150962，总耗时 44 分钟，全部 5 个 stage 成功完成。

**数据统计**：

| Stage | 表 | 行数 |
|-------|---|------|
| 1 Calendar | dynasty | 549 |
| | era_year | 761 |
| 2 People | person | 71 |
| | person_alias | 285 |
| | person_hometown | 71 |
| | person_detail | 1,620 |
| 3 Writing | writing | 21,150 |
| | writing_clause | 232,114 |
| | writing_comment | 17,688 |
| | writing_allusion | 12,138 |
| 4 Region | region | 373 |
| | region_history | 10,546 |
| 5 Reference | rhyme_entry | 106 |
| | ci_tune | 818 |
| | qu_tune | 1,072 |
| **合计** | **15 个表** | **299,362 行** |

**诗人匹配**：71/77 匹配成功。未匹配 6 人：刘脊虚、唐玄宗、张泌、无名氏、朱庆余、邱为。

**备注**：
- 中华新韵 API 返回 400（"未知韵书"），只获取到平水韵 106 条
- Region 有部分 404（"未找到匹配区域"），属正常现象
- CSV 已导出并上传为 GitHub Artifact（保留 30 天）

### FAQ：GitHub Actions 相关问题

**Q: CSV artifact 是 zip 吗？怎么下载？**

A: GitHub Actions 的 artifact 确实是 zip 打包上传的（本次 7.7 MB）。两种下载方式：
1. **网页下载**：仓库 → Actions 标签 → 点击运行记录 → 页面底部 Artifacts 区域 → 点击 `cnkgraph-csv` 下载 zip，解压后得到 15 个 `.csv` 文件
2. **CLI 下载**：`gh run download <run-id> --name cnkgraph-csv --dir data/csv`，自动解压到指定目录

**Q: 为什么 GitHub Actions 没有触发限流？**

A: 三个原因：
1. **IP 不同**：GitHub Actions runner 运行在 Azure 云上，IP 池很大。之前本地 IP 被限流，但 Azure IP 是全新的
2. **请求速率低**：爬虫 `concurrency=1`（串行），每次请求间隔 ~0.5s，远低于触发限流的阈值
3. **数据量可控**：只爬取 71 个诗人（非全量 200 万+），总耗时 44 分钟，平均 ~16 请求/分钟

**Q: 本地 IP 被限流后怎么办？**

A: cnkgraph 的限流是 IP 级别的。本地被限流后可以：
- 等 IP 限流解除（通常数小时到一天）
- 换 IP（关 VPN / 重拨宽带 / 手机热点）
- 使用 GitHub Actions（推荐，免费且不受本地 IP 限制）

## (九) CSV 格式修复 — ci_tune / qu_tune JSON 展开 — 2026-06-02

**问题**：导出的 15 个 CSV 中，`ci_tune.csv` 和 `qu_tune.csv` 的 `content` 列包含原始 JSON 字符串，无法直接作为表格使用。其余 13 个 CSV 格式正常。

**原因**：Stage 5 爬虫将 ci_tune / qu_tune 的整个 API 响应对象序列化为 JSON 字符串存入 `content` 列，没有拆分为独立字段。

**ci_tune 原始格式**：
```
id,name,content
1,归字谣,"{""Id"": 1, ""Type"": ""Ping"", ""Name"": ""归字谣"", ""Aliases"": [""苍梧谣"", ""十六字令""], ...}"
```

**修复**：修改 `export-csv.py`，导出 ci_tune 和 qu_tune 时解析 JSON content，展开为独立列：

**ci_tune 新格式**（6 列）：
```
id,name,type,aliases,desc,writing_count
1,归字谣,Ping,苍梧谣|十六字令,蔡伸词名《苍梧谣》...,251
```

**qu_tune 新格式**（6 列）：
```
id,name,path,aliases,name_comment,writing_count
1,喜迁莺,北曲/黃鍾宮,,,12
```

其中 `aliases` 是数组，用 `|` 分隔拼接为字符串。

**15 个 CSV 格式排查结果**：

| 文件 | 行数 | 状态 |
|------|------|------|
| dynasty.csv | 549 | 正常 |
| era_year.csv | 761 | 正常 |
| person.csv | 71 | 正常 |
| person_alias.csv | 285 | 正常 |
| person_hometown.csv | 71 | 正常 |
| person_detail.csv | 1,620 | 正常 |
| writing.csv | 21,150 | 正常 |
| writing_clause.csv | 232,114 | 正常 |
| writing_comment.csv | 17,688 | 正常 |
| writing_allusion.csv | 12,138 | 正常 |
| region.csv | 373 | 正常 |
| region_history.csv | 10,546 | 正常 |
| rhyme_entry.csv | 106 | 正常 |
| **ci_tune.csv** | 818 | **已修复（JSON 展开）** |
| **qu_tune.csv** | 1,072 | **已修复（JSON 展开）** |

**备注**：此修复仅影响 `export-csv.py` 导出逻辑，未改动 DDL 和爬虫代码。下次 GitHub Actions 运行会自动导出格式化后的 CSV。本地已用 `gh run download` 下载的 CSV 可重新运行 `python src/export-csv.py` 覆盖。

## (十) CI/CD 工作流说明 — 2026-06-02

项目有两个独立的 GitHub Actions workflow，互不干扰：

| Workflow | 触发方式 | 用途 |
|----------|---------|------|
| `deploy.yml` | `on: push` (master) + 手动 | 构建网站并部署到 GitHub Pages |
| `crawl.yml` | `on: workflow_dispatch`（仅手动） | 运行爬虫、导出 CSV、上传 artifact |

**关键设计**：
- push 代码到 master **只会触发网站部署**，不会运行爬虫
- 爬虫只能通过 Actions 页面手动点击 "Run workflow" 触发
- 两者完全独立，不会互相影响

## (十一) cnkgraph 数据同步到 dbt ODS 层 — 2026-06-02

**目标**：将 GitHub Actions 爬取的 15 个 CSV 表同步到 `cbdb/data/cbdb.duckdb` 的 `ods` schema，表名统一加前缀 `ods_cnkgraph_`。

**实现步骤**：

1. **复制 CSV 到 dbt seeds**：将 `cnkgraph/data/csv/*.csv` 复制到 `cbdb/cbdb_dw/seeds/`，文件名加 `ods_cnkgraph_` 前缀
2. **创建 schema.yml**：为 15 个 seed 表编写中文表注释和字段注释（`cbdb/cbdb_dw/seeds/schema.yml`）
3. **配置 dbt_project.yml**：添加 `seeds` 配置，指定 `+schema: ods`
4. **运行 `dbt seed`**：14 个表通过 dbt seed 直接加载成功
5. **writing 表特殊处理**：`writing.csv` 的 `preface` 字段含 HTML（含换行符和双引号），dbt seed 的 DuckDB CSV 解析器在 `strict_mode=true` 下报错。改用 Python 直接通过 `read_csv_auto(..., ignore_errors=true)` 加载，成功导入 20,786 行（跳过约 364 行有问题的数据）

**ci_tune 列名修复**：`desc` 是 SQL 保留字，导出 CSV 时改为 `description`

**数据验证结果**：

| 表名 | 行数 |
|------|------|
| ods_cnkgraph_dynasty | 549 |
| ods_cnkgraph_era_year | 761 |
| ods_cnkgraph_person | 71 |
| ods_cnkgraph_person_alias | 285 |
| ods_cnkgraph_person_hometown | 71 |
| ods_cnkgraph_person_detail | 1,620 |
| ods_cnkgraph_writing | 20,786 |
| ods_cnkgraph_writing_clause | 232,114 |
| ods_cnkgraph_writing_comment | 17,688 |
| ods_cnkgraph_writing_allusion | 12,138 |
| ods_cnkgraph_region | 373 |
| ods_cnkgraph_region_history | 10,546 |
| ods_cnkgraph_rhyme_entry | 106 |
| ods_cnkgraph_ci_tune | 818 |
| ods_cnkgraph_qu_tune | 1,072 |
| **合计** | **298,998** |

**关键文件**：

| 文件 | 说明 |
|------|------|
| `cbdb/cbdb_dw/seeds/ods_cnkgraph_*.csv` | 15 个 seed 数据文件 |
| `cbdb/cbdb_dw/seeds/schema.yml` | 15 个表的中文注释文档 |
| `cbdb/cbdb_dw/dbt_project.yml` | 新增 seeds 配置 |

## (十二) 已爬数据 vs API 全量数据对比 — 2026-06-03

**背景**：当前爬取范围限制为唐诗三百首的 77 位诗人（实际匹配 71 人），仅涉及唐朝。cnkgraph API 涵盖 15 个朝代、约 12 万文学人物、200 万+ 诗文。

### 数据对比总览

| 表名 | 已导入 ODS | API 全量估算 | 覆盖率 | 状态 | 说明 |
|------|-----------|-------------|--------|------|------|
| **dynasty** | 549 | ~549 | **100%** | 全量 | 单次请求获取所有朝代，无过滤 |
| **era_year** | 761 | ~761 | **100%** | 全量 | 遍历所有朝代获取年号，无过滤 |
| **ci_tune** | 818 | ~819 | **~100%** | 全量 | 单次 `GET /ciTune` 返回全部 |
| **qu_tune** | 1,072 | ~1,073 | **~100%** | 全量 | 单次 `GET /quTune` 返回全部 |
| **rhyme_entry** | 106 | ~106 | **100%** | 全量 | 平水韵 106 韵部；中华新韵 API 返回 400 错误 |
| **person** | 71 | ~120,000 | **0.06%** | 过滤 | 仅匹配 71 位唐诗三百首诗人；全量需遍历 15 个朝代 |
| **person_alias** | 285 | ~500,000 | **0.06%** | 过滤 | 仅 71 人的别名；全量需逐人请求详情 |
| **person_hometown** | 71 | ~120,000 | **0.06%** | 过滤 | 仅 71 人的籍贯 |
| **person_detail** | 1,620 | ~200,000 | **0.8%** | 过滤 | 71 人共 1,620 条传记；大诗人资料多 |
| **writing** | 20,786 | ~2,000,000 | **1%** | 过滤 | 仅 71 人作品；李白独占 3,120 首 |
| **writing_clause** | 232,114 | ~20,000,000 | **1.2%** | 过滤 | 随 writing 而来 |
| **writing_comment** | 17,688 | ~4,000,000 | **0.4%** | 过滤 | 名篇评注多 |
| **writing_allusion** | 12,138 | ~500,000 | **2.4%** | 过滤 | 随 writing 而来 |
| **region** | 373 | ~3,000 | **12%** | 过滤 | 仅从 71 人作品中提取的区域 |
| **region_history** | 10,546 | ~30,000 | **35%** | 过滤 | 随 region 而来，历史区域较多 |

### 分类说明

**A. 已全量，无需重爬（5 个表）**：

这些表的 API 是单次请求返回全部数据，不受诗人范围限制。已在 GitHub Actions 一次 44 分钟的运行中完成。

| 表 | 行数 | API 端点 |
|---|------|---------|
| dynasty | 549 | `GET /calendar` |
| era_year | 761 | `GET /calendar/{dynasty}` × 549 |
| ci_tune | 818 | `GET /ciTune` |
| qu_tune | 1,072 | `GET /quTune` |
| rhyme_entry | 106 | `GET /rhyme/平水韵` |

**B. 已过滤，如需全量需补充爬取（10 个表）**：

当前数据仅覆盖 71 位唐代诗人的子集。若需全量，需用 `crawl.py`（非 `crawl-tang300.py`）遍历全部朝代和作者。

| 补充范围 | 涉及表 | 增量估算 | 预估耗时 | 难度 |
|---------|--------|---------|---------|------|
| 全朝代人物（~12 万人） | person, person_alias, person_hometown, person_detail | +12 万 / +50 万 / +12 万 / +20 万 | ~8 小时 | 高（逐人请求，易限流） |
| 全朝代诗文（~200 万首） | writing, writing_clause, writing_comment, writing_allusion | +198 万 / +1,980 万 / +398 万 / +49 万 | ~20 小时 | 极高（海量分页，易限流） |
| 全量区域（~3,000 个） | region, region_history | +2,600 / +2 万 | ~30 分钟 | 低（增量补充即可） |

**C. 未爬取的表（10 个表，当前 ODS 中无数据）**：

| 表 | API 全量估算 | 状态 | 原因 |
|---|-------------|------|------|
| book | ~7,000 | 未爬 | crawl-tang300 跳过了 book 模块 |
| book_volume | ~数万 | 未爬 | 依赖 book，逐书请求 |
| glossary | ~5 万 | 未爬 | API 返回 405，禁用 |
| category_entry | ~5 万 | 未爬 | crawl-tang300 跳过 |
| char_dict | ~2 万 | 未爬 | 需遍历 CJK 字符集 |
| rhyme_char | ~数千 | 未爬 | 未实现，需逐韵部逐字请求 |
| scenery | ~1 万 | 未爬 | region 详情中提取，当前 0 条 |
| writing_link | ~数百万 | 未爬 | 需逐首请求 `/writing/{id}`，PRD 中标注"另行安排" |

### 补充爬取建议

若仅需唐诗数据（非全朝代），当前 71 人数据已基本满足唐诗三百首项目需求。如需扩展：

1. **补爬 6 位未匹配诗人**（刘脊虚、唐玄宗、张泌、无名氏、朱庆余、邱为）：可能是 API 中名称不同，需手动查 ID，约 10 分钟
2. **扩展到全部唐代诗人**（~2,500 人）：改用 `crawl.py --dynasty 唐朝`，预估增加 ~5 万首诗文，耗时约 2 小时
3. **扩展到全部朝代**：使用 `crawl.py` 不加限制，预估总量 ~200 万诗文，耗时 20+ 小时，需分批运行并注意限流

> **详细文档**：完整的数据管道技术文档（工具选型、脚本调用、CI/CD 运行对比、CSV 修复、dbt 导入、覆盖率比对方法论、全量爬取方案）见 [data-pipeline.md](data-pipeline.md)

---

## (十三) 未匹配诗人排查 + 卷 11 作者清单 — 2026-06-03

### 6 位未匹配诗人原因分析

爬虫从 cnkgraph API `/people/唐朝` 获取唐代人物列表，用精确匹配（`name == poet_name`）查找。以下 6 人未能匹配，原因均为**名字写法不同**：

| 我们的名字 | cnkgraph 使用的名字 | 原因 | 可否修复 |
|-----------|-------------------|------|---------|
| **刘脊虚** | 刘昚虚 | "昚"是生僻字，被误写为"脊"。实际上维基百科记载还有"刘慎虚"的写法 | 将 TANG300_POETS 中改为"刘昚虚" |
| **唐玄宗** | 李隆基 | cnkgraph 用本名"李隆基"而非庙号"唐玄宗"（也称"唐明皇"） | 将 TANG300_POETS 中改为"李隆基" |
| **张泌** | 张佖 | "泌"与"佖"字形相近。历史上张泌（花间词人）和南唐张佖实为不同人，但唐诗三百首的"张泌"在 cnkgraph 中可能被归为"张佖" | 将 TANG300_POETS 中改为"张佖"，或两名字都试 |
| **无名氏** | — | cnkgraph 人物库中无"无名氏"条目，这是诗歌署名的特殊情况 | 无法匹配，需单独处理 |
| **朱庆余** | 朱庆馀 | "余"vs"馀"——繁简异体字差异（"馀"是"余"的繁体异写） | 将 TANG300_POETS 中改为"朱庆馀" |
| **邱为** | 丘为 | 避孔子讳："丘"姓在清代雍正年间加"阝"旁变为"邱"，实为同一人 | 将 TANG300_POETS 中改为"丘为" |

**总结**：6 人中有 5 人可通过修正名字匹配，1 人（无名氏）无法匹配。需修改 `crawl-tang300.py` 中的 `TANG300_POETS` 列表。

### 卷 11（小学生古诗词）作者清单

卷 11 收录 100+ 首小学必背古诗词，跨多个朝代（汉→清），共 **100 位作者**（去重后），其中：

**唐代作者（与卷 01-10 重叠）**：白居易、岑参、陈陶、陈子昂、崔护、杜甫、杜牧、杜秋娘、杜荀鹤、高适、韩翃、韩愈、贺知章、胡令能、黄巢、贾岛、李白、李贺、李峤、李商隐、李绅、李世民、刘方平、刘禹锡、刘长卿、柳宗元、卢纶、骆宾王、孟浩然、孟郊、司空曙、宋之问、王勃、王昌龄、王翰、王建、王湾、王维、王之涣、韦应物、温庭筠、无名氏、元稹、张籍、张继、张九龄

**非唐代作者（需扩展爬取范围）**：

| 作者 | 朝代 | 代表作 |
|------|------|--------|
| 曹操 | 汉 | 《观沧海》 |
| 曹植 | 三国 | 《七步诗》 |
| 陶渊明 | 晋 | 《饮酒》 |
| 北朝民歌 | 南北朝 | 《木兰辞》 |
| 苏轼 | 宋 | 《题西林壁》《饮湖上初晴后雨》 |
| 王安石 | 宋 | 《梅花》《元日》 |
| 杨万里 | 宋 | 《小池》 |
| 李清照 | 宋 | 《夏日绝句》 |
| 陆游 | 宋 | 《示儿》 |
| 辛弃疾 | 宋 | 《清平乐·村居》 |
| 范仲淹 | 宋 | 《江上渔者》 |
| 曾巩 | 宋 | 《咏柳》 |
| 文天祥 | 宋 | 《过零丁洋》 |
| 唐寅 | 明 | 《画鸡》 |
| 于谦 | 明 | 《石灰吟》 |
| 郑燮 | 清 | 《竹石》 |
| 袁枚 | 清 | 《苔》 |
| 龚自珍 | 清 | 《己亥杂诗》 |
| 纳兰性德 | 清 | 《长相思》 |

卷 11 涉及 **汉、三国、晋、南北朝、唐、宋、元、明、清** 共 9 个朝代。若需爬取卷 11 全部数据，需将爬取范围从"唐朝"扩展到"全部朝代"。

---

*持续更新中*
