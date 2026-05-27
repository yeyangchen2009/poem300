# PRD — 唐诗三百首注音网页版（古籍竖排）

## 目标

将 `docs/唐诗三百首.md` 中的 310 首唐诗制作成一个可浏览的静态网页，采用**古籍竖排（从右到左）**排版风格，每首诗一个页面视图，支持前后切换，汉字旁注拼音。

## 数据结构

源文件 `唐诗三百首.md` 的格式：

```
## 卷01-五言古诗          ← 卷标题（##）
### 001 感遇其一           ← 诗标题（### 编号 名称）
> 张九龄                   ← 作者（> 开头）
                            ← 空行
孤鸿海上来，池潢不敢顾；   ← 诗文正文
```

共 8 个卷（## 标题），320 个 `###` 条目（含个别附录条目），实际约 310 首诗。

## 技术方案

纯静态站，无需后端。两个构建步骤：

1. **解析脚本** (`build.js`) — 读取 markdown → 解析为 JSON → 生成注音数据 → 输出到 `dist/`
2. **前端页面** — 单个 `index.html`，通过 JS 读取 JSON 数据，客户端渲染

### 为什么不做成 310 个独立 HTML 文件

- 切换时整页加载体验差
- 共享的导航/样式需重复输出
- 单页 + 路由方案更轻量、更快

## 竖排排版调研

### 核心技术：CSS `writing-mode`

浏览器原生支持竖排排版，核心 CSS：

```css
body {
  writing-mode: vertical-rl;     /* 竖排，从右到左 */
  text-orientation: upright;     /* 字符正立 */
}
```

这是 W3C 标准属性，Chrome/Firefox/Safari/Edge 全部支持，无需第三方库即可实现古籍竖排效果。

竖排模式下 `<ruby>` 注音会自动显示在文字右侧（而非上方），天然适配古籍"旁注"风格。

### 选定的排版库：赫蹏 (heti) — 已采纳

**[赫蹏](https://github.com/sivan/heti)**（6.4k stars，MIT 协议）是专为中文网页内容设计的排版样式增强库，直接命中本项目全部排版需求：

| 需求 | 赫蹏对应能力 | 用法 |
|------|-------------|------|
| 竖排排版 | 预置竖排样式 | `class="heti heti--vertical"` |
| 诗词排版 | 预置诗词版式 | `class="heti heti--poetry"` |
| 古文排版 | 预置古文版式 | `class="heti heti--ancient"` |
| 行间注（拼音注音） | 预置行间注版式 + ruby | `class="heti heti--annotation"` |
| 标点悬挂 | 标点偏移不占版面 | `class="heti-hang"` |
| 中西文混排 | 增强脚本自动处理 | `heti.autoSpacing()` |
| 标点挤压 | 增强脚本自动处理 | `heti.autoSpacing()` |
| 简繁中文支持 | 内置 | 开箱即用 |
| 自适应黑暗模式 | 内置 | 开箱即用 |
| 多栏排版 | 预置 | `class="heti--columns-2"` |

引入方式：

```html
<link rel="stylesheet" href="//unpkg.com/heti/umd/heti.min.css">
<script src="//unpkg.com/heti/umd/heti-addon.min.js"></script>
<script>
  const heti = new Heti('.heti');
  heti.autoSpacing();
</script>
```

本项目计划组合使用 `heti--ancient`（古文版式）+ `heti--vertical`（竖排）+ `heti--annotation`（行间注），配合 `<ruby>` 标签实现古籍竖排注音效果。

### 其他调研项目（未采纳）

| 项目 | 地址 | 未采纳原因 |
|------|------|-----------|
| **vert-cjk-web** | [github.com/garywill/vert-cjk-web](https://github.com/garywill/vert-cjk-web) | 浏览器扩展，用 iframe + transform 逆向改造已有网页，我们是原生构建 |
| **Traditional-Chinese-Vertical-Writing-Typesetting-Template** | [github.com/wujimacha/...](https://github.com/wujimacha/Traditional-Chinese-Vertical-Writing-Typesetting-Template) | InDesign 模板，非网页技术；设计风格可参考 |
| **Rubify** | [github.com/dohliam/rubify](https://github.com/dohliam/rubify) | Ruby 注音生成器；我们用 pinyin-pro 后端生成更方便，且该项目明确提到竖排 ruby 浏览器支持尚不完善 |
| **LuaTeX-CN** | [github.com/open-guji/luatex-cn](https://github.com/open-guji/luatex-cn) | LuaTeX 排版引擎，输出 PDF，非网页 |
| **vRain** | [github.com/shanleiguang/vRain](https://github.com/shanleiguang/vRain) | Perl 刻本风格电子书工具，非网页 |
| **charch** | [github.com/shuding/charch](https://github.com/shuding/charch) | 中文网页排版库，功能有限，不涉及竖排 |

### 参考规范

- [赫蹏在线预览](https://sivan.github.io/heti/) — 包含古文、诗词、行间注、竖排等完整示例
- [W3C: Styling vertical CJK text](https://www.w3.org/International/articles/vertical-text/) — CSS 竖排权威指南
- [W3C: 中文排版需求 (clreq)](https://xfq.github.io/testing/clreq-mobile/) — 中文排版完整规范

## 文件规划

```
pinyin/
├── build.js              ← 新增：构建脚本，解析 markdown → 生成 dist/
├── src/
│   └── index.html        ← 新增：单页应用模板
├── dist/                  ← 新增：构建输出（gitignore）
│   ├── index.html
│   └── data.json         ← 所有诗 + 拼音注音
├── add-pinyin.js          ← 保留，不受影响
├── docs/
│   ├── 唐诗三百首.md
│   └── prd-web.md         ← 本文件
└── package.json
```

## 构建脚本 build.js 职责

1. 读取 `docs/唐诗三百首.md`
2. 按行解析出结构：卷列表 → 诗列表（编号、标题、作者、正文行）
3. 用 `pinyin-pro` 给每行诗文的每个汉字生成注音
4. 输出 `dist/data.json`：

```json
{
  "volumes": [
    { "id": "juan01", "name": "卷01-五言古诗" }
  ],
  "poems": [
    {
      "id": 1,
      "number": "001",
      "title": "感遇其一",
      "author": "张九龄",
      "volumeId": "juan01",
      "lines": [
        {
          "text": "孤鸿海上来，池潢不敢顾；",
          "chars": [
            { "char": "孤", "pinyin": "gū" },
            { "char": "鸿", "pinyin": "hóng" }
          ]
        }
      ]
    }
  ]
}
```

注意：data.json 中每个字单独标注拼音（而非整行拼音字符串），方便前端按字生成 `<ruby>` 标签。标点符号保留但不注音。

5. 复制 `src/index.html` 到 `dist/index.html`

## 前端页面设计

### 视觉风格

仿古籍竖排卷轴：宣纸色背景、深褐色文字、竖排从右到左、繁体/楷体风格字体。

### 布局（单页，CSS 原生，不引入框架）

```
┌──────────────────────────────────────────────┐
│  唐诗三百首 · 注音版                           │  ← 顶栏
├──────────┬───────────────────────────────────┤
│          │                                    │
│ 目录     │    ┌─────────────────────────┐     │
│          │    │ 卷01-五言古诗            │     │
│ 卷01     │    │                          │     │
│ 001 感遇 │    │   张九龄                  │     │
│ 002 感遇 │    │                          │     │
│ ...      │    │   gū  hóng  hǎi  shàng   │     │
│          │    │   孤   鸿   海   上      │     │
│ 卷03     │    │   lái ， chí  huáng      │     │
│ ...      │    │   来 ， 池   潢         │     │
│          │    │   bù   gǎn   gù  ；      │     │
│          │    │   不   敢   顾  ；        │     │
│          │    │         ↓                 │     │
│          │    │   竖排文字从上到下，       │     │
│          │    │   列从右到左排列           │     │
│          │    └─────────────────────────┘     │
│          │                                    │
│          │        ▲ 上一首  下一首 ▼           │
├──────────┴───────────────────────────────────┤
│  共310首 · 当前第1首                           │
└──────────────────────────────────────────────┘
```

竖排模式下，诗文区域使用 `writing-mode: vertical-rl`：
- 文字从上到下书写，每列从右到左排列
- `<ruby>` 注音自动显示在每个字的右侧
- 模拟古籍阅读体验：从右向左翻页

### 赫蹏类名组合

诗文展示区域使用以下赫蹏类名组合：

```
heti heti--ancient heti--vertical heti--annotation
```

- `heti` — 基础排版增强
- `heti--ancient` — 古文版式（标题/正文字体搭配）
- `heti--vertical` — 竖排（`writing-mode: vertical-rl`）
- `heti--annotation` — 行间注（配合 `<ruby>` 标签使用）

辅助类名：
- `heti-verse` — 诗句居中显示
- `heti-x-large` — 诗文大号字体
- `heti-hang` — 标点悬挂（不占版面）
- `heti-meta heti-small` — 作者/朝代等元信息

### 诗文 HTML 结构示例

```html
<div class="heti heti--ancient heti--vertical heti--annotation">
  <h2>感遇其一<span class="heti-meta heti-small">[唐]张九龄</span></h2>
  <p class="heti-verse heti-x-large">
    <ruby>孤<rp>(</rp><rt>gū</rt><rp>)</rp></ruby>
    <ruby>鸿<rp>(</rp><rt>hóng</rt><rp>)</rp></ruby>
    <ruby>海<rp>(</rp><rt>hǎi</rt><rp>)</rp></ruby>
    <ruby>上<rp>(</rp><rt>shàng</rt><rp>)</rp></ruby>
    <ruby>来<rp>(</rp><rt>lái</rt><rp>)</rp></ruby>
    <span class="heti-hang">，</span>
    <ruby>池<rp>(</rp><rt>chí</rt><rp>)</rp></ruby>
    ...
  </p>
</div>
```

### 功能

| 功能 | 说明 |
|------|------|
| 侧栏目录 | 按卷分组，点击跳转到对应诗 |
| 上一首/下一首 | 按钮切换，键盘上下箭头也支持 |
| 注音显示 | `<ruby>` 标签，竖排模式下拼音显示在汉字右侧（旁注） |
| 搜索 | 按标题/作者/诗句搜索 |
| 当前位置 | 底部显示 "第X首/共310首" |
| **设置面板** | 见下方详细设计 |

### 设置面板

顶栏右侧齿轮图标 ⚙ 打开侧滑设置面板，所有设置项实时生效，持久化到 `localStorage`。

#### 设置项明细

| 设置项 | 类型 | 默认值 | 范围/选项 | 说明 |
|--------|------|--------|-----------|------|
| **明暗主题** | 切换 | 深色 | 浅色 / 深色 / 跟随系统 | 深色模式：深色背景 + 浅色文字；自动模式跟随系统 `prefers-color-scheme` |
| **字体** | 下拉 | 宋体 | 宋体 / 楷体 / 黑体 / 仿宋 | 对应 `font-family`：`Noto Serif SC` / `ZCOOL XiaoWei` / `Noto Sans SC` / `FangSong` |
| **字号** | 滑块 | 22px | 14–36px | 诗文正文 `font-size` |
| **字距** | 滑块 | 4px | 0–12px | 诗文 `letter-spacing` |
| **行距** | 滑块 | 3.2 | 1.5–5.0 | 诗文 `<p>` 的 `line-height` |
| **拼音大小** | 滑块 | 0.42em | 0.2–0.8em | 拼音文字 `font-size` |
| **注音距离** | 滑块 | 2px | 0–16px | 拼音与汉字之间的间距，通过 CSS `margin` 控制 |
| **拼音位置** | 按钮组 | 右侧 | 上方 / 下方 / 左侧 / 右侧 | 拼音相对于汉字的四个方位。竖排时「右」为同行右侧（标准），「左」为同行左侧；「上」「下」为列内上下。横排时「上」为上方（标准），「下」为下方，「左」「右」为字旁 |
| **排版方向** | 切换 | 竖排 | 竖排 / 横排 | 切换 `writing-mode: vertical-rl` / `horizontal-tb` |

#### 设置持久化

```js
// 读取
const settings = JSON.parse(localStorage.getItem('poem-settings') || '{}');
// 写入
localStorage.setItem('poem-settings', JSON.stringify(settings));
```

#### 设置面板 UI 示意

```
┌─────────────────────────┐
│  ⚙ 排版设置        ✕    │
├─────────────────────────┤
│                         │
│  明暗主题  [浅] [深] [自]│
│                         │
│  字体    [▼ 宋体      ] │
│                         │
│  字号    ──●────── 22px │
│                         │
│  字距    ──●────── 4px  │
│                         │
│  行距    ────●─── 3.2   │
│                         │
│  拼音大小 ──●──── 0.42em│
│                         │
│  注音距离 ──●────── 2px │
│                         │
│  拼音位置  [上] [下]     │
│           [左] [●右]    │
│                         │
│  排版方向  [●竖排] [横排]│
│                         │
│  ─────────────────────  │
│  [恢复默认]             │
└─────────────────────────┘
```

#### 技术实现要点

- 设置面板为固定定位侧滑 `<div>`，从右侧滑入，z-index 高于内容区
- 每个设置项变化时调用 `applySettings()` 函数，直接修改 CSS 变量或对应元素的 style
- 主题切换：在 `<html>` 上切换 `data-theme` 属性，CSS 用 `[data-theme="dark"]` 选择器覆盖变量
- 排版方向切换：通过 `.poem-card[data-dir]` 属性切换 `writing-mode`
- 拼音位置：不使用 `<ruby>`，改用自定义 `span.pz` + CSS 绝对定位，支持上/下/左/右四个方位
- 注音距离：CSS 变量 `--pz-offset` 控制拼音与汉字的间距
- 拼音始终水平显示：通过 `writing-mode: horizontal-tb` 确保拼音文字在任何排版方向下都保持水平可读
- 标点占位：中文标点单独包裹为 `<span class="pz-punct">`，确保标点在竖排中有足够的视觉间距
- 实时生效：方向和位置设置通过 `data-dir` / `data-pos` 属性实时切换，无需重新渲染 HTML

## 实现步骤

1. **build.js** — 解析 markdown，生成结构化数据（逐字拼音），输出 `dist/data.json`
2. **src/index.html** — 编写页面结构和竖排样式，JS 加载 data.json 并渲染
3. **验证** — 运行 `node build.js`，用浏览器打开 `dist/index.html` 确认竖排和注音效果
4. **package.json** — 添加 `build` 和 `preview` 脚本命令

## 命令

```bash
npm install          # 安装依赖
npm run build        # 运行构建，生成 dist/
npm run preview      # 本地预览（用 npx serve dist）
```

## 补充需求

### 长诗滚动

长诗（如长恨歌 840 字、琵琶行 616 字）在竖排模式下生成大量列，向左延伸超出可视区域。部分诗还带有诗序（如琵琶行"元和十年…"），进一步增加篇幅。

**方案：卡片内滚动**

- `.poem-card` 设 `max-width`（竖排）和 `max-height`（横排），限制在视口范围内
- 卡片内部 `overflow: auto`，竖排时横向滚动查看更多列，横排时纵向滚动
- 短诗不受影响，卡片按内容尺寸居中显示

### 标题和作者注音

标题和作者名不注音，保持纯文字显示。只有诗文正文逐字注音。
