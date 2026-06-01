# DevLog — CBDB 数据仓库工具集

## 2026-05-31

### 14:00 诗人传记卡片功能实现

**目标**：在唐诗三百首注音网页版中，点击作者名字弹出侧滑面板，展示 CBDB 中的传记信息。

**详细实现文档**：→ [poet-bio-card.md](poet-bio-card.md)

**概要**：
- 数据提取：`cbdb/scripts/export-poet-bio.js` 查询 CBDB SQLite 11 张表，输出 `src/poet-bio.json`（72/77 位有数据）
- 简繁映射：内置 S2T 静态表解决简体（王维）→ 繁体（王維）的差异
- 构建集成：`build.js` 读取 poet-bio.json 合并到 `data.poetBios`
- 前端 UI：侧滑面板展示生卒年、字号、籍贯、入仕、官职、身份

**文件变更**：
- 新建 `cbdb/scripts/export-poet-bio.js`
- 新建 `src/poet-bio.json`
- 新建 `cbdb/docs/poet-bio-card.md`
- 修改 `build.js` — 合并诗人传记数据 + 兼容卷11无编号诗题和"朝代-作者"格式
- 修改 `src/index.html` — 传记面板 CSS/HTML/JS + 朝代字段动态显示

### 15:00 build.js 兼容卷11格式

**问题**：新增卷11（小学生古诗词）的数据格式不同于卷1-10：
- 诗题无三位数字编号（`### 咏鹅` 而非 `### 001 咏鹅`）
- 作者含朝代前缀（`> 唐-骆宾王` 而非 `> 骆宾王`）
- 存在非唐朝诗人（宋-杨万里、明-唐寅、清-高鼎等）
- 特殊作者名无横线（`> 汉乐府`、`> 北朝民歌`）

**修复**：
- 诗题匹配：先尝试 `### \d{3} 标题`，失败则取 `###` 后全部文本，自增编号
- 作者解析：`> 朝代-作者` 用正则 `/(.+?)\s*[-—]\s*(.+)$/` 拆分朝代和姓名
- dynasty 字段：有横线取左半部分，无横线默认空（前端 `dynasty || '唐'` 兜底）
- 特殊映射：`{ '汉乐府': '汉', '北朝民歌': '南北朝' }`
- 前端显示：`〔${poem.dynasty || '唐'}〕${poem.author}` 替代硬编码 `〔唐〕`

### 16:00 诗歌系年数据调研

**目标**：查找唐诗"创作年份"数据源，用于未来给诗歌添加系年/系地信息。

**调研文档**：→ [../../docs/poem-dating-research.md](../../docs/poem-dating-research.md)

**结论**：
- CBDB 的粒度是"人物"和"文集"，不是"单首诗"，无法提供诗歌系年
- GitHub 上无结构化的诗歌系年数据库（chinese-poetry 等 30 万首诗均无系年字段）
- 王兆鹏团队（唐宋文学编年系地信息平台）有 62,559 条系年记录，但未开源
- 对于唐诗三百首（511 首），人工标注参考《唐诗系年》最可行，约 2-3 天

---

### 11:20 DuckDB 文件锁冲突

**报错**：`IO Error: Cannot open file cbdb.duckdb` — DBeaver 占用文件，dbt 无法写入。

**原因**：DuckDB 是单进程文件数据库，同一时间只允许一个进程写入，和 SQLite 一样。DBeaver 持有文件锁后 dbt 无法打开。

**解决**：DBeaver 中断开连接（不是关软件），再跑 `dbt run`。

**开发流程**：先 `dbt run` 建模，跑完再用 DBeaver 查看验证。

### 11:30 DuckDB 分层 schema

**问题**：ODS 表全部建在 `main` schema 下，后续 DIM/DWD 层也混在一起，无法按层区分。

**解决方案**：

1. `dbt_project.yml` 每层配 `+schema: ods/dim/dwd/dws/ads`
2. 新建 `macros/generate_schema_name.sql` 覆盖 dbt 默认的 schema 拼接逻辑（默认会拼成 `main_ods`，改为直接用 `ods`）

改后效果：

```
DuckDB
├── ods     ← ods_cbdb_biog_main, ods_cbdb_kin_data, ...
├── dim     ← dim_person, dim_dynasty, ...
├── dwd     ← fact_kinship, fact_association, ...
├── dws     ← dws_person_by_dynasty, ...
└── ads     ← ads_poet_timeline, ...
```

需要删旧 DuckDB 文件重跑（schema 结构变化）。

**报错**：`IO Error: Cannot open file cbdb.duckdb` — DBeaver 占用文件，dbt 无法写入。

**原因**：DuckDB 是单进程文件数据库，同一时间只允许一个进程写入，和 SQLite 一样。DBeaver 持有文件锁后 dbt 无法打开。

**解决**：DBeaver 中断开连接（不是关软件），再跑 `dbt run`。

**开发流程**：先 `dbt run` 建模，跑完再用 DBeaver 查看验证。

**报错 1：`Catalog "cbdb_src" does not exist!`**

**原因**：profiles.yml 中 attach 路径用了相对路径，dbt-duckdb 解析时找不到文件。**解决方案**：改用绝对路径。

**报错 2：表和字段注释为空**

**原因**：dbt 默认不执行 `COMMENT ON`。**解决方案**：在 `dbt_project.yml` 加 `+persist_docs: {relation: true, columns: true}`。

**修改 3：view 改 table**

ODS 层用 view 每次查询穿透到 SQLite，性能不可控。改为 `materialized: table`，数据物化到 DuckDB。

**修改 4：ETL_LOAD_DATETIME 格式**

`NOW()` 带微秒和时区（`2026-05-31 00:38:49.040 +0800`），改为 `CAST(DATE_TRUNC('second', NOW()) AS TIMESTAMP)` 输出干净格式：`2026-05-31 00:43:39`。

**关于删 DuckDB 文件重跑**：

这次删是因为从 view 改 table、加 ETL 字段，结构变化大，清理旧文件是稳妥做法。**之后日常开发不需要删文件**：
- `dbt run`：自动 DROP + CREATE 已变的 table，重新写入 COMMENT
- `dbt run --full-refresh`：强制重建所有 model
- `dbt clean`：清理 `target/` 构建缓存（不删 .duckdb 文件）

---

### 10:30 ODS 每张表追加 ETL 审计字段

在每个 ODS model 末尾追加 2 个 ETL 审计字段：

```sql
NOW()             AS ETL_LOAD_DATETIME,  -- ETL加载时间
CURRENT_DATE      AS ETL_LOAD_DATE       -- ETL加载数据日期
```

**修正**：
- 字段名改为 `ETL_LOAD_DATETIME` / `ETL_LOAD_DATE`（更清晰）
- `NOW()` 和 `CURRENT_DATE` 在 DuckDB 中已验证可用（`duckdb -c "SELECT NOW(), CURRENT_DATE"` 通过）
- **sources.yml 不包含这两个字段**（它们不存在于 SQLite 源表中，是 ODS 层新增的）
- ods/schema.yml 和 SQL 文件包含这两个字段

### 10:50 编写 ODS 同步指南

将"脚本驱动 ODS 同步"的方法论整理为独立文档 `docs/ods-sync-guide.md`，包含 6 个 Mermaid 图：
- 整体流程图、比对流程图、缺失分类图、注释优先级决策图、生成产物图、注释覆盖率推进图、DuckDB 注释机制时序图

### 12:00 编写 CBDB 数据挖掘与诗词项目集成文档

新建 `docs/cbdb-data-mining.md`，涵盖：
- CBDB 87 张表按 10 大领域分类（人物、地理、官职、关系、文献、朝代、事件、机构、身份、编码）
- 6 个数据挖掘方向（迁徙轨迹、关系网络、官职流动、文献计量、时空分析、群体画像）
- 4 个诗词项目集成方案（年谱地图、关系网络、传记卡片、朝代时间线）
- 经纬度转地图技术栈（Leaflet.js 推荐，WGS-84 坐标系无需转换）
- 含 3 个 Mermaid 图（数据全景、年谱地图数据流、整体数据流架构）

将"脚本驱动 ODS 同步"的方法论整理为独立文档 `docs/ods-sync-guide.md`，包含 6 个 Mermaid 图：
- 整体流程图、比对流程图、缺失分类图、注释优先级决策图、生成产物图、注释覆盖率推进图、DuckDB 注释机制时序图

**Q: models/sources.yml 和 models/ods/schema.yml 看起来一样，为什么需要 2 个？**

不一样，职责不同：

| | `models/sources.yml` | `models/ods/schema.yml` |
|---|---|---|
| dbt 概念 | **source**（外部数据源） | **model**（dbt 管理的对象） |
| 定义什么 | SQLite 里的原始表（只读） | dbt 创建的 ODS 视图 |
| 关键字 | `sources:` + `- name: cbdb_src` | `models:` + `- name: ods_cbdb_*` |
| 谁引用 | SQL 里用 `{{ source('cbdb_src', 'BIOG_MAIN') }}` | SQL 里用 `{{ ref('ods_cbdb_biog_main') }}` |
| dbt test | 对源表做数据质量检查 | 对 ODS 视图做数据质量检查 |

简单说：sources.yml 描述"数据从哪来"，schema.yml 描述"dbt 造了什么"。当前两者描述内容相似（因为 ODS 是 1:1 贴源），但后续 DIM/DWD 层的 schema.yml 会完全不同，那时区别就明显了。

**Q: 现在可以跑 `dbt run --select ods.*` 了吗？**

前提条件：
1. `~/.dbt/profiles.yml` 已配置 ✓（路径已核对）
2. `data/cbdb_20260523.sqlite3` 存在 ✓
3. dbt 项目已初始化 ✓（`cbdb_dw/dbt_project.yml`）
4. 77 个 ODS model + sources.yml + schema.yml 已生成 ✓

可以跑了。进入 `cbdb/cbdb_dw/` 目录执行 `dbt run --select ods.*` 即可。

---

## 2026-05-30

### 18:00 ODS 完善：显式字段 + 列注释 + DuckDB 视图注释机制

**Q1: SELECT * 改成显式字段列出有必要吗？**

有必要。改为 `SELECT 字段名 -- 注释` 的好处：
- SQL 文件本身就是可读的字段文档
- 源表增减字段时 ODS 不会静默变化
- dbt lineage 能追踪到列级别

**Q2: DuckDB 的 view 会保留字段注释吗？**

**会。** dbt 处理 schema.yml 的流程是：
1. 先执行 SQL 创建 view/table
2. 然后逐字段执行 `COMMENT ON COLUMN model.字段 IS '中文注释'`
3. DuckDB 的视图和表都支持 COMMENT ON，注释存储在元数据系统表 `duckdb_columns()` 中

验证方式：`SELECT column_name, comment FROM duckdb_columns() WHERE table_name = 'ods_cbdb_biog_main'`

**Q3: profiles.yml 路径核对**

用户已修正配置，核对通过：
- DuckDB: `path: ../data/cbdb.duckdb` → 解析为 `cbdb/data/cbdb.duckdb`
- SQLite: `path: ../data/cbdb_20260523.sqlite3` → 解析为 `cbdb/data/cbdb_20260523.sqlite3`
- 均从 `cbdb_dw/` 出发，路径正确

**完善结果**：

| 维度 | 数量 |
|------|------|
| sources.yml | 77 张源表，含完整列注释 |
| ods_cbdb_*.sql | 77 个文件，显式列出字段 + 行内注释 |
| ods/schema.yml | 77 个 model，含列级中文描述 |
| 注释覆盖率 | 722/722（100%） |

缺失注释的补充策略：
- 爬虫 JSON 有中文 → 直接用（638 个）
- 8 张 DDL 独有表 → 手动写表级+字段级描述
- 审计字段（c_created_by 等）→ 批量规则匹配
- 时间辅助字段（_nh_code 等）→ 批量规则匹配
- 最后 2 个缺失字段 → 版本重命名导致，人工补齐：
  - `ASSOC_CODE_TYPE_REL.c_assoc_type_code`：网站新版改名为 `c_assoc_type_id`，含义相同 —— "关联类型标识符，定义社交关系分类层级"
  - `ASSOC_TYPES.c_assoc_type_code`：同上 —— "关联类型唯一标识符，区分不同社会关系分类"

---

### 16:40 文档放置决策

**决策**：项目文档放 `cbdb/docs/`，不放 `cbdb_dw/`。

理由：
- dbt 自带 `dbt docs generate` 文档体系，根据 schema.yml 自动生成站点，不需要手写 markdown
- PRD、devlog、数仓建模方案、技术教程是项目级文档，属于 `cbdb/` 仓库层面
- `cbdb_dw/` 只放代码（models、macros、yml），可加一个简短 README.md

---

### 17:00 编写 ODS 层 models & YAML

**方案**：77 张 SQLite 实表全部同步到 DuckDB ODS 层。写脚本 `scripts/generate-ods-models.js` 从 DDL + 爬虫 JSON 自动生成：
- `models/sources.yml` — 定义 SQLite 数据源、全部 77 张表的字段和中文注释
- `models/ods/ods_cbdb_{table}.sql` — 每张表一个 ODS model（SELECT * FROM source）
- `models/ods/schema.yml` — ODS 层模型的中文描述

**生成结果**：

| 文件 | 数量 |
|------|------|
| sources.yml | 1 个，定义 77 张源表 |
| ods_cbdb_*.sql | 77 个 ODS model |
| schema.yml | 1 个，77 个 model 描述 |
| 有中文表描述 | 69/77 张（89.6%） |
| 有中文字段描述 | 638/722 个（88.4%） |

**dbt_project.yml 更新**：
- 删除 example 配置
- ODS 层 `+materialized: view`（贴源层用视图，不复制数据）
- DIM/DWD/DWS/ADS 层 `+materialized: table`

**注意事项**：
- profiles.yml 中 `attach.path` 为 `data/cbdb_20260523.sqlite3`，但 dbt 从 `cbdb_dw/` 运行，需改为 `../data/cbdb_20260523.sqlite3`
- DuckDB 文件 `dev.duckdb` 当前在 `cbdb_dw/` 目录，讨论过放 `data/` 但暂未调整

---

### 17:30 缺失注释分析与补充方案

**Q1: 缺失注释的原因是什么？**

**版本不一致是主因。** SQLite 文件是 `cbdb_20260523` 版本（下载的固定快照），而网站 cbdb.sunan.me 运行的可能是更新版本。证据：
- 字段名差异（c_assoc_type_code vs c_assoc_type_id）说明网站做过字段重命名
- 网站有 18 张 SQLite 中不存在的表（视图和应用元数据表）
- 8 张 SQLite 表在网站上完全找不到（如 APPOINTMENT_CODES 三张一组）

**Q2: SQLite 自身能提取注释吗？**

**不能。** SQLite 没有 `COMMENT ON` 语法，不支持列级注释。DDL 中少量字段有英文 `/* ... */` 行内注释（如 BIOG_MAIN 的 c_name、c_name_chn），但绝大多数字段无注释。中文描述只存在于网站前端的数据字典中，无法从 SQLite 文件本身获取。

**Q3: 84 个缺失字段能补吗？怎么补？**

用脚本 `scripts/analyze-missing-desc.js` 分析了 84 个缺失字段的分布：

| 类别 | 数量 | 补充方式 |
|------|------|---------|
| 审计字段（c_created_by/date 等） | 20 | 批量自动补："记录创建人/修改人/时间" |
| 时间辅助字段（_nh_code, _range 等） | 14 | 批量自动补："年号编码/时间范围标识" |
| 来源/备注字段（c_notes, c_source 等） | 7 | 批量自动补："备注/资料来源" |
| 其他（集中在 8 张 DDL 独有表） | 43 | 字段名可读性高（如 c_appt_code → 任命方式编码），人工手动补 |

**实际操作**：84 个字段中约 41 个（审计+时间+来源）可脚本批量补，剩余 43 个集中在 8 张表，字段名按 CBDB 命名惯例可读（c_admin_cat_code → 行政区类别编码），人工逐个补充即可。

---

### 16:30 DuckDB 文件位置 & 工具输出说明

**Q1: DuckDB 是像 SQLite 那样的单文件吗？放哪？**

DuckDB 和 SQLite 一样是单文件数据库（如 `cbdb.duckdb`），路径在 dbt 的 `profiles.yml` 中配置。放 `data/` 而不是 `cbdb_dw/`：
- `data/` 已在 `.gitignore` 中排除大文件，SQLite 源文件也在那里
- `cbdb_dw/` 是 dbt 项目代码（models、macros、yml），不应放数据文件
- DuckDB 文件由 `dbt run` 生成，属于衍生数据，和 SQLite 源文件同级管理更清晰

```
data/
├── cbdb_20260523.sqlite3   ← 源数据（OLTP）
└── cbdb.duckdb             ← 分析库（OLAP，dbt run 生成）
```

**Q2: compare-schema.js 脚本输出了什么文件？**

脚本的输出有两个通道：
- **stdout（终端）**：打印人类可读的对比报告（表数量、差异列表）
- **文件**：`output/schema-compare-report.json`（结构化 JSON，供程序读取）

**Q3: 怎么知道结果并记录到 devlog 的？**

脚本在终端运行后输出了完整对比报告，我根据终端输出整理成结构化的 devlog 条目。`output/schema-compare-report.json` 也保存了原始数据供后续复用。

---

### 17:00 DDL vs 爬虫数据字典校验 & ODS 同步可行性探讨

**背景**：dbt 项目 `cbdb_dw` 已初始化，需要将 SQLite 全部表同步到 DuckDB ODS 层（命名 `ods_cbdb_{table}`）。同步前需确认两个数据源的字段是否一致，以便复用爬虫的中文注释。

**数据源**：
- DDL：`docs/cbdb_tbl.md`（从 SQLite `.schema` 导出，77 张表）
- 爬虫：`output/cbdb_dict.json`（从 cbdb.sunan.me 爬取，87 张表）

**校验工具**：编写 `scripts/compare-schema.js`，自动解析 DDL 和 JSON，逐表逐字段对比。

**校验结果**：

| 维度 | 数量 |
|------|------|
| DDL 表（SQLite 实表） | 77 |
| 爬虫表（网站展示） | 87 |
| 两边共有 | 69 |
| 仅在 DDL（SQLite 有，网站没展示） | 8 |
| 仅在爬虫（网站有，SQLite 无此实表） | 18 |
| 字段完全一致 | 50 |
| 字段有差异 | 19 |

**仅 DDL 的 8 张表**：

| 表 | 说明 |
|----|------|
| ADMIN_CAT_CODES / _CODE_TYPE_REL / _TYPES | 行政区类别代码，3张一组 |
| APPOINTMENT_CODES / _CODE_TYPE_REL / _TYPES | 任命方式代码，3张一组 |
| KIN_MOURNING | 亲属丧服关系（网站大小写不同：KIN_Mourning） |
| MERGED_PERSON_DATA | 人物合并记录 |

**仅爬虫的 18 张表**（网站独有，SQLite 中无实表）：

| 类型 | 表 |
|------|-----|
| 视图/派生表 | ADDRESSES（地址层级视图）、ADDR_PLACE_DATA、ADDR_XY |
| 应用元数据 | CopyMissingTables、CopyTables、CopyTablesDefault、ForeignKeys、FormLabels、TablesFields、TablesFieldsChanges、CBDB_NAME_LIST、TMP_INDEX_YEAR |
| 转换表 | OFFICE_CODES_CONVERSION、SOCIAL_INSTITUTION_CODES_CONVERSION |
| 备份表 | OFFICE_TYPE_TREE_backup |

**19 张有差异表的差异模式**：

| 差异模式 | 涉及表 | 说明 |
|---------|--------|------|
| DDL 多出审计字段 | ADDR_BELONGS_DATA, BIOG_SOURCE_DATA, POSTED_TO_ADDR_DATA, POSTING_DATA | SQLite 有 c_created_by/date, c_modified_by/date，网站不展示 |
| 字段名变更 | ASSOC_CODE_TYPE_REL, ASSOC_TYPES | DDL: c_assoc_type_code → 爬虫: c_assoc_type_id |
| 字段名变更 | ENTRY_DATA | DDL: c_entry_nh_id → 爬虫: c_nianhao_id, c_parental_status_code → c_parental_status |
| 字段拆分 | ASSOC_DATA | DDL 有 c_assoc_first_year/last_year（8个），爬虫合并为 c_assoc_year（4个） |
| 爬虫多展示列 | OFFICE_CODES, TEXT_CODES, ETHNICITY_TRIBE_CODES | 网站做了 JOIN 补充展示列 |
| 爬虫多字段 | BIOG_MAIN | 多 c_self_bio（自传标记） |

**可行性结论**：

> **dbt ODS 同步完全可行。** 以 SQLite DDL 为准（77 张实表），爬虫 JSON 提供中文注释。

方案：
1. `sources.yml` 定义 77 张 SQLite 表（以 DDL 为准）
2. 每张表一个 `ods_cbdb_{table}.sql`，内容为 `SELECT * FROM source(...)`
3. `schema.yml` 用爬虫的中文 desc 做注释，DDL 多出的字段（审计列等）手动补充
4. 字段名有差异的 19 张表，注释以 DDL 字段名为准（因为实际读的是 SQLite）
5. 网站独有的 18 张表不进入 ODS（非 SQLite 实表）

风险点：
- 19 张表的字段不完全对齐，注释需人工校准
- DuckDB sqlite 扩展的兼容性需实际验证

---

### 18:00 项目脚手架搭建

### 18:00 项目脚手架搭建

**重构目录结构**，将根目录堆积的文件按职责归类：

```
cbdb/
├── data/        ← cbdb_20260523.sqlite3, .json, latest.zip
├── docs/        ← cbdb_tbl.md, cbdb-data-warehouse.md, pachong.md
├── scripts/     ← Node.js 脚本
├── sql/         ← test.sql
└── output/      ← 脚本输出（gitignore）
```

创建 `package.json`（ESM，零依赖）和 `.gitignore`（排除大文件和输出）。

> 根目录 `cbdb_20260523.sqlite3` 因被进程占用无法删除，data/ 中已有完整副本。

---

### 18:20 网站结构探索

分析 https://cbdb.sunan.me 的技术实现：

- Vue.js 3 + Element Plus + ECharts 的 SPA
- 数据通过静态 JSON 文件加载：`/data/{表名}_data_dict.json`
- 目录页 `/data/` 列出所有 87 个 JSON 文件
- SSL 证书已过期，需跳过验证
- JSON 中中文描述存在编码乱码（双重 UTF-8 编码），表名和字段名正常

发现过程：
1. `curl` 直连被 SSL 拒绝 → 加 `-k` 跳过验证
2. HTML 只有一个 `<div id="app">` → SPA，需要找 API
3. 分析 `index-*.js` 打包文件 → 发现 `fetch("/data/")` 和 `fetch("/data/${name}")` 模式
4. 访问 `/data/` → 得到文件目录 HTML
5. 访问单个 JSON → 发现中文乱码，latin1→utf-8 修复策略有效

---

### 19:00 crawl-dict.js v1 — 数据字典爬取

**首次运行**：
- 87 张表、795 个字段，0 失败
- 编码修复成功（`Buffer.from(str, 'latin1').toString('utf-8')`）
- 输出：`cbdb_dict.json`（251K）、`cbdb_dict.csv`（70K）、`cbdb_dict.md`（88K）

**发现遗漏**：JSON 中包含 `foreign_keys` 字段（外键关系），但 CSV 和 Markdown 没有输出。

---

### 19:30 crawl-dict.js v2 — 补充外键关系

**改动**：
- CSV 拆分为两个文件：`cbdb_dict_columns.csv`（字段）和 `cbdb_dict_foreign_keys.csv`（外键）
- Markdown 每张表新增"外键"小节，展示 from→to 关系
- 统计报告增加外键计数

**运行结果**：
- 87 张表、795 个字段、**185 个外键**（65 张表有外键）
- 输出文件：`cbdb_dict.json`、`cbdb_dict_columns.csv`、`cbdb_dict_foreign_keys.csv`、`cbdb_dict.md`
- 外键描述中文正常，无乱码

**输出示例**（Markdown 中的外键表）：

```
**外键**（6 个）

| 字段 | 目标表 | 目标字段 | 更新 | 删除 | 说明 |
|------|--------|----------|------|------|------|
| c_index_year_type_code | INDEXYEAR_TYPE_CODES | c_index_year_type_code | CASCADE | CASCADE | 索引年份类型代码引用 |
| c_dy | DYNASTIES | c_dy | CASCADE | CASCADE | 所属朝代代码引用 |
| c_index_addr_id | ADDRESSES | c_addr_id | CASCADE | CASCADE | 主地址ID引用地址表 |
...
```

---

### 20:00 技术栈调研 — SQLite + DuckDB + dbt

**背景**：CBDB 的 SQLite 文件缺少表/字段注释（COMMENT），需要为后续数仓建模补充中文元数据。

**调研结论**：

1. **SQLite**：不支持 `COMMENT ON`，无法直接加注释。虽然可以重建表（`ALTER TABLE → INSERT → DROP → RENAME`），但风险大且破坏原始数据
2. **DuckDB**：OLAP 分析引擎，内置 `COMMENT ON` 支持，可通过 `sqlite` 扩展直接 ATTACH SQLite 文件读取数据
3. **dbt**（Data Build Tool）：SQL 转换编排框架，`dbt-duckdb` 适配器可：
   - 在 `profiles.yml` 中配置 DuckDB + sqlite 扩展，直连 SQLite
   - 在 `sources.yml` 定义 SQLite 源表
   - 在 `schema.yml` 用 YAML 写中文注释，dbt run 时自动执行 `COMMENT ON`
   - 通过 model SQL 文件实现 ODS → DWD → DWS → ADS 分层建模

**方案对比**：

| 方案 | 优点 | 缺点 |
|------|------|------|
| 重建 SQLite 表加注释 | 数据留在原处 | 有损操作，风险大 |
| dbt YAML + DuckDB COMMENT | 零侵入源数据，声明式 | 需额外工具链 |

**结论**：采用 dbt + DuckDB 方案，注释写在 YAML 中，不碰 SQLite 原始文件。

---

### 20:40 文档编写 — sqlite-duckdb-guide.md

编写 `docs/sqlite-duckdb-dbt-guide.md`，涵盖：

- **SQLite CLI**：安装方法、常用命令、PRAGMA 查看表结构
- **DuckDB**：安装方法、sqlite 扩展 ATTACH、COMMENT ON 注释、CSV/Parquet 导入导出
- **dbt 教程**：安装 `dbt-duckdb`、项目结构、`profiles.yml` 配置（sqlite ATTACH）、`sources.yml` 定义、model SQL 示例（ODS/DWD/DWS/ADS）、`schema.yml` 中文注释、常用命令
- **完整工作流**：init → develop → run → test → docs → export
- **8 个 Mermaid 图表**辅助理解架构和流程

---

### 21:00 PRD 更新

将 PRD 更新为 dbt 方案：

- 技术栈从"Node.js 零依赖"改为"Node.js（脚本）+ DuckDB（OLAP）+ dbt（建模编排）"
- 2.1 验收标准全部标记已完成（87 表、795 字段、185 外键、0 失败）
- 2.3 从"ETL 脚本"改为"dbt 数仓建模"，含架构图、分层说明、项目结构、中文注释方案
- 非功能需求增加 Python/dbt 依赖
- 风险项更新（dbt 兼容性、初始化复杂度）
- 里程碑细化：M2 已完成，M4 改为 dbt 初始化，新增 M5（全链路）、M6（导出）
