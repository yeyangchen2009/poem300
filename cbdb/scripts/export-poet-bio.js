/**
 * export-poet-bio.js
 * 从 CBDB SQLite 提取唐诗三百首 77 位诗人的传记数据，输出为 JSON。
 *
 * 用法: node scripts/export-poet-bio.js
 * 输出: ../src/poet-bio.json
 */

import Database from 'better-sqlite3';
import { readFileSync, writeFileSync } from 'fs';
import { resolve, dirname } from 'path';
import { fileURLToPath } from 'url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const DB_PATH = resolve(__dirname, '../data/cbdb_20260523.sqlite3');
const OUTPUT_PATH = resolve(__dirname, '../../src/poet-bio.json');
const POEMS_PATH = resolve(__dirname, '../../dist/data.json');

const TANG_DY = 6;

// 简体 → CBDB 繁体姓名（或含括号的特殊形式）
// 直接匹配的 22 位无需映射（李白、杜甫、王昌龄(简)→王昌齡 等）
const S2T = {
  '张九龄': '張九齡', '王维': '王維', '王昌龄': '王昌齡',
  '綦毋潜': '綦毋潛', '岑参': '岑參', '元结': '元結',
  '韦应物': '韋應物', '陈子昂': '陳子昂', '李颀': '李頎',
  '韩愈': '韓愈', '李商隐': '李商隱', '高适': '高適',
  '骆宾王': '駱賓王', '杜审言': '杜審言', '宋之问': '宋之問',
  '刘长卿': '劉長卿', '钱起': '錢起', '韩翃': '韓翃',
  '戴叔伦': '戴叔倫', '卢纶': '盧綸', '刘禹锡': '劉禹錫',
  '张籍': '張籍', '许浑': '許渾', '马戴': '馬戴',
  '张乔': '張喬', '崔涂': '崔塗', '杜荀鹤': '杜荀鶴',
  '韦庄': '韋莊', '崔颢': '崔顥', '祖咏': '祖詠',
  '秦韬玉': '秦韜玉', '王之涣': '王之渙', '权德舆': '權德輿',
  '张祜': '張祜', '贾岛': '賈島', '李频': '李頻',
  '金昌绪': '金昌緒', '贺知章': '賀知章', '张旭': '張旭',
  '张继': '張繼', '刘方平': '劉方平', '顾况': '顧況',
  '郑畋': '鄭畋', '韩偓': '韓偓', '陈陶': '陳陶',
  '张泌': '張泌',
  // 特殊映射：CBDB 中以特殊形式记录
  '唐玄宗': '李隆基(唐玄宗)',
  '僧皎然': '釋皎然',
  '西鄙人': '釋西鄙人',
  '杜秋娘': '杜秋娘',
};

// 无名氏、柳中庸、刘脊虚、朱庆余、邱为 在 CBDB 中无记录
const NO_DATA = new Set(['无名氏', '柳中庸', '刘脊虚', '朱庆余', '邱为']);

// 别名类型：字(4)、室名別號(5)、諡號(6)、行第(7)、法號(19)、道號(20)
const ALTNAME_TYPES = { 4: '字', 5: '号', 6: '谥号', 7: '行第', 19: '法号', 20: '道号' };

function getPoetNames() {
  const poems = JSON.parse(readFileSync(POEMS_PATH, 'utf-8'));
  return [...new Set(poems.poems.map(p => p.author))];
}

function main() {
  const db = new Database(DB_PATH, { readonly: true });
  const poets = getPoetNames();
  console.log(`共 ${poets.length} 位诗人，开始提取...\n`);

  const stmtAltname = db.prepare(`
    SELECT a.c_alt_name_chn, a.c_alt_name_type_code, t.c_name_type_desc_chn
    FROM ALTNAME_DATA a
    LEFT JOIN ALTNAME_CODES t ON a.c_alt_name_type_code = t.c_name_type_code
    WHERE a.c_personid = ?
  `);
  const stmtStatus = db.prepare(`
    SELECT s.c_status_code, sc.c_status_desc_chn
    FROM STATUS_DATA s
    JOIN STATUS_CODES sc ON s.c_status_code = sc.c_status_code
    WHERE s.c_personid = ?
  `);
  const stmtEntry = db.prepare(`
    SELECT e.c_entry_code, ec.c_entry_desc_chn, e.c_year
    FROM ENTRY_DATA e
    JOIN ENTRY_CODES ec ON e.c_entry_code = ec.c_entry_code
    WHERE e.c_personid = ?
  `);
  const stmtAddr = db.prepare(`
    SELECT ba.c_addr_id, ba.c_addr_type, ba.c_firstyear, ba.c_lastyear,
           ba.c_natal, ac.c_name_chn, ac.x_coord, ac.y_coord
    FROM BIOG_ADDR_DATA ba
    JOIN ADDR_CODES ac ON ba.c_addr_id = ac.c_addr_id
    WHERE ba.c_personid = ?
    ORDER BY ba.c_firstyear ASC
  `);
  const stmtOffice = db.prepare(`
    SELECT p.c_office_id, p.c_firstyear, p.c_lastyear,
           oc.c_office_chn
    FROM POSTED_TO_OFFICE_DATA p
    JOIN OFFICE_CODES oc ON p.c_office_id = oc.c_office_id
    WHERE p.c_personid = ?
    ORDER BY p.c_firstyear ASC
  `);

  const result = {};
  let matchCount = 0;

  for (const poetName of poets) {
    if (NO_DATA.has(poetName)) {
      result[poetName] = null;
      continue;
    }

    // 查找 CBDB 人物 ID
    const cbdbName = S2T[poetName] || poetName;
    const findBiog = db.prepare(
      'SELECT * FROM BIOG_MAIN WHERE c_name_chn = ? AND c_dy = ?'
    );
    let person = findBiog.get(cbdbName, TANG_DY);

    // 如果唐朝匹配不到，放宽朝代限制（如崔曙 c_dy=15 实为唐代）
    if (!person) {
      person = db.prepare(
        'SELECT * FROM BIOG_MAIN WHERE c_name_chn = ?'
      ).get(cbdbName);
    }

    // 如果名字含括号（如"李隆基(唐玄宗)"），尝试 LIKE 匹配
    if (!person && cbdbName.includes('(')) {
      person = db.prepare(
        "SELECT * FROM BIOG_MAIN WHERE c_name_chn LIKE ? AND c_dy = ?"
      ).get(`%${cbdbName.replace(/[()]/g, '%')}%`, TANG_DY);
    }

    if (!person) {
      console.log(`  ⚠ 未找到: ${poetName}`);
      result[poetName] = null;
      continue;
    }

    matchCount++;
    const pid = person.c_personid;

    // 字号
    const altnames = stmtAltname.all(pid);
    const altNameList = altnames
      .filter(a => a.c_alt_name_chn && ALTNAME_TYPES[a.c_alt_name_type_code])
      .map(a => `${ALTNAME_TYPES[a.c_alt_name_type_code]}${a.c_alt_name_chn}`);

    // 社会身份（去重，取前 5 个）
    const statuses = [...new Set(stmtStatus.all(pid).map(s => s.c_status_desc_chn).filter(Boolean))].slice(0, 5);

    // 入仕途径（去重）
    const entries = [...new Set(stmtEntry.all(pid).map(e => e.c_entry_desc_chn).filter(Boolean))].slice(0, 3);

    // 籍贯（优先取 c_natal=1 或第一个地址）
    const addrs = stmtAddr.all(pid);
    const hometown = addrs.find(a => a.c_natal === 1) || addrs[0];

    // 主要官职（取前 5 个，去重）
    const offices = stmtOffice.all(pid);
    const officeList = [...new Set(offices.map(o => o.c_office_chn).filter(Boolean))].slice(0, 5);

    result[poetName] = {
      birthYear: person.c_birthyear || null,
      deathYear: person.c_deathyear || null,
      dynasty: '唐',
      altNames: altNameList.length ? altNameList : undefined,
      hometown: hometown?.c_name_chn || undefined,
      hometownCoord: (hometown?.x_coord && hometown?.y_coord)
        ? [parseFloat(hometown.y_coord), parseFloat(hometown.x_coord)]
        : undefined,
      status: statuses.length ? statuses : undefined,
      entry: entries.length ? entries : undefined,
      offices: officeList.length ? officeList : undefined,
    };

    // 日志
    const info = [];
    if (person.c_birthyear) info.push(`${person.c_birthyear}-${person.c_deathyear || '?'}`);
    if (altNameList.length) info.push(altNameList.join('、'));
    console.log(`  ✓ ${poetName} #${pid}  ${info.join(' | ')}`);
  }

  db.close();

  writeFileSync(OUTPUT_PATH, JSON.stringify(result, null, 2), 'utf-8');
  console.log(`\n完成: ${matchCount}/${poets.length} 位诗人有传记数据`);
  console.log(`输出: ${OUTPUT_PATH}`);
}

main();
