const fs = require('fs');
const path = require('path');
const { pinyin } = require('pinyin-pro');

const inputFile = path.join(__dirname, 'docs', '唐诗三百首.md');
const outputFile = path.join(__dirname, 'docs', '唐诗三百首_注音版.md');

function addPinyinToLine(line) {
  let pinyinLine = '';
  let charIndex = 0;
  
  while (charIndex < line.length) {
    const char = line[charIndex];
    const regex = /[\u4e00-\u9fa5]/;
    
    if (regex.test(char)) {
      const py = pinyin(char, { toneType: 'number' });
      pinyinLine += `${py} `;
    } else {
      pinyinLine += char + ' ';
    }
    charIndex++;
  }
  return pinyinLine.trim();
}

function addPinyinToText(text) {
  const lines = text.split('\n');
  const result = [];
  
  lines.forEach(line => {
    if (line.trim() === '') {
      result.push(line);
    } else {
      const pinyinLine = addPinyinToLine(line);
      result.push(pinyinLine);
      result.push(line);
    }
  });
  
  return result.join('\n');
}

async function main() {
  try {
    console.log('正在读取唐诗三百首...');
    const content = fs.readFileSync(inputFile, 'utf8');
    
    console.log('正在添加拼音...');
    const result = addPinyinToText(content);
    
    console.log('正在写入文件...');
    fs.writeFileSync(outputFile, result, 'utf8');
    
    console.log(`注音完成！已生成文件: ${outputFile}`);
  } catch (error) {
    console.error('处理过程中发生错误:', error);
  }
}

main();
