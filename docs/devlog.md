# DevLog — 唐诗三百首注音网页版（古籍竖排）

## 2026-05-26 开发记录

### 项目背景

将 `docs/唐诗三百首.md` 中 310+ 首唐诗做成古籍竖排风格的静态网页，每首诗一页，支持拼音注音和前后切换。

### 今天的开发过程

#### 1. PRD 编写与调研

- 编写了 [docs/prd-web.md](prd-web.md)，确定技术方案：纯静态站 + Node.js 构建脚本
- 调研了 7 个 GitHub 竖排相关项目（vert-cjk-web、縱書卷軸模板、Rubify、LuaTeX-CN、vRain、charch、赫蹏）
- 最终选定 [赫蹏 (heti)](https://github.com/sivan/heti) 作为排版库：内置古文版式、竖排、行间注、诗词排版，MIT 协议，6.4k stars

#### 2. 开发规划

- 编写了 [docs/dev-plan.md](dev-plan.md)，含 6 张 Mermaid 图（架构图、流程图、状态机、甘特图等）
- 编写了 [docs/dev-plan-visual.html](dev-plan-visual.html)，自包含 HTML 可视化页面，含竖排效果预览

#### 3. 阶段一：构建脚本 build.js

**文件**：`build.js`（新增）

核心逻辑：
- `parseMarkdown()` — 逐行扫描 markdown，识别 `##` 卷标题、`###` 诗标题、`>` 作者、正文行
- 跳过非诗歌区域（"内容提要"、"编选介绍"）
- `annotateLine()` — 用 pinyin-pro 逐字注音，汉字标声调拼音，标点保留不注音
- 输出 `dist/data.json`，每字单独标注 `{ char, pinyin }` 方便前端生成 `<ruby>` 标签
- 同时复制 `src/index.html` → `dist/index.html`

数据验证结果：
- 10 卷，320 首诗，0 首无作者，0 首空诗
- data.json 大小 0.82 MB

遇到的问题：
- 源文件中有 `## 内容提要` 和 `## 编选介绍` 两个非诗歌区域，需要用 `SKIP_SECTIONS` 跳过
- 部分诗后有不属于正文的注释行（如"又作岳"），当前被作为正文行处理，暂不处理

#### 4. 阶段二+三：页面与交互（合并开发）

**文件**：`src/index.html`（新增）

所有前端逻辑写在一个文件中，无框架依赖：

| 模块 | 实现 |
|------|------|
| 布局 | 顶栏 + 侧栏目录 + 内容区 + 底栏，CSS Flexbox |
| 排版 | 赫蹏 `heti--ancient heti--vertical heti--annotation`，宣纸色 + 墨色 |
| 数据加载 | `fetch('data.json')` → 全局状态 |
| 侧栏 | `renderSidebar()` 按卷分组，可折叠，点击切换 |
| 诗文渲染 | `renderPoem()` 逐字生成 `<ruby>` HTML |
| 导航 | 上一首/下一首按钮 + 键盘左右箭头 |
| 路由 | URL hash（`#001`），支持分享和前进后退 |
| 搜索 | 按标题/作者/诗句实时过滤，下拉结果列表 |
| 移动端 | 侧栏折叠为汉堡菜单，`<768px` 响应式适配 |

赫蹏增强脚本：`heti.autoSpacing()` 自动处理中西文间距和标点挤压

#### 5. 样式修复

用户反馈的问题及修复：

| 问题 | 原因 | 修复 |
|------|------|------|
| 看不到作者 | 作者和标题挤在 `<h2>` 的 `<span>` 里，竖排模式下不明显 | 拆分为独立的 `<span class="poem-author">〔唐〕作者</span>`，增加字号和颜色区分 |
| 拼音和汉字间距太近 | `letter-spacing: 2px` + `line-height: 2.4` 偏小 | 调为 `letter-spacing: 4px`，`line-height: 2.8`，诗句 `line-height: 3.2` |
| 诗句行间距不够 | 默认 `<br>` 换行间距不足 | `<p>` 设置 `line-height: 3.2` |

### 文件变更汇总

```
新增:
  build.js                  构建脚本
  src/index.html            页面模板（含全部 JS/CSS）
  dist/data.json            构建产物：320 首诗注音数据
  dist/index.html           构建产物：页面
  docs/prd-web.md           产品需求文档
  docs/dev-plan.md          开发规划（Mermaid）
  docs/dev-plan-visual.html 可视化规划页面

修改:
  package.json              +build/preview scripts
  .gitignore                +dist/

不变:
  docs/唐诗三百首.md        数据源
  add-pinyin.js             旧脚本，保留
  CLAUDE.md                 项目说明
```

### 待办

- [ ] 部署到 GitHub Pages
- [ ] 部分诗后的注释行（如"又作岳"）需要过滤
- [ ] 多浏览器兼容测试

---

## 2026-05-27 更新记录

### 1. 样式修复（用户反馈）

| 问题 | 原因 | 修复 |
|------|------|------|
| 看不到作者 | 竖排模式下作者和标题挤在一起 | 拆为独立 `<span class="poem-author">〔唐〕作者`，18px 灰色 |
| 拼音和汉字间距太近 | `letter-spacing: 2px` 偏小 | 调为 `4px` |
| 诗句行间距不够 | `line-height: 2.4` 偏小 | 诗文 `<p>` 调为 `line-height: 3.2` |

### 2. PRD 更新 — 新增设置面板需求

用户提出需要可自定义的排版设置，已补充到 `docs/prd-web.md`：

| 设置项 | 类型 | 默认值 | 范围 |
|--------|------|--------|------|
| 明暗主题 | 切换 | 浅色 | 浅色 / 深色 / 跟随系统 |
| 字体 | 下拉 | 宋体 | 宋体 / 楷体 / 黑体 / 仿宋 |
| 字号 | 滑块 | 22px | 14–36px |
| 字距 | 滑块 | 4px | 0–12px |
| 行距 | 滑块 | 3.2 | 1.5–5.0 |
| 拼音大小 | 滑块 | 0.42em | 0.2–0.8em |
| 拼音位置 | 切换 | 右侧 | 左侧 / 右侧 |
| 排版方向 | 切换 | 竖排 | 竖排 / 横排 |

设置面板为顶栏齿轮图标触发的侧滑面板，所有设置实时生效，通过 `localStorage` 持久化。

### 3. 开发规划更新 — 新增阶段五

`docs/dev-plan.md` 新增"阶段五：设置面板"：

- 5.1 设置面板 HTML/CSS（侧滑面板 + 表单控件）
- 5.2 明暗主题切换（CSS 变量覆盖 + `data-theme`）
- 5.3 排版参数控件（字体/字号/字距/行距/拼音大小滑块）
- 5.4 拼音位置 + 排版方向切换
- 5.5 localStorage 持久化 + 页面加载恢复
- 5.6 恢复默认按钮 + 验证联动

### 4. Mermaid 图表样式统一

用户要求统一 mermaid 图的配色。根据全局 memory（`~/.claude/memory/feedback-dark-mermaid.md`），IDE 为暗色主题，mermaid 必须使用暗色 fill + 浅色 stroke。已更新项目 memory 并修改 `docs/dev-plan.md` 中全部 mermaid 代码块：

| 节点类型 | fill | stroke | 用途 |
|----------|------|--------|------|
| 数据源/输入 | `#3a2a1a` | `#d4a76a` | 源文件、用户操作入口 |
| 产出/中间件 | `#1a2a3a` | `#90caf9` | 脚本、面板、新增文件 |
| 最终结果 | `#1a2a1a` | `#a5d6a7` | 输出文件、渲染结果 |
| 不变/跳过 | `#2a2a2a` | `#888` | 不变文件、跳过节点 |
| 流程节点 | `#2a2a3a` | `#888` | 中间处理步骤 |

已更新 6 张 mermaid 图的 style 指令：
- 整体架构图
- 数据管线流程图（补全全部节点样式）
- 页面结构图（新增设置面板数据流）
- 导航状态机
- 甘特图（新增阶段五）
- 文件变更图（补全缺失节点样式）

### 文件变更

```
修改:
  docs/prd-web.md           +设置面板需求（9 个设置项 + UI 示意 + 技术要点）
  docs/dev-plan.md           +阶段五任务、+设置面板流程图、mermaid styles 统一
  docs/devlog.md             +本节更新记录

新增:
  ~/.claude/memory/feedback-dark-mermaid.md      全局 memory：暗色 IDE 要求 mermaid 暗色 fill
  memory/feedback-mermaid-styles.md              项目 memory：适配暗色主题的 mermaid 配色方案
  memory/MEMORY.md                                memory 索引
```

---

## 2026-05-27 更新记录（二）— 设置面板实现

### 1. 设置面板 v1 实现

在 `src/index.html` 中添加了侧滑设置面板，包含 8 项设置：

| 设置项 | 控件 | 实现方式 |
|--------|------|----------|
| 明暗主题 | 按钮组（浅色/深色/自动） | `data-theme` 属性切换，auto 跟随 `prefers-color-scheme` |
| 字体 | 下拉选择（宋/楷/黑/仿宋） | CSS 变量 `--poem-font` |
| 字号 | 滑块 14–36px | CSS 变量 `--font-size` |
| 字距 | 滑块 0–12px | CSS 变量 `--letter-spacing` |
| 行距 | 滑块 1.5–5.0 | CSS 变量 `--line-height` |
| 拼音大小 | 滑块 0.2–0.8em | CSS 变量 `--pinyin-size` |
| 拼音位置 | 按钮组（右侧/左侧） | CSS `ruby-position: over/under` |
| 排版方向 | 按钮组（竖排/横排） | CSS `writing-mode` 切换 |

所有设置通过 `localStorage` 持久化，页面加载时恢复。

### 2. 文件变更

```
修改:
  docs/prd-web.md           +设置面板需求（8 个设置项 + UI 示意 + 技术要点）
  docs/dev-plan.md           +阶段五任务、+设置面板流程图、mermaid styles 统一
  docs/devlog.md             +本节更新记录

新增:
  ~/.claude/memory/feedback-dark-mermaid.md      全局 memory：暗色 IDE 要求 mermaid 暗色 fill
  memory/feedback-mermaid-styles.md              项目 memory：适配暗色主题的 mermaid 配色方案
  memory/MEMORY.md                                memory 索引
```

---

## 2026-05-27 更新记录（三）— 注音定位系统重构

### 用户反馈与需求

1. **横排/竖排切换不实时**：修改方向设置后需要手动翻页才能看到效果
2. **标点不明显**：竖排模式下标点符号与汉字挤在一起，缺乏视觉区分
3. **拼音方向问题**：竖排模式下拼音文字也被旋转，无法正常拼读
4. **注音距离**：需要可调节汉字和拼音之间的距离
5. **拼音四方位**：从原来的左/右两个位置扩展为上/下/左/右四个方位

### 2. PRD 更新

设置项变更：

| 变更 | 旧 | 新 |
|------|----|----|
| 拼音位置 | 2 选项（左侧/右侧） | 4 选项（上方/下方/左侧/右侧） |
| 注音距离 | 无 | 新增，滑块 0–16px，默认 2px |
| 默认主题 | 浅色 | 深色 |

技术实现要点更新：
- 不再使用 `<ruby>` 标签，改用自定义 `span.pz` + CSS 绝对定位
- 拼音通过 `writing-mode: horizontal-tb` 始终保持水平显示
- 标点单独包裹为 `<span class="pz-punct">`，增加可见间距
- 排版方向和拼音位置通过 `data-dir` / `data-pos` 属性实时切换，无需重新渲染 HTML

### 3. 注音定位系统重构

**核心改动**：用自定义 `span.pz` 替代 `<ruby>` 标签，实现四方位定位。

**HTML 结构变化**：

```html
<!-- 旧：ruby 标签 -->
<ruby>汉<rp>(</rp><rt>hàn</rt><rp>)</rp></ruby>

<!-- 新：自定义 span -->
<span class="pz">
  <span class="pz-base">汉</span>
  <span class="pz-text">hàn</span>
</span>

<!-- 标点占位 -->
<span class="pz-punct">，</span>
```

**CSS 定位机制**：

```css
.pz { position: relative; display: inline; }
.pz-text { position: absolute; writing-mode: horizontal-tb; }

/* 通过 data-pos 属性选择定位方向 */
.poem-card[data-pos="right"] .pz-text { left: 100%; top: 50%; transform: translateY(-50%); }
.poem-card[data-pos="left"]  .pz-text { right: 100%; top: 50%; transform: translateY(-50%); }
.poem-card[data-pos="top"]   .pz-text { bottom: 100%; left: 50%; transform: translateX(-50%); }
.poem-card[data-pos="bottom"].pz-text { top: 100%; left: 50%; transform: translateX(-50%); }
```

**实时切换机制**：

方向和位置设置通过 `poem-card` 元素的 `data-dir` / `data-pos` 属性控制，`applySettings()` 直接更新属性值，CSS 选择器自动生效，无需重新渲染诗文 HTML。

### 4. 标点处理

通过正则表达式识别中文标点：

```javascript
const PUNCT_RE = /[，。、；：！？""''《》（）—…·「」『』【】〔〕〈〉　-〿＀-￯]/;
```

标点包裹为 `<span class="pz-punct">`，CSS 设置 `min-width: 0.6em` 确保标点在竖排中有足够的视觉空间。

### 文件变更

```
修改:
  docs/prd-web.md           设置项更新（拼音四方位 + 注音距离 + 标点说明）
  docs/devlog.md             +本节更新记录
  src/index.html             注音定位系统重构
  dist/index.html            构建产物更新
  dist/data.json             不变
```

---

## 2026-05-27 更新记录（四）— 长诗滚动 + 标题作者注音

### 1. 长诗滚动

长诗（如长恨歌 840 字、琵琶行 616 字并含诗序 45 行）在竖排模式下生成大量列，内容向左延伸超出可视区域，无法阅读。

**方案**：卡片内滚动。

改动：
- `.poem-view` 的 `overflow` 从 `auto` 改为 `hidden`，不再由视图层滚动
- `.poem-card` 新增 `max-width`（上限 800px）和 `max-height`（基于视口），`overflow: auto`
- 短诗不受影响，卡片按内容尺寸居中显示；长诗在卡片内滚动

**竖排滚动修复**：

初始方案在 `.poem-card`（horizontal-tb）上设 `overflow: auto`，但竖排内容（vertical-rl）向左溢出，卡片层的水平滚动条无法正确匹配竖排阅读方向，导致滚动几乎无效。

修复：竖排模式下将滚动交给 `.poem-body`（vertical-rl 元素），浏览器自动处理正确的滚动方向。横排模式保持卡片自身滚动。

```css
/* 竖排：body 内部滚动 */
.poem-card[data-dir="vertical"] { overflow: hidden; }
.poem-card[data-dir="vertical"] .poem-body {
  writing-mode: vertical-rl;
  max-width: min(calc(100vw - var(--sidebar-w) - 140px), 700px);
  overflow: auto;
}

/* 横排：卡片滚动 */
.poem-card[data-dir="horizontal"] { overflow: auto; }
```

### 2. 标题和作者注音

经用户确认，标题和作者名不需要注音，保持纯文字显示。仅诗文正文逐字注音。

之前曾实现过标题/作者注音（build.js 新增 `titleChars` / `authorChars`，前端渲染 `.pz` 注音），后按用户要求回退。data.json 从 0.90 MB 回到 0.82 MB。

### 文件变更

```
修改:
  build.js                  回退 titleChars/authorChars
  src/index.html             +竖排滚动修复 + 回退标题作者注音
  docs/prd-web.md            标题作者不注音 + 长诗滚动方案更新
  docs/devlog.md             +本节更新记录

构建产物:
  dist/data.json             0.90 MB → 0.82 MB（回退标题作者注音数据）
  dist/index.html            同步更新
```

---

## 2026-05-27 更新记录（五）— 项目文档完善

### 1. 项目 README

新增 `README.md`，包含项目简介、在线预览说明、快速上手、技术栈、项目结构（Mermaid 图）、功能截图描述、开发命令等。

### 2. 适配其他经典的指南

新增 `docs/guide-adapt.md`，详细介绍如何将本项目适配到其他中国古典文献（如《论语》《道德经》《大学》《中庸》等），包含：
- 准备材料清单
- Markdown 源文件格式规范（Mermaid 流程图）
- 数据管线各环节说明（Mermaid 架构图）
- 分步操作流程
- 自定义排版样式的方法

配套可视化页面 `docs/guide-adapt-visual.html`，用暗色/亮色双主题 HTML 展示适配流程和 Markdown 格式示例。

### 文件变更

```
新增:
  README.md                  项目介绍和快速上手
  docs/guide-adapt.md        适配其他经典的指南
  docs/guide-adapt-visual.html  适配流程可视化页面
```

---

## 2026-05-27 更新记录（六）— GitHub Pages 部署踩坑

### 背景

项目已推送到 https://github.com/yeyangchen2009/poem300 ，需要把 `dist/` 目录部署为 GitHub Pages 静态站。

### 踩坑：gh-pages 分支操作导致本地文件消失

**错误做法**：在本地仓库直接切分支、删文件，只留 dist 内容。

```mermaid
flowchart TD
    A["master 分支<br/>所有源文件完整"] --> B["git checkout -b gh-pages"]
    B --> C["gh-pages 分支<br/>（此时文件和 master 一样）"]
    C --> D["git rm -rf .<br/>删除所有跟踪文件"]
    D --> E["工作目录只剩 dist/<br/>其他文件全部消失"]
    E --> F["用户看到文件丢失<br/>体验非常差"]

    style A fill:#1a2a1a,stroke:#a5d6a7,color:#eee
    style B fill:#2a2a3a,stroke:#888,color:#eee
    style C fill:#2a2a3a,stroke:#888,color:#eee
    style D fill:#3a1a1a,stroke:#ef9a9a,color:#eee
    style E fill:#3a1a1a,stroke:#ef9a9a,color:#eee
    style F fill:#3a1a1a,stroke:#ef9a9a,color:#eee
```

**问题根源**：

1. `git checkout -b gh-pages` 创建新分支，工作目录仍指向同一文件夹
2. `git rm -rf .` 从 git 跟踪中移除所有文件，工作目录上的文件也被删除
3. 虽然文件在 master 分支上安全，但用户看到本地文件突然全没了，非常吓人

**正确做法**：不应该在本地分支上做破坏性操作，而应通过远程 API 或独立工作目录完成部署。

```mermaid
flowchart TD
    A["master 分支<br/>所有源文件完整"] --> B{"部署方式选择"}

    B -->|"推荐"| C["gh api 远程创建<br/>gh-pages 分支"]
    B -->|"备选"| D["git worktree<br/>独立工作目录"]
    B -->|"备选"| E["GitHub Actions<br/>自动构建部署"]

    C --> F["本地文件完全不动"]
    D --> G["独立目录操作<br/>不影响主工作区"]
    E --> H["CI 自动完成<br/>无需本地操作"]

    style A fill:#1a2a1a,stroke:#a5d6a7,color:#eee
    style B fill:#2a2a3a,stroke:#888,color:#eee
    style C fill:#1a2a3a,stroke:#90caf9,color:#eee
    style D fill:#1a2a3a,stroke:#90caf9,color:#eee
    style E fill:#1a2a3a,stroke:#90caf9,color:#eee
    style F fill:#1a2a1a,stroke:#a5d6a7,color:#eee
    style G fill:#1a2a1a,stroke:#a5d6a7,color:#eee
    style H fill:#1a2a1a,stroke:#a5d6a7,color:#eee
```

### 恢复操作

```bash
# 切回 master
git checkout master

# 用远程代码覆盖本地（恢复所有文件）
git reset --hard origin/master

# 删除 gh-pages 分支
git branch -D gh-pages
```

### 教训

- **永远不要在主工作目录上做破坏性 git 操作来部署 Pages**
- 部署是远程操作，应尽量通过 API 或 CI 完成，不影响本地文件
- 操作前要向用户解释清楚即将发生什么，尤其是看起来像「删文件」的操作

---

## 2026-05-27 更新记录（七）— GitHub Actions 部署 + 教程文档

### 1. GitHub Actions 部署

最终采用 GitHub Actions 方案部署，本地文件零影响。

**创建的文件**：`.github/workflows/deploy.yml`

流程：push → 触发 workflow → 云端 `npm ci && npm run build` → 上传 dist/ → 部署到 Pages。

**踩坑与修复**：

| 问题 | 原因 | 修复 |
|------|------|------|
| `npm ci` 报错找不到 lock 文件 | `package-lock.json` 在 `.gitignore` 中 | 从 `.gitignore` 移除 `package-lock.json` |
| 首次构建失败 | 同上 | 提交 lock 文件后第二次构建成功 |

**启用 Pages**：

```bash
gh api repos/yeyangchen2009/poem300/pages --method POST \
  -f build_type=workflow -f source[branch]=master -f source[path]=/
```

站点地址：https://yeyangchen2009.github.io/poem300/

### 2. 教程文档

新增 `docs/github-actions-pages-tutorial.md`，包含：

- GitHub Actions 原理（核心概念、workflow 文件结构、sequence 流程图）
- gh CLI 操作 Pages 的常用命令
- 两种方式的异同对比（Mermaid 图 + 对比表格）
- 选择决策流程图
- 本项目实际部署流程图
- 踩坑记录流程图

### 文件变更

```
新增:
  .github/workflows/deploy.yml      GitHub Actions 部署工作流
  docs/github-actions-pages-tutorial.md  Actions + Pages 教程

修改:
  .gitignore                         移除 package-lock.json
  docs/devlog.md                     +本节更新记录
```

---

## 2026-05-28 开发记录

### （八）经典文库扩展方案整理

基于 Kimi 对话内容，整理了从「唐诗三百首注音版」扩展到「经史子集全品类」的产品规划文档。

新增 `docs/classic-library-expansion.md`，包含以下内容：

#### 1. 现有架构评价

对当前技术栈（pinyin-pro + heti + 原生 HTML/CSS/JS + GitHub Pages）的稳定性与适用性评估。

#### 2. 四库全品类扩展的三种技术路线

```mermaid
flowchart TD
    Now["poem300 现有架构"] --> Choice{"扩展方向"}
    Choice -->|"A：继承现有架构"| A["升级构建管线 + 四库分类"]
    Choice -->|"B：docsify/VitePress"| B["文档站体验"]
    Choice -->|"C：Vue 3 + Vite"| C["现代框架"]
```

- **方案 A**：继承现有架构，古籍阅读质感最强，适合个人维护
- **方案 B**：docsify/VitePress 文档站，上手最快，生态丰富
- **方案 C**：Vue 3 + Vite 现代框架，适合团队开发、长期迭代

#### 3. 多音字问题与解决方案

古诗文注音最大的坑——多音字（如「说(yuè)乎」「乐(lè/yào)」）会标错。

解决方案：建立 `corrections.json` 人工校正表，构建时先自动注音再覆盖。

#### 4. 文档站方案补充对比

对比了 docsify、VitePress、MkDocs、Docusaurus、Astro 五种方案的上手难度、竖排控制和构建速度。

#### 5. 亲子共读场景产品设计

核心用户画像：家长（30-45岁）+ 小朋友（6-12岁），需要拼音辅助识字、音频朗读、每日推荐等功能。

#### 6. 平台选型

分阶段策略：网页 MVP 验证 → 微信小程序裂变留存 → App 深度用户。

各平台能力对比（网页 H5 / 微信小程序 / App）涵盖开发成本、音频能力、传播方式、支付等维度。

#### 7. 从内容站到阅读产品的演进

三阶段路线：内容站（¥0）→ 轻账户（¥0-50/月）→ 社区化（¥100-300/月）。

### 文件变更

```
新增:
  docs/classic-library-expansion.md    中华经典文库产品扩展方案

修改:
  docs/devlog.md                       +本节更新记录
```

---

## 2026-05-31 ~ 06-01 开发记录

### （九）诗人传记卡片功能

#### 背景

唐诗三百首网页版中作者名为纯文本，无交互。用户希望利用 CBDB 数据库中的历史人物信息，为 77 位诗人制作传记卡片。点击作者名字即可弹出侧滑面板，展示生卒年、籍贯、字号、入仕途径、官职等传记信息。

#### 数据提取

编写 `cbdb/scripts/export-poet-bio.js`，通过 `better-sqlite3` 查询 CBDB SQLite 数据库，提取 77 位诗人的传记信息。

查询了 11 张 CBDB 表（7 张数据表 + 4 张代码表）：

| 数据表 | 用途 |
|--------|------|
| BIOG_MAIN | 人物主表，匹配诗人（c_name_chn + c_dy） |
| ALTNAME_DATA + ALTNAME_CODES | 字号别号（过滤 type 4,5,6,7,19,20） |
| STATUS_DATA + STATUS_CODES | 社会身份 |
| ENTRY_DATA + ENTRY_CODES | 入仕途径 |
| BIOG_ADDR_DATA + ADDR_CODES | 籍贯地址（c_natal=1 优先） |
| POSTED_TO_OFFICE_DATA + OFFICE_CODES | 主要官职 |

简繁映射：CBDB 用繁体字（王維），项目用简体字（王维），脚本内置 50 个姓名映射。特殊映射如 唐玄宗→李隆基(唐玄宗)、僧皎然→釋皎然。

输出 `src/poet-bio.json`，72/77 位诗人有数据（5 位无 CBDB 记录：无名氏、柳中庸、刘脊虚、朱庆余、邱为）。

#### 构建集成

修改 `build.js`，在构建末尾读取 `poet-bio.json` 合并到 `data.poetBios`，输出到 `dist/data.json`。

#### 前端实现

在 `src/index.html` 中添加传记侧滑面板：

- 作者 `<span>` 加 `data-bio` 属性，有传记数据则绑定点击事件
- 复用设置面板的 overlay + slide-in 交互模式
- 面板内容：生卒年（大号字）、字号别号（药丸标签）、籍贯、入仕途径、官职、社会身份
- ESC 键 / 点击遮罩 / 关闭按钮均可关闭
- 移动端面板宽度 100%

#### 文件变更

```
新增:
  cbdb/scripts/export-poet-bio.js   数据提取脚本
  src/poet-bio.json                 72 位诗人传记静态数据
  cbdb/docs/poet-bio-card.md        技术实现文档

修改:
  build.js                          +poetBios 合并
  src/index.html                    +传记面板 CSS/HTML/JS
```

---

### （十）诗歌系年系地数据调研

#### 背景

用户希望为每首诗标注"创作年份"（系年）和"创作地点"（系地）。CBDB 的粒度是"人物"和"文集"，无单首诗的系年数据。需要调研其他数据源。

#### 调研过程

1. **CBDB**：确认无单首诗系年。TEXT_CODES 表存文集级别（61,070 部），静夜思不在 CBDB 中。

2. **GitHub 开源项目**：chinese-poetry (45k stars) 等 4 个项目，均无系年字段。

3. **发现 cnkgraph.com**：古籍文献知识图谱网，提供开放 Web API，包含王兆鹏教授团队的 62,559 条编年记录。

#### cnkgraph API 实测

解析了 12 个 Postman 集合（71 个端点），验证了关键数据：

| 项目 | 结果 |
|------|------|
| API 地址 | `https://api.cnkgraph.com/api/` |
| 诗文总量 | 2,012,794 首（唐朝 74,805 首） |
| 无需认证 | GET 请求直接返回 JSON |
| 静夜思系年 | `AuthorDate: "727年"`, `AuthorPlace: "湖北省孝感市安陆市"` |
| 李白人物 ID | 15188，返回完整传记（生卒年、17 个别名、官职、籍贯、多部辞书传记原文） |

关键发现：列表接口 `/api/writing/{朝代}/{作者}/{ID}/Poem` 每页 20 首，**已包含完整诗句、评注、用典**。只有 `Links`（结构化编年系地标签）需单独调 `/api/writing/{id}`。

#### 文档输出

`docs/poem-dating-research.md`：完整调研报告，包含 API 端点详解、调用示例、curl/Node.js 示例代码。

#### 文件变更

```
新增:
  docs/poem-dating-research.md    诗歌系年系地数据调研文档

修改:
  docs/devlog.md                  +本节更新记录
```

---

## 2026-06-01 ~ 06-02 开发记录

### （十一）cnkgraph 全量爬虫项目规划

#### 背景

用户指出"这次只爬唐诗三百首，以后扩展还要重新爬"，要求把 cnkgraph 全部数据统统爬下来，一次爬取永久受用。

#### 技术栈选型

对比了 Python 和 Node.js：

| 对比项 | Python | Node.js |
|--------|--------|---------|
| DuckDB 绑定 | 官方一等公民 (1.5.2 已装) | npm 第三方包，API 不全 |
| 异步 HTTP | aiohttp 3.13 已装 | fetch 原生，无连接池 |
| 批量写入 | COPY 极快 | 逐条 INSERT |

**结论：选 Python。** DuckDB 官方绑定 + aiohttp + asyncio，本机已就绪。

#### 数据库设计

25 张表覆盖 cnkgraph 全部 12 个模块，存储为 DuckDB（列式压缩预估 500MB ~ 1GB）。

核心表：

| 模块 | 表 | 预估行数 |
|------|-----|---------|
| 诗文 | writing + writing_clause + writing_comment + writing_link + writing_allusion | 200万 + 2000万 + 400万 + 100万 + 50万 |
| 人物 | person + person_alias + person_hometown + person_detail | 10万 + 50万 + 10万 + 20万 |
| 地理 | region + region_history + scenery | 3千 + 1万 + 1万 |
| 其他 | dynasty, era_year, book, book_volume, glossary, rhyme_entry, rhyme_char, ci_tune, qu_tune, category_entry, char_dict | — |

所有 25 张表已补充 `COMMENT ON TABLE` 和 `COMMENT ON COLUMN` 注释。

#### 爬取策略

5 个阶段，支持断点续爬：

| 阶段 | 内容 | 耗时 |
|------|------|------|
| 1 | 年历（朝代 + 年号） | ~3 min |
| 2 | 人物（15 朝代翻页 + 详情） | ~30 min |
| 3 | 诗文（15 朝代 × 作者 × 翻页） | ~2-10 h |
| 4 | 地理（去重所有 region_id） | ~15 min |
| 5 | 古籍 + 词汇 + 韵典 + 词谱 + 曲谱 + 类书 + 字典 | ~1 h |

并发模型：`asyncio.Semaphore(5)` 控制 5 并发 + 200ms 随机间隔，5 并发约 2-3 小时跑完。

#### 项目结构

```
cnkgraph/
├── data/cnkgraph.duckdb         # 目标数据库
├── docs/prd.md                  # 爬虫 PRD
├── postman/                     # API 参考集合
├── src/
│   ├── crawl.py                 # 主入口 CLI
│   ├── db.py                    # DuckDB 建表 + 写入
│   ├── api.py                   # aiohttp 客户端 + 限速
│   ├── stages/                  # 各阶段爬虫
│   │   ├── stage1_calendar.py
│   │   ├── stage2_people.py
│   │   ├── stage3_writing.py
│   │   ├── stage4_region.py
│   │   └── stage5_reference.py
│   └── models.py                # 数据清洗 + 转换
└── output/                      # 导出产物
```

#### PRD 文档

`cnkgraph/docs/prd.md`：完整爬虫产品需求文档，包含技术选型对比、5 阶段爬取流程图、断点续爬状态机、并发模型、CLI 接口、容错设计、验收标准。

#### 文件变更

```
新增:
  cnkgraph/docs/prd.md                      爬虫 PRD
  cnkgraph/postman/*.json                   API Postman 集合（12 个文件）

修改:
  docs/poem-dating-research.md              +数据库设计（25 张表 DDL + COMMENT）
                                            +全量爬取策略（5 阶段 + 断点续爬）
  docs/devlog.md                            +本节更新记录
```
