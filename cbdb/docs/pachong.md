# CBDB 数据字典网站爬取方案

## 目标网站

https://cbdb.sunan.me — CBDB（中国历代人物传记资料库）数据字典在线浏览站

## 网站结构分析

### 技术栈

- **前端框架**：Vue.js 3 + Element Plus + ECharts
- **渲染方式**：SPA（单页应用），页面内容由 JS 动态渲染
- **数据加载**：静态 JSON 文件，路径为 `https://cbdb.sunan.me/data/{表名}_data_dict.json`
- **SSL 证书**：已过期，请求时需忽略证书验证（`curl -k` 或 `NODE_TLS_REJECT_UNAUTHORIZED=0`）

### 数据接口

| 接口 | 说明 |
|------|------|
| `https://cbdb.sunan.me/data/` | 文件目录页，列出所有 JSON 文件 |
| `https://cbdb.sunan.me/data/{表名}_data_dict.json` | 单张表的字典数据 |

### JSON 数据结构

每张表的 JSON 格式：

```json
{
  "table": "BIOG_MAIN",
  "table_desc": "人物传记主表说明（中文，存在编码问题）",
  "columns": [
    {
      "cid": 0,
      "name": "c_personid",
      "type": "INTEGER",
      "notnull": 1,
      "dflt_value": null,
      "pk": 0,
      "desc": "字段说明（中文，存在编码问题）"
    }
  ]
}
```

**可用字段**：`table`（表名）、`columns[].name`（字段名）、`columns[].type`（类型）、`columns[].notnull`（是否非空）、`columns[].pk`（是否主键）

**已知问题**：`table_desc` 和 `columns[].desc` 中的中文存在编码乱码（疑似 GBK → UTF-8 双重编码），需在脚本中尝试修复。

### 文件清单

目录页共列出约 90 个 JSON 文件，涵盖 CBDB 所有表的字典信息。

## 实施方案

### 技术选型

使用 **Node.js** 脚本（项目已有 Node.js 环境，无需额外安装依赖）。

### 脚本逻辑

```
1. 请求 /data/ 目录页，用正则提取所有 JSON 文件名
2. 逐个请求每个 JSON 文件
3. 尝试修复中文编码（若乱码）
4. 整理数据，输出两种格式：
   - cbdb_dict.csv：所有表结构汇总为一张 CSV
   - cbdb_dict.md：按分类组织的 Markdown 文档
5. 保存到 cbdb/docs/ 目录
```

### 输出格式

**CSV 格式**（cbdb_dict.csv）：

| table_name | column_name | column_type | notnull | pk | desc |
|------------|-------------|-------------|---------|-----|------|
| BIOG_MAIN  | c_personid  | INTEGER     | 1       | 0   | ...  |

**Markdown 格式**（cbdb_dict.md）：

按表分章节，每张表包含：
- 表名和说明
- 字段列表表格（字段名、类型、是否必填、说明）
