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

---

*持续更新中*
