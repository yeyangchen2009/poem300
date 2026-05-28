# 中华经典文库 — 产品扩展方案

> 基于 Kimi 对话整理，从「唐诗三百首注音版」扩展到「经史子集全品类」的产品规划，以及面向「亲子共读」场景的平台策略。

## 一、现有架构评价

| 环节 | 技术 | 评价 |
|------|------|------|
| 拼音生成 | `pinyin-pro` + Node.js | 稳定可靠，适合批量处理 |
| 竖排排版 | 赫蹏 heti | 专门的中文竖排方案 |
| 前端 | 原生 HTML/CSS/JS | 零依赖，加载快 |
| 数据 | Markdown → JSON 构建管线 | 作者友好，易维护 |
| 部署 | GitHub Pages 静态站 | 免费，CDN 全球加速 |

## 二、扩展到四库全品类的方案选型

### 三种技术路线

```mermaid
flowchart TD
    Now["poem300 现有架构"] --> Choice{"扩展方向"}

    Choice -->|"A：继承现有架构<br/>渐进扩展"| A["升级构建管线<br/>多音字校正 + 四库分类"]
    Choice -->|"B：docsify/VitePress<br/>文档站"| B["侧重文档站体验<br/>目录导航 + 搜索 + 插件"]
    Choice -->|"C：Vue 3 + Vite<br/>现代框架"| C["完全可控<br/>支持未来用户系统"]

    A --> A1["古籍阅读质感最强"]
    B --> B1["上手最快，生态丰富"]
    C --> C1["适合团队开发，长期迭代"]

    style Now fill:#3a2a1a,stroke:#d4a76a,color:#eee
    style Choice fill:#2a2a3a,stroke:#888,color:#eee
    style A fill:#1a2a1a,stroke:#a5d6a7,color:#eee
    style B fill:#1a2a3a,stroke:#90caf9,color:#eee
    style C fill:#1a2a3a,stroke:#90caf9,color:#eee
    style A1 fill:#1a2a1a,stroke:#a5d6a7,color:#eee
    style B1 fill:#1a2a3a,stroke:#90caf9,color:#eee
    style C1 fill:#1a2a3a,stroke:#90caf9,color:#eee
```

### 方案对比

| 维度 | A：继承 poem300 | B：docsify/VitePress | C：Vue 3 + Vite |
|------|----------------|---------------------|-----------------|
| 竖排控制 | 精细（heti 专门优化） | 需额外 CSS 调优 | 完全自由 |
| 拼音位置 | 四方位可调 | 默认上方，需自定义 | 完全自由 |
| 古籍质感 | 最强 | 偏文档风格 | 完全可控 |
| 维护成本 | 中 | 低（自带很多功能） | 高 |
| 扩展性 | 高（完全可控） | 中（受限于框架架构） | 最高 |
| 适合场景 | 个人维护、追求质感 | 快速搭建 | 团队开发、长期迭代 |

### 推荐策略

```mermaid
flowchart LR
    Q{"你的情况?"} --> A["个人维护<br/>追求古籍阅读质感"]
    Q --> B["快速搭建<br/>文档站风格可接受"]
    Q --> C["有前端团队<br/>未来加社交/笔记"]

    A --> RA["方案 A<br/>继承 poem300"]
    B --> RB["方案 B<br/>docsify/VitePress"]
    C --> RC["方案 C<br/>Vue 3 + Vite"]

    style Q fill:#3a2a1a,stroke:#d4a76a,color:#eee
    style RA fill:#1a2a1a,stroke:#a5d6a7,color:#eee
    style RB fill:#1a2a3a,stroke:#90caf9,color:#eee
    style RC fill:#1a2a3a,stroke:#90caf9,color:#eee
```

## 三、多音字问题

这是古诗文注音最大的坑。`pinyin-pro` 对古汉语多音字（如「说(yuè)乎」「乐(lè/yào)」）会标错。

**解决方案**：建立 `corrections.json` 人工校正表，构建时先自动注音再覆盖。

```json
{
  "论语": {
    "学而时习之不亦说乎": { "说": "yuè" },
    "有朋自远方来不亦乐乎": { "乐": "lè" }
  }
}
```

## 四、文档站方案补充对比

除 docsify 外，还有几个适合竖排+拼音的方案：

| 方案 | 上手难度 | 竖排控制 | 构建速度 | 适合人群 |
|------|---------|---------|---------|---------|
| **docsify** | 最简单 | 需 CSS | 无构建 | 快速验证 |
| **VitePress** | 简单 | 完全可控 | 很快 | Vue 用户 |
| **MkDocs** | 简单 | 需 CSS | 快 | Python 用户 |
| **Docusaurus** | 中等 | 完全可控 | 中等 | React 用户 |
| **Astro** | 中等 | 完全可控 | 最快 | 追求性能 |

**VitePress 不推荐的原因**：它是为技术文档设计的，竖排古籍的 `writing-mode: vertical-rl` + 拼音四方位定位 + 阅读设置持久化需要大量 hack，不如原生方案自如。

## 五、面向亲子共读的产品设计

### 核心场景

```mermaid
graph TD
    Parent["家长（30-45岁）<br/>想陪孩子学古文<br/>但自己功底一般"] --> Together["亲子共读"]
    Child["小朋友（6-12岁）<br/>识字量有限<br/>需要拼音、朗读"] --> Together

    Together --> P1["竖排 + 拼音<br/>帮助识字"]
    Together --> P2["音频朗读<br/>跟着一起读"]
    Together --> P3["B站视频<br/>看动画学古诗"]
    Together --> P4["每日推荐<br/>降低选择成本"]

    style Parent fill:#3a2a1a,stroke:#d4a76a,color:#eee
    style Child fill:#3a2a1a,stroke:#d4a76a,color:#eee
    style Together fill:#1a2a3a,stroke:#90caf9,color:#eee
    style P1 fill:#1a2a1a,stroke:#a5d6a7,color:#eee
    style P2 fill:#1a2a1a,stroke:#a5d6a7,color:#eee
    style P3 fill:#1a2a1a,stroke:#a5d6a7,color:#eee
    style P4 fill:#1a2a1a,stroke:#a5d6a7,color:#eee
```

### 音频/视频格式支持

| 格式 | 支持方式 | 网页可行性 |
|------|---------|-----------|
| MP3 音频 | HTML5 `<audio>` 标签 | 完美支持 |
| B站视频 | iframe 嵌入播放器 | 完美支持 |
| MP4 视频 | HTML5 `<video>` 标签 | 完美支持 |
| 逐句跟读 | Web Audio API + 字幕同步 | 可实现 |

**网页版的限制**：音频不能后台锁屏播放、不能缓存到本地、没有播放进度记忆。

## 六、平台选型：网页 vs 小程序 vs App

### 分阶段策略

```mermaid
flowchart TD
    S1["阶段一：网页 MVP<br/>验证需求"] -->|"日活达标<br/>用户反馈"| S2["阶段二：微信小程序<br/>裂变 + 留存"]
    S2 -->|"日活 >5000<br/>需要深度功能"| S3["阶段三：App<br/>深度用户"]

    S1 --> F1["竖排+拼音+B站视频嵌入<br/>音频播放+收藏<br/>1-2周上线，¥0"]
    S2 --> F2["跟读录音+AI打分<br/>后台播放+离线缓存<br/>家长推送学习报告"]
    S3 --> F3["逐字高亮同步<br/>AI语音评测<br/>AR书法临摹"]

    style S1 fill:#1a2a1a,stroke:#a5d6a7,color:#eee
    style S2 fill:#1a2a3a,stroke:#90caf9,color:#eee
    style S3 fill:#3a2a1a,stroke:#d4a76a,color:#eee
    style F1 fill:#2a2a3a,stroke:#888,color:#eee
    style F2 fill:#2a2a3a,stroke:#888,color:#eee
    style F3 fill:#2a2a3a,stroke:#888,color:#eee
```

### 平台能力对比

| 维度 | 网页 H5 | 微信小程序 | App |
|------|---------|-----------|-----|
| 开发成本 | 最低 | 中 | 最高 |
| 音频后台播放 | 浏览器限制 | 原生支持 | 完美 |
| 音频离线缓存 | 有限 | 支持 | 完美 |
| 跟读打分 | Web Audio 精度差 | 录音 API 好 | 最佳 |
| 家长分享传播 | 复制链接 | 微信一键分享 | 需下载 |
| 小朋友使用门槛 | 低 | 低 | 高 |
| 支付/会员 | 麻烦 | 微信支付 | 内购 |

### 小程序特有的亲子功能

```
小朋友端：
  打开 → "今日任务：背《春晓》"（家长预设或系统推荐）
  听朗读 → 跟读录音 → AI打分（流畅度/准确度）
  完成打卡 → 获得积分/勋章

家长端：
  微信推送："小明今天完成了《春晓》跟读，得分85分"
  查看周报：本周背了5首，总时长30分钟
  设置学习计划：每天一首，周末复习
```

## 七、从内容站到阅读产品的演进

```mermaid
flowchart LR
    subgraph Phase1["阶段一：内容站"]
        C1["竖排+拼音展示"]
        C2["四库分类导航"]
        C3["基础搜索"]
        C4["分享链接"]
    end

    subgraph Phase2["阶段二：轻账户"]
        U1["微信登录"]
        U2["阅读进度同步"]
        U3["书签+书架"]
        U4["收藏夹"]
    end

    subgraph Phase3["阶段三：社区化"]
        S1["划线批注"]
        S2["历代评点集成"]
        S3["读书圈子"]
        S4["背诵打卡"]
    end

    Phase1 -->|"验证用户<br/>愿意来"| Phase2
    Phase2 -->|"验证留存<br/>用户反复来"| Phase3

    style Phase1 fill:#1a2a1a,stroke:#a5d6a7,color:#eee
    style Phase2 fill:#1a2a3a,stroke:#90caf9,color:#eee
    style Phase3 fill:#3a2a1a,stroke:#d4a76a,color:#eee
```

### 各阶段技术栈

| 阶段 | 架构 | 成本 |
|------|------|------|
| 一 | GitHub Pages 静态站 | ¥0 |
| 二 | Vercel/Cloudflare + Supabase | ¥0-50/月 |
| 三 | Vercel + Supabase + Redis + 对象存储 | ¥100-300/月 |

## 八、关键决策建议

| 问题 | 建议 |
|------|------|
| 先做网页还是小程序？ | **网页 MVP 验证 → 小程序做留存** |
| 音频存在哪？ | 阶段一：CDN/对象存储；阶段二：小程序云存储 |
| B站视频还是自制音频？ | 初期用 B站现成资源，零成本测试 |
| AI 朗读还是真人朗读？ | 先用 AI（成本低），数据好再请专业录制 |
| 收费模式？ | 免费基础内容 + 会员解锁全部音频/跟读功能 |
| 古籍特色功能？ | 背诵打卡、书法临摹、历代评点多层嵌套 |
