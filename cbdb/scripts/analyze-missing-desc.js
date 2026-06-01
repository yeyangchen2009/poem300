/**
 * 分析缺失中文注释的字段，分类统计
 */
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(__dirname, '..');

// 解析 DDL
const ddlText = fs.readFileSync(path.join(ROOT, 'docs', 'cbdb_tbl.md'), 'utf-8')
  .replace(/\\_/g, '_');

const ddlTables = {};
// 同时提取 DDL 中的 /* ... */ 英文注释
const ddlComments = {};

const createRe = /CREATE TABLE "([^"]+)"\s*\(([\s\S]*?)\)\s*$/gm;
let m;
while ((m = createRe.exec(ddlText)) !== null) {
  const tableName = m[3] || m[1];
  const body = m[4] || m[2];
  const cols = [];
  const comments = {};
  // 匹配 "col_name" type ... /* comment */
  const colCommentRe = /^\s*"([^"]+)"[^/,]*?(?:\/\*\s*(.*?)\s*\*\/)?/gm;
  let cm;
  while ((cm = colCommentRe.exec(body)) !== null) {
    const colName = cm[1];
    if (colName === tableName) continue;
    cols.push(colName);
    if (cm[2]) comments[colName] = cm[2].trim();
  }
  ddlTables[tableName] = [...new Set(cols)];
  if (Object.keys(comments).length > 0) ddlComments[tableName] = comments;
}

// 读取爬虫 JSON
const dictData = JSON.parse(
  fs.readFileSync(path.join(ROOT, 'output', 'cbdb_dict.json'), 'utf-8')
);
const dictMap = {};
for (const [name, info] of Object.entries(dictData)) {
  const colDescs = {};
  for (const c of info.columns || []) colDescs[c.name] = c.desc || '';
  dictMap[name] = { table_desc: info.table_desc || '', col_descs: colDescs };
}

// 分类统计缺失字段
const missing = [];
const auditPattern = /^c_(created|modified)_(by|date)$/;
const yearPattern = /_(firstyear|lastyear|nh_code|nh_year|range|intercalary|month|day|day_gz)$/;

for (const [tName, cols] of Object.entries(ddlTables).sort()) {
  const dict = dictMap[tName];
  for (const col of cols) {
    const hasChineseDesc = dict?.col_descs[col] && dict.col_descs[col].length > 0;
    const hasEnglishComment = ddlComments[tName]?.[col];
    if (!hasChineseDesc) {
      let category = '其他';
      if (auditPattern.test(col)) category = '审计字段';
      else if (yearPattern.test(col)) category = '时间辅助字段';
      else if (col === 'c_notes' || col === 'c_pages' || col === 'c_source') category = '来源/备注字段';
      else if (hasEnglishComment) category = '有英文注释';

      missing.push({ table: tName, column: col, category, englishComment: hasEnglishComment || '' });
    }
  }
}

// 按类别统计
const categories = {};
for (const f of missing) {
  categories[f.category] = (categories[f.category] || 0) + 1;
}

console.log('=== 缺失中文注释的字段分析 ===\n');
console.log(`总计：${missing.length} 个字段缺失中文注释\n`);

console.log('按类别统计：');
for (const [cat, count] of Object.entries(categories).sort((a, b) => b[1] - a[1])) {
  console.log(`  ${cat}：${count} 个`);
}

console.log('\n--- 有英文注释的字段（可直接翻译）---');
const withEn = missing.filter(f => f.category === '有英文注释');
for (const f of withEn) {
  console.log(`  ${f.table}.${f.column}`);
  console.log(`    EN: ${f.englishComment}`);
}

console.log('\n--- 审计字段（可批量补 "创建/修改人/时间"）---');
const auditFields = missing.filter(f => f.category === '审计字段');
const auditTables = [...new Set(auditFields.map(f => f.table))];
console.log(`  涉及 ${auditTables.length} 张表，共 ${auditFields.length} 个字段`);

console.log('\n--- 无描述的表（8 张 DDL 独有）---');
for (const tName of Object.keys(ddlTables).sort()) {
  if (!dictMap[tName]?.table_desc) {
    console.log(`  ${tName}（${ddlTables[tName].length} 字段）`);
  }
}

// 保存详细列表
fs.writeFileSync(
  path.join(ROOT, 'output', 'missing-desc-detail.json'),
  JSON.stringify(missing, null, 2)
);
console.log('\n详细列表已保存到 output/missing-desc-detail.json');
