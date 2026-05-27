# 开发规划 — 唐诗三百首注音网页版（古籍竖排）

> 配套可视化：`docs/dev-plan-visual.html`

## 整体架构

```mermaid
graph LR
    subgraph 构建阶段["构建阶段 (build.js)"]
        MD["唐诗三百首.md"] --> Parser["Markdown 解析器"]
        Parser --> Struct["结构化数据<br/>(卷/诗/作者/正文)"]
        Struct --> Pinyin["pinyin-pro<br/>逐字注音"]
        Pinyin --> JSON["data.json"]
    end

    subgraph 运行阶段["运行阶段 (浏览器)"]
        HTML["index.html"] -->|加载| JSON
        JSON --> Renderer["JS 渲染器"]
        Renderer --> HETI["赫蹏排版"]
        HETI --> PAGE["竖排注音页面"]
    end

    style MD fill:#3a2a1a,stroke:#d4a76a,color:#eee
    style Parser fill:#2a2a3a,stroke:#888,color:#eee
    style Struct fill:#2a2a3a,stroke:#888,color:#eee
    style Pinyin fill:#2a2a3a,stroke:#888,color:#eee
    style JSON fill:#1a2a3a,stroke:#90caf9,color:#eee
    style HTML fill:#3a2a1a,stroke:#d4a76a,color:#eee
    style Renderer fill:#2a2a3a,stroke:#888,color:#eee
    style HETI fill:#2a2a3a,stroke:#888,color:#eee
    style PAGE fill:#1a2a1a,stroke:#a5d6a7,color:#eee
```

## 里程碑与任务拆解

### 阶段一：数据管线（build.js）

目标：把 markdown 源文件转换为带拼音的结构化 JSON。

```mermaid
flowchart TD
    A["读取唐诗三百首.md"] --> B["逐行扫描"]
    B --> C{"当前行类型?"}

    C -->|## 开头| D["记录卷信息<br/>volume = { id, name }"]
    C -->|### 开头| E["记录诗标题<br/>poem = { number, title }"]
    C -->|> 开头| F["记录作者<br/>poem.author = ..."]
    C -->|空行| G["跳过"]
    C -->|其他| H["追加为诗文行<br/>poem.lines.push(...)"]

    D --> B
    E --> B
    F --> B
    G --> B
    H --> B

    H --> I["所有诗解析完成"]
    I --> J["遍历每个诗的每行"]
    J --> K["逐字判断：汉字?"]
    K -->|是| L["pinyin(char) 获取拼音"]
    K -->|否| M["保留原字符，不注音"]
    L --> N["组装 chars 数组"]
    M --> N
    N --> J

    J --> O["输出 dist/data.json"]
    O --> P["复制 src/index.html → dist/"]

    style A fill:#3a2a1a,stroke:#d4a76a,color:#eee
    style B fill:#2a2a3a,stroke:#888,color:#eee
    style C fill:#2a2a3a,stroke:#888,color:#eee
    style D fill:#2a2a3a,stroke:#888,color:#eee
    style E fill:#2a2a3a,stroke:#888,color:#eee
    style F fill:#2a2a3a,stroke:#888,color:#eee
    style G fill:#2a2a2a,stroke:#888,color:#eee
    style H fill:#2a2a3a,stroke:#888,color:#eee
    style I fill:#2a2a3a,stroke:#888,color:#eee
    style J fill:#2a2a3a,stroke:#888,color:#eee
    style K fill:#2a2a3a,stroke:#888,color:#eee
    style L fill:#2a2a3a,stroke:#888,color:#eee
    style M fill:#2a2a3a,stroke:#888,color:#eee
    style N fill:#2a2a3a,stroke:#888,color:#eee
    style O fill:#1a2a3a,stroke:#90caf9,color:#eee
    style P fill:#1a2a1a,stroke:#a5d6a7,color:#eee
```

| # | 任务 | 产出 | 依赖 |
|---|------|------|------|
| 1.1 | 编写 markdown 行解析器，识别 `##`/`###`/`>`/空行/正文 | `parseMarkdown()` 函数 | 无 |
| 1.2 | 编写逐字注音模块，用 pinyin-pro 给汉字注音，标点保留 | `annotateChars()` 函数 | 1.1 |
| 1.3 | 组装 JSON 结构（volumes + poems），写入 `dist/data.json` | `build.js` 主流程 | 1.1, 1.2 |
| 1.4 | 复制 `src/index.html` 到 `dist/index.html`，添加 npm scripts | `package.json` 更新 | 1.3 |
| 1.5 | 端到端验证：运行 `node build.js`，检查输出 JSON 结构和内容 | 验证通过 | 1.4 |

### 阶段二：页面骨架（index.html）

目标：搭出侧栏 + 内容区的布局骨架，能加载 JSON 并渲染第一首诗。

```mermaid
graph TD
    subgraph 页面结构
        HEADER["顶栏：唐诗三百首 · 注音版"]
        SIDEBAR["侧栏目录<br/>按卷分组"]
        CONTENT["内容区<br/>诗文展示"]
        FOOTER["底栏：第X首/共310首"]
        SETTINGS["⚙ 设置面板<br/>排版/主题/拼音"]
    end

    HEADER --> SIDEBAR
    HEADER --> CONTENT
    HEADER --> SETTINGS
    CONTENT --> FOOTER

    subgraph 侧栏数据流
        S1["data.json → volumes"] --> S2["渲染卷标题"]
        S1 --> S3["渲染诗列表<br/>(编号 + 标题)"]
        S3 --> S4["点击 → 切换当前诗"]
    end

    subgraph 内容区数据流
        C1["data.json → poems[id]"] --> C2["生成 &lt;ruby&gt; HTML"]
        C2 --> C3["套用赫蹏类名<br/>heti--ancient<br/>heti--vertical<br/>heti--annotation"]
    end

    subgraph 设置数据流
        ST1["localStorage"] --> ST2["读取设置"]
        ST2 --> ST3["applySettings()"]
        ST3 --> ST4["修改 CSS 变量<br/>切换 class"]
    end

    style HEADER fill:#3a2a1a,stroke:#d4a76a,color:#eee
    style SIDEBAR fill:#3a2a1a,stroke:#d4a76a,color:#eee
    style CONTENT fill:#1a2a1a,stroke:#a5d6a7,color:#eee
    style FOOTER fill:#3a2a1a,stroke:#d4a76a,color:#eee
    style SETTINGS fill:#1a2a3a,stroke:#90caf9,color:#eee
    style S1 fill:#1a2a3a,stroke:#90caf9,color:#eee
    style S2 fill:#2a2a3a,stroke:#888,color:#eee
    style S3 fill:#2a2a3a,stroke:#888,color:#eee
    style S4 fill:#2a2a3a,stroke:#888,color:#eee
    style C1 fill:#1a2a3a,stroke:#90caf9,color:#eee
    style C2 fill:#2a2a3a,stroke:#888,color:#eee
    style C3 fill:#2a2a3a,stroke:#888,color:#eee
    style ST1 fill:#3a2a1a,stroke:#d4a76a,color:#eee
    style ST2 fill:#2a2a3a,stroke:#888,color:#eee
    style ST3 fill:#2a2a3a,stroke:#888,color:#eee
    style ST4 fill:#2a2a3a,stroke:#888,color:#eee
```

| # | 任务 | 产出 | 依赖 |
|---|------|------|------|
| 2.1 | 编写 HTML 骨架：顶栏 + 侧栏 + 内容区 + 底栏 | `src/index.html` 结构 | 无 |
| 2.2 | 引入 heti CSS/JS，编写自定义样式（宣纸背景、墨色文字） | `<style>` 部分 | 2.1 |
| 2.3 | 编写 `loadData()` — fetch data.json，存为全局状态 | JS 数据加载 | 2.1 |
| 2.4 | 编写 `renderSidebar()` — 按卷分组渲染诗列表，点击切换 | 侧栏交互 | 2.3 |
| 2.5 | 编写 `renderPoem()` — 根据诗数据生成 ruby HTML + 赫蹏类名 | 诗文渲染 | 2.3 |
| 2.6 | 端到端验证：浏览器打开，确认第一首诗竖排注音显示正常 | 验证通过 | 2.4, 2.5 |

### 阶段三：导航与交互

目标：完成前后切换、键盘控制、搜索等交互功能。

```mermaid
stateDiagram-v2
    [*] --> 显示当前诗
    显示当前诗 --> 更新内容区: 上一首 / 下一首
    显示当前诗 --> 更新内容区: 侧栏点击
    显示当前诗 --> 搜索结果: 输入搜索词
    更新内容区 --> 显示当前诗: 渲染完成
    搜索结果 --> 显示当前诗: 点击结果项
    搜索结果 --> 显示当前诗: 清空搜索

    state 显示当前诗 {
        渲染诗文 --> 更新侧栏高亮
        更新侧栏高亮 --> 更新底栏计数
        更新底栏计数 --> 更新URL哈希
    }
```

| # | 任务 | 产出 | 依赖 |
|---|------|------|------|
| 3.1 | 上一首/下一首按钮 + 键盘左右箭头控制 | 导航按钮 | 阶段二 |
| 3.2 | 侧栏当前诗高亮，自动滚动到可见 | 侧栏联动 | 阶段二 |
| 3.3 | 底栏 "第X首/共310首" 更新 | 底栏状态 | 阶段二 |
| 3.4 | URL hash 路由（`#poem-001`），支持分享和前进后退 | hash 路由 | 3.1 |
| 3.5 | 搜索框：按标题/作者/诗句过滤，显示匹配列表 | 搜索功能 | 3.4 |
| 3.6 | 响应式适配：移动端侧栏折叠为汉堡菜单 | 移动端适配 | 3.5 |

### 阶段四：打磨与发布

| # | 任务 | 产出 | 依赖 |
|---|------|------|------|
| 4.1 | 验证全部 310 首诗渲染无报错（批量检查 data.json 完整性） | 数据完整性验证 | 阶段三 |
| 4.2 | 浏览器兼容测试（Chrome / Firefox / Safari / 移动端） | 兼容性报告 | 4.1 |
| 4.3 | 性能优化：data.json gzip 后体积检查，按需加载评估 | 性能基线 | 4.1 |
| 4.4 | 部署到 GitHub Pages | 线上可访问 | 4.2 |

### 阶段五：设置面板

目标：用户可自定义排版参数（主题、字体、字距、行距、拼音大小/位置、排版方向），设置持久化到 localStorage。

```mermaid
flowchart LR
    OPEN["点击 ⚙"] --> PANEL["设置面板滑入"]
    PANEL --> CHANGE["修改设置项"]
    CHANGE --> APPLY["applySettings()"]
    APPLY --> CSS["修改 CSS 变量<br/>/ 切换 class"]
    APPLY --> LS["写入 localStorage"]
    CSS --> RENDER["页面实时更新"]

    LS --> RELOAD["下次加载时<br/>读取并恢复"]

    style OPEN fill:#3a2a1a,stroke:#d4a76a,color:#eee
    style PANEL fill:#2a2a3a,stroke:#888,color:#eee
    style CHANGE fill:#2a2a3a,stroke:#888,color:#eee
    style APPLY fill:#1a2a3a,stroke:#90caf9,color:#eee
    style CSS fill:#2a2a3a,stroke:#888,color:#eee
    style LS fill:#3a2a1a,stroke:#d4a76a,color:#eee
    style RENDER fill:#1a2a1a,stroke:#a5d6a7,color:#eee
    style RELOAD fill:#3a2a1a,stroke:#d4a76a,color:#eee
```

| # | 任务 | 产出 | 依赖 |
|---|------|------|------|
| 5.1 | 设置面板 HTML/CSS：侧滑面板 + 表单控件 | 设置面板 UI | 阶段四 |
| 5.2 | 明暗主题切换：CSS 变量覆盖 + `data-theme` 属性 | 主题系统 | 5.1 |
| 5.3 | 排版参数控件：字体、字号、字距、行距、拼音大小滑块 | 排版参数控制 | 5.1 |
| 5.4 | 拼音位置切换（左/右）+ 排版方向切换（竖/横） | 方向控制 | 5.3 |
| 5.5 | localStorage 持久化 + 页面加载时恢复设置 | 设置持久化 | 5.4 |
| 5.6 | 恢复默认按钮 + 验证所有设置项联动正常 | 完整性验证 | 5.5 |

## 任务依赖关系

```mermaid
gantt
    title 开发时间线
    dateFormat YYYY-MM-DD
    axisFormat %m/%d

    section 阶段一 数据管线
    1.1 Markdown解析器       :a1, 2026-05-27, 1d
    1.2 逐字注音模块         :a2, after a1, 1d
    1.3 组装JSON输出         :a3, after a2, 1d
    1.4 package.json配置     :a4, after a3, 1d
    1.5 端到端验证           :a5, after a4, 1d

    section 阶段二 页面骨架
    2.1 HTML骨架             :b1, after a5, 1d
    2.2 引入heti+自定义样式  :b2, after b1, 1d
    2.3 数据加载             :b3, after b1, 1d
    2.4 侧栏渲染             :b4, after b3, 1d
    2.5 诗文渲染             :b5, after b3, 1d
    2.6 端到端验证           :b6, after b5, 1d

    section 阶段三 导航交互
    3.1 前后切换             :c1, after b6, 1d
    3.2 侧栏联动             :c2, after b6, 1d
    3.3 底栏状态             :c3, after b6, 1d
    3.4 URL路由              :c4, after c1, 1d
    3.5 搜索功能             :c5, after c4, 1d
    3.6 移动端适配           :c6, after c5, 1d

    section 阶段四 打磨发布
    4.1 数据完整性验证        :d1, after c6, 1d
    4.2 浏览器兼容测试        :d2, after d1, 1d
    4.3 性能优化             :d3, after d1, 1d
    4.4 部署GitHub Pages     :d4, after d2, 1d

    section 阶段五 设置面板
    5.1 设置面板UI           :e1, after d4, 1d
    5.2 明暗主题             :e2, after e1, 1d
    5.3 排版参数控件         :e3, after e1, 1d
    5.4 拼音位置+排版方向    :e4, after e3, 1d
    5.5 localStorage持久化   :e5, after e4, 1d
    5.6 验证+恢复默认        :e6, after e5, 1d
```

## 文件变更清单

```mermaid
graph TB
    subgraph 新增文件
        BUILD["build.js<br/>构建脚本"]
        INDEX["src/index.html<br/>页面模板"]
        DIST_JSON["dist/data.json<br/>注音数据"]
        DIST_HTML["dist/index.html<br/>构建产物"]
        PLAN["docs/dev-plan.md<br/>本文件"]
        VIS["docs/dev-plan-visual.html<br/>可视化辅助"]
    end

    subgraph 修改文件
        PKG["package.json<br/>+scripts +dependencies"]
        GIT[".gitignore<br/>+dist/"]
        CLAUDE["CLAUDE.md<br/>更新开发命令"]
    end

    subgraph 不变文件
        SRC_MD["docs/唐诗三百首.md"]
        OLD["add-pinyin.js"]
    end

    BUILD --> DIST_JSON
    BUILD --> DIST_HTML
    INDEX -->|"被复制"| DIST_HTML

    style BUILD fill:#1a2a3a,stroke:#90caf9,color:#eee
    style INDEX fill:#1a2a3a,stroke:#90caf9,color:#eee
    style DIST_JSON fill:#1a2a1a,stroke:#a5d6a7,color:#eee
    style DIST_HTML fill:#1a2a1a,stroke:#a5d6a7,color:#eee
    style PLAN fill:#1a2a3a,stroke:#90caf9,color:#eee
    style VIS fill:#1a2a3a,stroke:#90caf9,color:#eee
    style PKG fill:#3a2a1a,stroke:#d4a76a,color:#eee
    style GIT fill:#3a2a1a,stroke:#d4a76a,color:#eee
    style CLAUDE fill:#3a2a1a,stroke:#d4a76a,color:#eee
    style SRC_MD fill:#2a2a2a,stroke:#888,color:#eee
    style OLD fill:#2a2a2a,stroke:#888,color:#eee
```

## 关键技术决策

| 决策 | 选择 | 理由 |
|------|------|------|
| 排版库 | 赫蹏 (heti) | 内置古文/竖排/行间注/诗词版式，MIT 协议 |
| 拼音生成 | pinyin-pro（Node.js 后端） | 已有依赖，API 简单，支持声调 |
| 前端框架 | 无（原生 JS） | 项目规模小，无需引入框架 |
| 数据传递 | 构建 JSON，运行时 fetch | 分离构建和渲染，页面可离线使用 |
| 路由 | URL hash（`#poem-001`） | 无需服务器配置，GitHub Pages 直接支持 |
| 部署 | GitHub Pages | 免费，直接从 dist/ 目录发布 |
