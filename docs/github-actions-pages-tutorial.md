# GitHub Actions 与 gh CLI Pages 部署教程

> 本文档介绍两种将项目部署到 GitHub Pages 的方式：GitHub Actions 自动化部署 和 gh CLI 手动部署，以及它们的原理、操作步骤和适用场景。

## 整体架构对比

```mermaid
flowchart LR
    subgraph CI["GitHub Actions（自动）"]
        Push1["git push"] --> Trigger1["触发 workflow"]
        Trigger1 --> Cloud1["云端构建"]
        Cloud1 --> Deploy1["自动部署"]
    end

    subgraph CLI["gh CLI（手动）"]
        Local2["本地构建"] --> API2["gh api 调用"]
        API2 --> Remote2["远程创建分支"]
        Remote2 --> Pages2["Pages 服务"]
    end

    style CI fill:#1a2a1a,stroke:#a5d6a7,color:#eee
    style CLI fill:#1a2a3a,stroke:#90caf9,color:#eee
    style Push1 fill:#2a2a3a,stroke:#888,color:#eee
    style Trigger1 fill:#2a2a3a,stroke:#888,color:#eee
    style Cloud1 fill:#2a2a3a,stroke:#888,color:#eee
    style Deploy1 fill:#1a2a1a,stroke:#a5d6a7,color:#eee
    style Local2 fill:#2a2a3a,stroke:#888,color:#eee
    style API2 fill:#2a2a3a,stroke:#888,color:#eee
    style Remote2 fill:#2a2a3a,stroke:#888,color:#eee
    style Pages2 fill:#1a2a3a,stroke:#90caf9,color:#eee
```

## 一、GitHub Actions 原理

### 什么是 GitHub Actions

GitHub Actions 是 GitHub 内置的 CI/CD（持续集成/持续部署）服务。它在 GitHub 的云服务器上自动运行你定义的工作流，不需要本地参与。

### 工作原理

```mermaid
sequenceDiagram
    participant Dev as 开发者
    participant Repo as GitHub 仓库
    participant Runner as Actions Runner
    participant Pages as GitHub Pages

    Dev->>Repo: git push
    Repo->>Runner: 触发 workflow（.github/workflows/deploy.yml）
    Runner->>Runner: checkout 代码
    Runner->>Runner: npm ci（安装依赖）
    Runner->>Runner: npm run build（构建）
    Runner->>Pages: 上传 dist/ 并部署
    Pages-->>Dev: 站点上线
```

### 核心概念

```mermaid
graph TD
    Actions["GitHub Actions"] --> Workflow["Workflow<br/>工作流"]
    Workflow --> Trigger["Trigger 触发条件"]
    Workflow --> Job["Job 任务"]
    Job --> Step["Step 步骤"]
    Step --> Action["Action<br/>可复用操作"]

    Trigger --> T1["push 推送时"]
    Trigger --> T2["schedule 定时"]
    Trigger --> T3["workflow_dispatch 手动"]

    style Actions fill:#3a2a1a,stroke:#d4a76a,color:#eee
    style Workflow fill:#1a2a3a,stroke:#90caf9,color:#eee
    style Trigger fill:#2a2a3a,stroke:#888,color:#eee
    style Job fill:#2a2a3a,stroke:#888,color:#eee
    style Step fill:#2a2a3a,stroke:#888,color:#eee
    style Action fill:#2a2a3a,stroke:#888,color:#eee
    style T1 fill:#1a2a1a,stroke:#a5d6a7,color:#eee
    style T2 fill:#1a2a1a,stroke:#a5d6a7,color:#eee
    style T3 fill:#1a2a1a,stroke:#a5d6a7,color:#eee
```

| 概念 | 说明 | 类比 |
|------|------|------|
| **Workflow** | 一个完整的自动化流程，写在 YAML 文件中 | 一份菜谱 |
| **Trigger** | 什么时候触发（push、定时、手动） | 开火信号 |
| **Job** | 一组步骤的集合，在一个虚拟机上运行 | 厨房 |
| **Step** | 具体的操作命令或调用 Action | 一个烹饪步骤 |
| **Action** | 可复用的操作单元（如 `actions/checkout@v4`） | 预制调料包 |

### Workflow 文件结构

```
.github/
└── workflows/
    └── deploy.yml    ← GitHub 自动识别这个目录下的 YAML 文件
```

```yaml
name: Deploy to GitHub Pages       # 工作流名称

on:                                 # 触发条件
  push:
    branches: [master]              # master 分支有推送时触发
  workflow_dispatch:                 # 也支持手动触发

permissions:                        # 权限声明
  contents: read                    # 读取代码
  pages: write                      # 写入 Pages
  id-token: write                   # OIDC 身份验证

jobs:
  build-and-deploy:                 # 任务名称
    runs-on: ubuntu-latest          # 运行环境
    steps:                          # 步骤列表
      - uses: actions/checkout@v4   # 拉取代码
      - uses: actions/setup-node@v4 # 安装 Node.js
      - run: npm ci                 # 安装依赖
      - run: npm run build          # 构建
      - uses: actions/deploy-pages@v4  # 部署到 Pages
```

### 常用 gh CLI 命令（Actions 相关）

```bash
# 查看所有 workflow 运行记录
gh run list

# 查看某次运行的详情
gh run view <run-id>

# 查看失败的日志
gh run view <run-id> --log-failed

# 实时观看运行状态
gh run watch <run-id>

# 手动触发 workflow
gh workflow run deploy.yml

# 查看 workflow 列表
gh workflow list
```

---

## 二、gh CLI 操作 GitHub Pages

### 什么是 gh CLI

`gh` 是 GitHub 官方命令行工具，可以直接在终端操作 GitHub 的各种功能（Issue、PR、Pages、Actions 等），不需要打开浏览器。

### Pages 部署方式

通过 gh CLI 部署 Pages 有两种方式：

```mermaid
flowchart TD
    CLI["gh CLI"] --> A{"选择部署方式"}
    A -->|"方式一"| B["API 创建 gh-pages 分支<br/>（远程操作，不动本地）"]
    A -->|"方式二"| C["配置 Pages 源为 Actions<br/>然后推送 workflow 文件"]

    B --> D["gh api 创建远程分支"]
    D --> E["gh api 配置 Pages 指向该分支"]
    E --> F["站点上线"]

    C --> G["推送 .github/workflows/deploy.yml"]
    G --> H["Actions 自动构建部署"]
    H --> F

    style CLI fill:#3a2a1a,stroke:#d4a76a,color:#eee
    style A fill:#2a2a3a,stroke:#888,color:#eee
    style B fill:#1a2a3a,stroke:#90caf9,color:#eee
    style C fill:#1a2a1a,stroke:#a5d6a7,color:#eee
    style D fill:#2a2a3a,stroke:#888,color:#eee
    style E fill:#2a2a3a,stroke:#888,color:#eee
    style F fill:#1a2a1a,stroke:#a5d6a7,color:#eee
    style G fill:#2a2a3a,stroke:#888,color:#eee
    style H fill:#2a2a3a,stroke:#888,color:#eee
```

### 常用 gh CLI 命令（Pages 相关）

```bash
# 查看 Pages 状态
gh api repos/<owner>/<repo>/pages

# 启用 Pages（源为 Actions workflow）
gh api repos/<owner>/<repo>/pages --method POST \
  -f build_type=workflow \
  -f source[branch]=master \
  -f source[path]=/

# 启用 Pages（源为 gh-pages 分支的根目录）
gh api repos/<owner>/<repo>/pages --method POST \
  -f build_type=legacy \
  -f source[branch]=gh-pages \
  -f source[path]=/

# 查看 Pages 部署历史
gh api repos/<owner>/<repo>/pages/deployments

# 删除 Pages 站点
gh api repos/<owner>/<repo>/pages --method DELETE
```

---

## 三、两种方式对比

```mermaid
graph LR
    subgraph 相同点
        S1["都部署到 GitHub Pages"]
        S2["都通过 gh CLI 管理"]
        S3["都支持自定义域名"]
    end

    subgraph Actions["GitHub Actions（自动）"]
        A1["push 触发自动构建"]
        A2["云端构建，本地不动"]
        A3["需要 workflow YAML 文件"]
        A4["适合持续部署"]
    end

    subgraph Legacy["gh-pages 分支（手动）"]
        L1["手动构建和推送"]
        L2["需要维护独立分支"]
        L3["简单项目更直接"]
        L4["适合一次性部署"]
    end

    style S1 fill:#2a2a2a,stroke:#888,color:#eee
    style S2 fill:#2a2a2a,stroke:#888,color:#eee
    style S3 fill:#2a2a2a,stroke:#888,color:#eee
    style A1 fill:#1a2a1a,stroke:#a5d6a7,color:#eee
    style A2 fill:#1a2a1a,stroke:#a5d6a7,color:#eee
    style A3 fill:#1a2a1a,stroke:#a5d6a7,color:#eee
    style A4 fill:#1a2a1a,stroke:#a5d6a7,color:#eee
    style L1 fill:#1a2a3a,stroke:#90caf9,color:#eee
    style L2 fill:#1a2a3a,stroke:#90caf9,color:#eee
    style L3 fill:#1a2a3a,stroke:#90caf9,color:#eee
    style L4 fill:#1a2a3a,stroke:#90caf9,color:#eee
```

| 对比维度 | GitHub Actions | gh-pages 分支 |
|----------|---------------|---------------|
| **构建位置** | GitHub 云端 | 本地 |
| **本地文件影响** | 零影响 | 可能需要切分支操作 |
| **触发方式** | push 自动触发 | 手动推送 |
| **配置复杂度** | 需要写 YAML | 简单直接 |
| **依赖管理** | 需要 `package-lock.json` | 不需要 |
| **构建一致性** | 云端环境一致 | 取决于本地环境 |
| **回滚** | 可通过 `gh run` 重新部署 | 需要回退分支 commit |
| **适用场景** | 团队协作、持续部署 | 个人项目、快速原型 |

### 如何选择

```mermaid
flowchart TD
    Q{"你的项目需要?"}
    Q -->|"多人协作"| A["用 Actions"]
    Q -->|"每次 push 自动更新"| A
    Q -->|"需要构建步骤<br/>（npm run build）"| A
    Q -->|"纯静态文件<br/>不需要构建"| B["用 gh-pages 分支"]
    Q -->|"一次性部署"| B

    style Q fill:#3a2a1a,stroke:#d4a76a,color:#eee
    style A fill:#1a2a1a,stroke:#a5d6a7,color:#eee
    style B fill:#1a2a3a,stroke:#90caf9,color:#eee
```

---

## 四、本项目的实际部署流程

本项目使用 GitHub Actions 方案，完整流程：

```mermaid
flowchart TD
    A["开发者 git push"] --> B["GitHub 检测到<br/>.github/workflows/deploy.yml"]
    B --> C["创建云端 Ubuntu 虚拟机"]
    C --> D["checkout 拉取代码"]
    D --> E["setup-node 安装 Node 20"]
    E --> F["npm ci 安装依赖"]
    F --> G["npm run build<br/>解析唐诗 + 注音 + 输出 dist/"]
    G --> H["upload-pages-artifact<br/>打包 dist/"]
    H --> I["deploy-pages<br/>部署到 Pages 服务器"]
    I --> J["https://yeyangchen2009.github.io/poem300/"]

    style A fill:#3a2a1a,stroke:#d4a76a,color:#eee
    style B fill:#2a2a3a,stroke:#888,color:#eee
    style C fill:#2a2a3a,stroke:#888,color:#eee
    style D fill:#2a2a3a,stroke:#888,color:#eee
    style E fill:#2a2a3a,stroke:#888,color:#eee
    style F fill:#2a2a3a,stroke:#888,color:#eee
    style G fill:#2a2a3a,stroke:#888,color:#eee
    style H fill:#2a2a3a,stroke:#888,color:#eee
    style I fill:#2a2a3a,stroke:#888,color:#eee
    style J fill:#1a2a1a,stroke:#a5d6a7,color:#eee
```

### 踩坑记录

```mermaid
flowchart TD
    P1["package-lock.json<br/>在 .gitignore 中"] --> Fail1["npm ci 报错<br/>Dependencies lock file not found"]
    Fail1 --> Fix1["从 .gitignore 移除<br/>package-lock.json"]
    Fix1 --> OK1["构建成功"]

    P2["在本地切 gh-pages 分支<br/>git rm -rf ."] --> Fail2["工作目录文件全部消失"]
    Fail2 --> Fix2["用 Actions 代替<br/>云端构建，本地不动"]
    Fix2 --> OK2["安全部署"]

    style P1 fill:#3a1a1a,stroke:#ef9a9a,color:#eee
    style Fail1 fill:#3a1a1a,stroke:#ef9a9a,color:#eee
    style Fix1 fill:#1a2a3a,stroke:#90caf9,color:#eee
    style OK1 fill:#1a2a1a,stroke:#a5d6a7,color:#eee
    style P2 fill:#3a1a1a,stroke:#ef9a9a,color:#eee
    style Fail2 fill:#3a1a1a,stroke:#ef9a9a,color:#eee
    style Fix2 fill:#1a2a3a,stroke:#90caf9,color:#eee
    style OK2 fill:#1a2a1a,stroke:#a5d6a7,color:#eee
```
