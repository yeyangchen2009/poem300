/**
 * 对比 cbdb_tbl.md（SQLite DDL）与 cbdb_dict.json（爬虫数据字典）的字段差异
 * 用法：node scripts/compare-schema.js
 */
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(__dirname, '..');

// 1. 解析 DDL 文件
const ddlPath = path.join(ROOT, 'docs', 'cbdb_tbl.md');
const ddlText = fs.readFileSync(ddlPath, 'utf-8');
// Markdown 中下划线被转义为 \_，还原
const cleanDdl = ddlText.replace(/\\_/g, '_');

// 提取 CREATE TABLE 块
const ddlTables = {};
const createRe = /CREATE TABLE "([^"]+)"\s*\(([\s\S]*?)\)\s*$/gm;
let m;
while ((m = createRe.exec(cleanDdl)) !== null) {
  const tableName = m[1];
  const body = m[2];
  // 提取列名（排除 PRIMARY KEY 行）
  const cols = [];
  const colRe = /^\s*"([^"]+)"/gm;
  let cm;
  while ((cm = colRe.exec(body)) !== null) {
    const colName = cm[1];
    // 跳过 PRIMARY KEY 行中的列引用
    if (colName === tableName) continue;
    cols.push(colName);
  }
  // 去重（PRIMARY KEY 行可能重复引用列名）
  ddlTables[tableName] = [...new Set(cols)];
}

// 2. 读取爬虫 JSON
const jsonPath = path.join(ROOT, 'output', 'cbdb_dict.json');
const dictData = JSON.parse(fs.readFileSync(jsonPath, 'utf-8'));

const dictTables = {};
for (const [name, info] of Object.entries(dictData)) {
  dictTables[name] = (info.columns || []).map(c => c.name);
}

// 3. 对比
const ddlNames = Object.keys(ddlTables).sort();
const dictNames = Object.keys(dictTables).sort();

const onlyInDDL = ddlNames.filter(n => !dictTables[n]);
const onlyInDict = dictNames.filter(n => !ddlTables[n]);
const common = ddlNames.filter(n => dictTables[n]);

let fieldDiffCount = 0;
const fieldDiffs = [];

for (const name of common) {
  const ddlCols = ddlTables[name];
  const dictCols = dictTables[name];

  const onlyInDDLFields = ddlCols.filter(c => !dictCols.includes(c));
  const onlyInDictFields = dictCols.filter(c => !ddlCols.includes(c));

  if (onlyInDDLFields.length > 0 || onlyInDictFields.length > 0) {
    fieldDiffCount++;
    fieldDiffs.push({
      table: name,
      only_ddl: onlyInDDLFields,
      only_dict: onlyInDictFields,
      ddl_count: ddlCols.length,
      dict_count: dictCols.length,
    });
  }
}

// 4. 输出报告
console.log('=== DDL vs 爬虫数据字典 对比报告 ===\n');
console.log(`DDL 表数量：${ddlNames.length}`);
console.log(`爬虫 表数量：${dictNames.length}`);
console.log(`共有表数量：${common.length}`);
console.log();

console.log(`仅在 DDL 中（${onlyInDDL.length} 张）：`);
onlyInDDL.forEach(n => console.log(`  - ${n}（${ddlTables[n].length} 字段）`));
console.log();

console.log(`仅在爬虫中（${onlyInDict.length} 张）：`);
onlyInDict.forEach(n => console.log(`  - ${n}（${dictTables[n].length} 字段）`));
console.log();

console.log(`字段完全一致：${common.length - fieldDiffCount} 张`);
console.log(`字段有差异：${fieldDiffCount} 张`);
console.log();

if (fieldDiffs.length > 0) {
  console.log('--- 字段差异详情 ---');
  for (const d of fieldDiffs) {
    console.log(`\n[${d.table}] DDL=${d.ddl_count}字段 爬虫=${d.dict_count}字段`);
    if (d.only_ddl.length > 0) console.log(`  DDL多出：${d.only_ddl.join(', ')}`);
    if (d.only_dict.length > 0) console.log(`  爬虫多出：${d.only_dict.join(', ')}`);
  }
}

// 5. 输出 JSON 供后续使用
const report = {
  ddl_count: ddlNames.length,
  dict_count: dictNames.length,
  common_count: common.length,
  only_in_ddl: onlyInDDL,
  only_in_dict: onlyInDict,
  field_match_count: common.length - fieldDiffCount,
  field_diff_count: fieldDiffCount,
  field_diffs: fieldDiffs,
};
fs.writeFileSync(
  path.join(ROOT, 'output', 'schema-compare-report.json'),
  JSON.stringify(report, null, 2)
);
console.log('\n报告已保存到 output/schema-compare-report.json');
