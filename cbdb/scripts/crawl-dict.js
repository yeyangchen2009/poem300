import https from 'node:https';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(__dirname, '..');
const OUTPUT_DIR = path.join(ROOT, 'output');
const BASE_URL = 'https://cbdb.sunan.me/data/';

// 跳过过期 SSL 证书
process.env.NODE_TLS_REJECT_UNAUTHORIZED = '0';

// ---------- 网络请求 ----------
function fetchText(url) {
  return new Promise((resolve, reject) => {
    https.get(url, { timeout: 15000 }, (res) => {
      if (res.statusCode >= 300 && res.statusCode < 400 && res.headers.location) {
        return fetchText(res.headers.location).then(resolve, reject);
      }
      const chunks = [];
      res.on('data', (c) => chunks.push(c));
      res.on('end', () => resolve(Buffer.concat(chunks)));
    }).on('error', reject);
  });
}

// ---------- 编码修复 ----------
// 网站返回的 UTF-8 JSON 中，中文被双重编码（UTF-8 字节被当作 Latin1 再编码为 UTF-8）
// 修复策略：将乱码字符串转为 Latin1 Buffer，再以 UTF-8 解码
function fixEncoding(str) {
  if (!str) return str;
  // 检测是否包含 Unicode 私用区代理对（乱码特征：\udcXX）
  if (!/\udc[\x80-\xbf]/i.test(str)) return str;
  try {
    const buf = Buffer.from(str, 'latin1');
    const fixed = buf.toString('utf-8');
    // 修复后应包含常见中文字符范围
    if (/[一-鿿]/.test(fixed)) return fixed;
  } catch {
    // 修复失败，返回原文
  }
  return str;
}

// ---------- 解析目录页 ----------
function parseFileList(html) {
  const re = /href="([^"]+_data_dict\.json)"/g;
  const files = [];
  let m;
  while ((m = re.exec(html))) files.push(m[1]);
  return files;
}

// ---------- 生成 CSV ----------
function toCSV(tables) {
  // 字段表
  const colHeader = 'table_name,column_name,column_type,notnull,pk,column_desc';
  const colRows = [colHeader];
  for (const t of tables) {
    const tname = t.table || '';
    for (const c of t.columns || []) {
      const desc = fixEncoding(c.desc || '').replace(/"/g, '""');
      colRows.push(
        `${tname},${c.name},${c.type},${c.notnull},${c.pk},"${desc}"`
      );
    }
  }
  // 外键表
  const fkHeader = 'table_name,from_column,target_table,target_column,on_update,on_delete,fk_desc';
  const fkRows = [fkHeader];
  for (const t of tables) {
    const tname = t.table || '';
    for (const fk of t.foreign_keys || []) {
      const desc = fixEncoding(fk.desc || '').replace(/"/g, '""');
      fkRows.push(
        `${tname},${fk.from},${fk.table},${fk.to},${fk.on_update},${fk.on_delete},"${desc}"`
      );
    }
  }
  return { columns: colRows.join('\n'), foreignKeys: fkRows.join('\n') };
}

// ---------- 生成 Markdown ----------
function toMarkdown(tables) {
  const parts = [`# CBDB 数据字典\n`, `> 共 ${tables.length} 张表\n`];
  let totalFK = 0;

  for (const t of tables) {
    const tname = t.table || 'UNKNOWN';
    const tdesc = fixEncoding(t.table_desc || '');
    const cols = t.columns || [];
    const fks = t.foreign_keys || [];

    parts.push(`## ${tname}\n`);
    if (tdesc) parts.push(`${tdesc}\n`);

    // 字段表
    parts.push(`**字段**（${cols.length} 个）\n`);
    parts.push('| 字段名 | 类型 | 非空 | 主键 | 说明 |');
    parts.push('|--------|------|------|------|------|');
    for (const c of cols) {
      const desc = fixEncoding(c.desc || '').replace(/\|/g, '\\|');
      const nn = c.notnull ? '是' : '否';
      const pk = c.pk ? '是' : '否';
      parts.push(`| ${c.name} | ${c.type} | ${nn} | ${pk} | ${desc} |`);
    }

    // 外键表
    if (fks.length > 0) {
      totalFK += fks.length;
      parts.push(`\n**外键**（${fks.length} 个）\n`);
      parts.push('| 字段 | 目标表 | 目标字段 | 更新 | 删除 | 说明 |');
      parts.push('|------|--------|----------|------|------|------|');
      for (const fk of fks) {
        const desc = fixEncoding(fk.desc || '').replace(/\|/g, '\\|');
        parts.push(`| ${fk.from} | ${fk.table} | ${fk.to} | ${fk.on_update} | ${fk.on_delete} | ${desc} |`);
      }
    }

    parts.push('');
  }

  // 汇总统计
  const totalCols = tables.reduce((s, t) => s + (t.columns?.length || 0), 0);
  const tablesWithFK = tables.filter((t) => (t.foreign_keys?.length || 0) > 0).length;
  parts.unshift(`> 共 ${tables.length} 张表，${totalCols} 个字段，${totalFK} 个外键（${tablesWithFK} 张表有外键）\n`);

  return parts.join('\n');
}

// ---------- 主流程 ----------
async function main() {
  fs.mkdirSync(OUTPUT_DIR, { recursive: true });

  // 1. 获取文件列表
  console.error('正在获取文件列表...');
  const indexHtml = (await fetchText(BASE_URL)).toString('utf-8');
  const files = parseFileList(indexHtml);
  console.error(`发现 ${files.length} 个数据字典文件`);

  // 2. 逐个抓取
  const tables = [];
  const failed = [];
  for (let i = 0; i < files.length; i++) {
    const file = files[i];
    const url = new URL(file, BASE_URL).href;
    process.stderr.write(`\r[${i + 1}/${files.length}] ${file}          `);
    try {
      const raw = await fetchText(url);
      const json = JSON.parse(raw.toString('utf-8'));
      tables.push(json);
    } catch (e) {
      failed.push({ file, error: e.message });
      console.error(`\n  失败: ${file} — ${e.message}`);
    }
    // 间隔 200ms，避免请求过快
    await new Promise((r) => setTimeout(r, 200));
  }
  console.error('\n');

  // 按表名排序
  tables.sort((a, b) => (a.table || '').localeCompare(b.table || ''));

  // 3. 输出 JSON
  const jsonPath = path.join(OUTPUT_DIR, 'cbdb_dict.json');
  const jsonMap = {};
  for (const t of tables) jsonMap[t.table] = t;
  fs.writeFileSync(jsonPath, JSON.stringify(jsonMap, null, 2));
  console.error(`JSON → ${jsonPath}`);

  // 4. 输出 CSV（字段 + 外键分开）
  const csvData = toCSV(tables);
  const csvPath = path.join(OUTPUT_DIR, 'cbdb_dict_columns.csv');
  fs.writeFileSync(csvPath, '﻿' + csvData.columns); // BOM for Excel
  console.error(`CSV  → ${csvPath}`);
  const fkCsvPath = path.join(OUTPUT_DIR, 'cbdb_dict_foreign_keys.csv');
  fs.writeFileSync(fkCsvPath, '﻿' + csvData.foreignKeys);
  console.error(`FK   → ${fkCsvPath}`);

  // 5. 输出 Markdown
  const mdPath = path.join(OUTPUT_DIR, 'cbdb_dict.md');
  fs.writeFileSync(mdPath, toMarkdown(tables));
  console.error(`MD   → ${mdPath}`);

  // 6. 汇总报告
  const totalCols = tables.reduce((s, t) => s + (t.columns?.length || 0), 0);
  const totalFK = tables.reduce((s, t) => s + (t.foreign_keys?.length || 0), 0);
  const tablesWithFK = tables.filter((t) => (t.foreign_keys?.length || 0) > 0).length;
  console.error(`\n完成：${tables.length} 张表，${totalCols} 个字段，${totalFK} 个外键（${tablesWithFK} 张表有外键）`);
  if (failed.length) {
    console.error(`失败：${failed.length} 个文件`);
    for (const f of failed) console.error(`  - ${f.file}: ${f.error}`);
  }
}

main().catch((e) => {
  console.error('致命错误:', e);
  process.exit(1);
});
