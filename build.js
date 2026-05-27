const fs = require('fs');
const path = require('path');
const { pinyin } = require('pinyin-pro');

const inputFile = path.join(__dirname, 'docs', '唐诗三百首.md');
const outputDir = path.join(__dirname, 'dist');
const outputFile = path.join(outputDir, 'data.json');

const CJK_REGEX = /[一-龥]/;

// 需要跳过的非诗歌区域
const SKIP_SECTIONS = ['内容提要', '编选介绍'];

function parseMarkdown(text) {
  const lines = text.split('\n');
  const volumes = [];
  const poems = [];

  let currentVolume = null;
  let currentPoem = null;
  let skipSection = false;

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    const trimmed = line.trim();

    // ## 卷标题
    if (trimmed.startsWith('## ') && !trimmed.startsWith('### ')) {
      const name = trimmed.replace(/^## /, '').trim();

      // 检查是否是需要跳过的非诗歌区域
      skipSection = SKIP_SECTIONS.some(s => name.includes(s));
      if (skipSection) continue;

      currentVolume = {
        id: 'juan' + String(volumes.length + 1).padStart(2, '0'),
        name: name,
      };
      volumes.push(currentVolume);
      currentPoem = null;
      continue;
    }

    if (skipSection) continue;

    // ### 诗标题
    if (trimmed.startsWith('### ')) {
      const match = trimmed.match(/^###\s+(\d{3})\s+(.+)$/);
      if (match) {
        currentPoem = {
          id: poems.length + 1,
          number: match[1],
          title: match[2],
          author: '',
          volumeId: currentVolume ? currentVolume.id : null,
          lines: [],
        };
        poems.push(currentPoem);
      }
      continue;
    }

    if (!currentPoem) continue;

    // > 作者
    if (trimmed.startsWith('>')) {
      currentPoem.author = trimmed.replace(/^>\s*/, '').trim();
      continue;
    }

    // 空行跳过
    if (trimmed === '') continue;

    // 诗文正文行
    currentPoem.lines.push(trimmed);
  }

  return { volumes, poems };
}

function annotateLine(lineText) {
  const chars = [];
  for (const char of lineText) {
    if (CJK_REGEX.test(char)) {
      chars.push({ char, pinyin: pinyin(char, { toneType: 'symbol' }) });
    } else {
      chars.push({ char, pinyin: '' });
    }
  }
  return chars;
}

function annotatePoems(poems) {
  for (const poem of poems) {
    poem.lines = poem.lines.map((lineText) => ({
      text: lineText,
      chars: annotateLine(lineText),
    }));
  }
}

function build() {
  console.log('正在读取唐诗三百首...');
  const content = fs.readFileSync(inputFile, 'utf8');

  console.log('正在解析 Markdown...');
  const { volumes, poems } = parseMarkdown(content);

  console.log(`解析完成：${volumes.length} 卷，${poems.length} 首诗`);

  console.log('正在生成注音...');
  annotatePoems(poems);

  // 确保输出目录存在
  if (!fs.existsSync(outputDir)) {
    fs.mkdirSync(outputDir, { recursive: true });
  }

  const data = { volumes, poems };

  console.log('正在写入 data.json...');
  fs.writeFileSync(outputFile, JSON.stringify(data, null, 2), 'utf8');

  const sizeMB = (Buffer.byteLength(JSON.stringify(data)) / 1024 / 1024).toFixed(2);
  console.log(`data.json 大小：${sizeMB} MB`);

  // 复制页面模板
  const srcHtml = path.join(__dirname, 'src', 'index.html');
  const dstHtml = path.join(outputDir, 'index.html');
  fs.copyFileSync(srcHtml, dstHtml);
  console.log('已复制 index.html → dist/');
  console.log(`构建完成！输出目录：${outputDir}`);
}

build();
