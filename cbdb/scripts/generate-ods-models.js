/**
 * 生成完善的 ODS 层文件（v2）：
 * - sources.yml：77 张源表，字段含完整中文注释
 * - ods_cbdb_*.sql：显式列出字段名 + 行内注释
 * - ods/schema.yml：model 描述 + 列级描述
 */
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(__dirname, '..');
const DBT_MODELS = path.join(ROOT, 'cbdb_dw', 'models');
const ODS_DIR = path.join(DBT_MODELS, 'ods');

// ========== 1. 解析 DDL ==========
const ddlText = fs.readFileSync(path.join(ROOT, 'docs', 'cbdb_tbl.md'), 'utf-8')
  .replace(/\\_/g, '_');

const ddlTables = {};
const rowCounts = {};
const createRe = /## [A-Z_]+\s*\n\s*[A-Z_]+\s*\n\s*(\d+)\s*\n\s*CREATE TABLE "([^"]+)"\s*\(([\s\S]*?)\)\s*$/gm;
let m;
while ((m = createRe.exec(ddlText)) !== null) {
  const rowCount = parseInt(m[1]);
  const tableName = m[2];
  const body = m[3];
  const cols = [];
  const colRe = /^\s*"([^"]+)"/gm;
  let cm;
  while ((cm = colRe.exec(body)) !== null) {
    if (cm[1] === tableName) continue;
    cols.push(cm[1]);
  }
  ddlTables[tableName] = [...new Set(cols)];
  rowCounts[tableName] = rowCount;
}

// ========== 2. 读取爬虫 JSON ==========
const dictData = JSON.parse(
  fs.readFileSync(path.join(ROOT, 'output', 'cbdb_dict.json'), 'utf-8')
);
const dictMap = {};
for (const [name, info] of Object.entries(dictData)) {
  const colDescs = {};
  for (const c of info.columns || []) colDescs[c.name] = c.desc || '';
  dictMap[name] = { table_desc: info.table_desc || '', col_descs: colDescs };
}

// ========== 3. 缺失注释补充规则 ==========
// 批量规则：按字段名模式匹配
const batchRules = [
  // 审计字段
  { pattern: /^c_created_by$/, desc: '记录创建人' },
  { pattern: /^c_created_date$/, desc: '记录创建时间' },
  { pattern: /^c_modified_by$/, desc: '记录修改人' },
  { pattern: /^c_modified_date$/, desc: '记录修改时间' },
  // 来源/备注
  { pattern: /^c_notes$/, desc: '备注说明' },
  { pattern: /^c_source$/, desc: '资料来源ID' },
  { pattern: /^c_pages$/, desc: '资料页码' },
  // 时间辅助
  { pattern: /_nh_code$/, desc: '年号编码' },
  { pattern: /_nh_year$/, desc: '年号年份' },
  { pattern: /_range$/, desc: '年份范围标识' },
  { pattern: /_intercalary$/, desc: '闰月标识' },
  { pattern: /_month$/, desc: '月份' },
  { pattern: /_day_gz$/, desc: '日干支编码' },
  { pattern: /_day$/, desc: '日期（日）' },
];

// 8 张 DDL 独有表的表级和字段级描述
const manualTableDescs = {
  ADMIN_CAT_CODES: '行政区类别代码表，定义行政区划的类型编码',
  ADMIN_CAT_CODE_TYPE_REL: '行政区类别与类型的关联关系表',
  ADMIN_CAT_TYPES: '行政区类型代码表，定义行政区划类型分类',
  APPOINTMENT_CODES: '任命方式代码表，定义官员任命的具体方式',
  APPOINTMENT_CODE_TYPE_REL: '任命方式与类型的关联关系表',
  APPOINTMENT_TYPES: '任命类型代码表，定义任命方式的分类',
  KIN_MOURNING: '亲属丧服关系表，记录亲属关系的丧服等级和服属类型',
  MERGED_PERSON_DATA: '人物合并记录表，记录已合并的重复人物ID',
};

const manualFieldDescs = {
  // ADMIN_CAT_CODES
  'ADMIN_CAT_CODES.c_admin_cat_code': '行政区类别编码',
  'ADMIN_CAT_CODES.c_admin_cat_py': '行政区类别拼音名',
  'ADMIN_CAT_CODES.c_admin_cat_hz': '行政区类别中文名',
  'ADMIN_CAT_CODES.c_admin_cat_trans': '行政区类别英文名',
  // ADMIN_CAT_CODE_TYPE_REL
  'ADMIN_CAT_CODE_TYPE_REL.c_admin_cat_code': '行政区类别编码',
  'ADMIN_CAT_CODE_TYPE_REL.c_admin_cat_type_code': '行政区类型编码',
  // ADMIN_CAT_TYPES
  'ADMIN_CAT_TYPES.c_admin_cat_type_code': '行政区类型编码',
  'ADMIN_CAT_TYPES.c_admin_cat_type_hz': '行政区类型中文名',
  'ADMIN_CAT_TYPES.c_admin_cat_type_trans': '行政区类型英文名',
  // APPOINTMENT_CODES
  'APPOINTMENT_CODES.c_appt_code': '任命方式编码',
  'APPOINTMENT_CODES.c_appt_desc_chn': '任命方式中文描述',
  'APPOINTMENT_CODES.c_appt_desc': '任命方式英文描述',
  'APPOINTMENT_CODES.c_appt_desc_chn_alt': '任命方式中文别名',
  'APPOINTMENT_CODES.c_appt_desc_alt': '任命方式英文别名',
  // APPOINTMENT_CODE_TYPE_REL
  'APPOINTMENT_CODE_TYPE_REL.c_appt_code': '任命方式编码',
  'APPOINTMENT_CODE_TYPE_REL.c_appt_type_code': '任命类型编码',
  // APPOINTMENT_TYPES
  'APPOINTMENT_TYPES.c_appt_type_code': '任命类型编码',
  'APPOINTMENT_TYPES.c_appt_type_desc': '任命类型英文描述',
  'APPOINTMENT_TYPES.c_appt_type_desc_chn': '任命类型中文描述',
  // KIN_MOURNING
  'KIN_MOURNING.c_kinrel': '亲属关系英文名（主键）',
  'KIN_MOURNING.c_kinrel_alt': '亲属关系英文别名',
  'KIN_MOURNING.c_kinrel_chn': '亲属关系中文名',
  'KIN_MOURNING.c_mourning': '丧服等级英文名',
  'KIN_MOURNING.c_mourning_chn': '丧服等级中文名',
  'KIN_MOURNING.c_kindist': '亲属距离等级',
  'KIN_MOURNING.c_kintype': '亲属类型编码',
  'KIN_MOURNING.c_kintype_desc': '亲属类型英文描述',
  'KIN_MOURNING.c_kintype_desc_chn': '亲属类型中文描述',
  // MERGED_PERSON_DATA
  'MERGED_PERSON_DATA.c_personid': '合并后保留的人物ID',
  'MERGED_PERSON_DATA.c_merged_from_personid': '被合并的原始人物ID',
  // DDL 有但爬虫无的字段（版本差异）
  'ADDR_CODES.c_admin_cat_code': '行政区类别编码',
  'BIOG_MAIN.c_self_bio': '是否为自传人物',
  'ASSOC_DATA.c_assoc_first_year': '社交关系起始年份',
  'ASSOC_DATA.c_assoc_last_year': '社交关系结束年份',
  'ASSOC_DATA.c_assoc_fy_nh_code': '起始年年号编码',
  'ASSOC_DATA.c_assoc_fy_nh_year': '起始年年号年份',
  'ASSOC_DATA.c_assoc_fy_range': '起始年年份范围标识',
  'ASSOC_DATA.c_assoc_ly_nh_code': '结束年年号编码',
  'ASSOC_DATA.c_assoc_ly_nh_year': '结束年年号年份',
  'ASSOC_DATA.c_assoc_ly_range': '结束年年份范围标识',
  'ASSOC_DATA.c_assoc_fy_intercalary': '起始年闰月标识',
  'ASSOC_DATA.c_assoc_fy_month': '起始年月份',
  'ASSOC_DATA.c_assoc_fy_day': '起始年日期',
  'ASSOC_DATA.c_assoc_fy_day_gz': '起始年日干支编码',
  'ASSOC_DATA.c_assoc_ly_intercalary': '结束年闰月标识',
  'ASSOC_DATA.c_assoc_ly_month': '结束年月份',
  'ASSOC_DATA.c_assoc_ly_day': '结束年日期',
  'ASSOC_DATA.c_assoc_ly_day_gz': '结束年日干支编码',
  'ENTRY_DATA.c_entry_nh_id': '入仕年号ID',
  'ENTRY_DATA.c_entry_dy': '入仕朝代编码',
  'ENTRY_DATA.c_parental_status_code': '父辈身份状态编码',
  'POSTED_TO_OFFICE_DATA.c_appt_code': '任命方式编码',
  'ASSOC_CODE_TYPE_REL.c_assoc_type_code': '关联类型标识符，指向ASSOC_TYPES表，定义社交关系的分类层级',
  'ASSOC_TYPES.c_assoc_type_code': '关联类型唯一标识符，用于区分不同类型的社会关系分类',
  'YEAR_RANGE_CODES.c_approx': '约数标识英文',
  'YEAR_RANGE_CODES.c_approx_chn': '约数标识中文',
  'EVENTS_ADDR.c_event_code': '事件编码',
  'EVENTS_ADDR.c_sequence': '事件序号',
};

// ========== 4. 获取完整注释 ==========
function getDescription(tableName, colName) {
  // 优先级1: 爬虫 JSON 的中文注释
  const dict = dictMap[tableName];
  if (dict?.col_descs[colName]) return dict.col_descs[colName];

  // 优先级2: 手动定义的注释
  const key = `${tableName}.${colName}`;
  if (manualFieldDescs[key]) return manualFieldDescs[key];

  // 优先级3: 批量规则匹配
  for (const rule of batchRules) {
    if (rule.pattern.test(colName)) return rule.desc;
  }

  // 优先级4: 无法推断，返回空
  return '';
}

function getTableDesc(tableName) {
  if (dictMap[tableName]?.table_desc) return dictMap[tableName].table_desc;
  if (manualTableDescs[tableName]) return manualTableDescs[tableName];
  return `${tableName}`;
}

// ========== 5. YAML 辅助 ==========
function yamlStr(s) {
  if (!s) return '""';
  if (/[":{}\[\]#\n&*?|>!%@`']/.test(s) || s.startsWith(' ')) {
    return `"${s.replace(/\\/g, '\\\\').replace(/"/g, '\\"')}"`;
  }
  return s;
}

// ========== 6. 生成 sources.yml ==========
function genSourcesYml() {
  const L = ['version: 2', '', 'sources:', '  - name: cbdb_src',
    '    description: "CBDB 中国历代人物传记资料库（SQLite 源库，77 张实表）"',
    '    database: cbdb_src', '    schema: main', '    tables:'];
  for (const tName of Object.keys(ddlTables).sort()) {
    L.push('', `      - name: ${tName}`);
    L.push(`        description: ${yamlStr(getTableDesc(tName))}`);
    L.push('        meta:', `          row_count: ${rowCounts[tName] || 0}`);
    L.push('        columns:');
    for (const col of ddlTables[tName]) {
      const desc = getDescription(tName, col);
      L.push(`          - name: ${col}`);
      if (desc) L.push(`            description: ${yamlStr(desc)}`);
    }
    // 注意：sources.yml 不加 ETL 字段，它们不在 SQLite 源表中
  }
  return L.join('\n');
}

// ========== 7. 生成 ODS SQL（显式字段） ==========
function genOdsSql(tName) {
  const cols = ddlTables[tName];
  const L = [
    '{{ config(materialized=\'table\') }}',
    '',
    `-- ODS: ${getTableDesc(tName)}`,
    `-- 源表: ${tName}（${rowCounts[tName] || 0} 行）`,
    '',
    'SELECT',
  ];
  cols.forEach((col, i) => {
    const desc = getDescription(tName, col);
    const comma = ',';
    const comment = desc ? `  -- ${desc}` : '';
    L.push(`    ${col}${comma}${comment}`);
  });
  L.push('    CAST(DATE_TRUNC(\'second\', NOW()) AS TIMESTAMP) AS ETL_LOAD_DATETIME,  -- ETL加载时间');
  L.push('    CURRENT_DATE              AS ETL_LOAD_DATE       -- ETL加载数据日期');
  L.push(`FROM {{ source('cbdb_src', '${tName}') }}`, '');
  return L.join('\n');
}

// ========== 8. 生成 ODS schema.yml（含列描述） ==========
function genOdsSchemaYml() {
  const L = ['version: 2', '', 'models:'];
  for (const tName of Object.keys(ddlTables).sort()) {
    const model = `ods_cbdb_${tName.toLowerCase()}`;
    L.push('', `  - name: ${model}`);
    L.push(`    description: ${yamlStr(getTableDesc(tName))}`);
    L.push('    meta:', `      source_table: ${tName}`, `      row_count: ${rowCounts[tName] || 0}`);
    L.push('    columns:');
    for (const col of ddlTables[tName]) {
      const desc = getDescription(tName, col);
      L.push(`      - name: ${col}`);
      if (desc) L.push(`        description: ${yamlStr(desc)}`);
    }
    L.push('      - name: ETL_LOAD_DATETIME');
    L.push('        description: "ETL加载时间"');
    L.push('      - name: ETL_LOAD_DATE');
    L.push('        description: "ETL加载数据日期"');
  }
  return L.join('\n');
}

// ========== 9. 写入文件 ==========
fs.mkdirSync(ODS_DIR, { recursive: true });

const sourcesPath = path.join(DBT_MODELS, 'sources.yml');
fs.writeFileSync(sourcesPath, genSourcesYml());
console.log(`✓ ${path.relative(ROOT, sourcesPath)}`);

for (const tName of Object.keys(ddlTables)) {
  fs.writeFileSync(path.join(ODS_DIR, `ods_cbdb_${tName.toLowerCase()}.sql`), genOdsSql(tName));
}
console.log(`✓ models/ods/ods_cbdb_*.sql (${Object.keys(ddlTables).length} files)`);

const schemaPath = path.join(ODS_DIR, 'schema.yml');
fs.writeFileSync(schemaPath, genOdsSchemaYml());
console.log(`✓ ${path.relative(ROOT, schemaPath)}`);

// 统计
const tableNames = Object.keys(ddlTables);
let totalCols = 0, coveredCols = 0;
for (const t of tableNames) {
  for (const c of ddlTables[t]) {
    totalCols++;
    if (getDescription(t, c)) coveredCols++;
  }
}
console.log(`\n注释覆盖率：${coveredCols}/${totalCols}（${(coveredCols / totalCols * 100).toFixed(1)}%）`);
