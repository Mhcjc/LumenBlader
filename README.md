# LumenBlader

一站式管理抖音与 TikTok 博主，批量下载视频，AI 深度分析内容质量与爆款潜力。

## 功能特性

- **博主管理** — 粘贴抖音/TikTok 主页链接，自动识别平台、获取昵称、创建本地目录
- **批量下载** — 按时间范围批量下载视频，支持并发、断点续传、失败重试
- **单视频下载** — 粘贴单条视频链接，快速下载
- **AI 分析** — 7 维度 Rubric 打分（选题吸引力、深度、清晰度、情感共鸣、信息密度、独特角度、行动引导），支持摘要和深度两种模式
- **实时进度** — 下载任务实时追踪，状态筛选，进度可视化
- **本地部署** — 数据完全自主，无需注册

## 技术栈

| 层级 | 技术 |
|------|------|
| 后端 | Python 3.12、FastAPI、Uvicorn、aiosqlite |
| 前端 | 原生 HTML/CSS/JS（Apple 风格设计） |
| AI | OpenAI 兼容 API（通过 httpx） |
| 视频下载 | [TikTokDownloader](https://github.com/JoeanAmier/TikTokDownloader)（Web API 模式） |
| 分析方法论 | [Cheat on Content](https://github.com/XBuilderLAB/cheat-on-content)（Rubric 打分体系） |

## 依赖项目说明

LumenBlader 本身是一个轻量管理面板，核心能力依赖以下两个开源项目：

### TikTokDownloader — 视频数据采集与下载引擎

[TikTokDownloader](https://github.com/JoeanAmier/TikTokDownloader)（又名 DouK-Downloader）是一个功能完整的抖音/TikTok 数据采集工具。LumenBlader 以 **Web API 模式** 启动它，通过 HTTP 接口调用以下能力：

- **视频详情获取** — 解析视频 ID，获取下载链接、标题、作者信息
- **账号作品列表** — 按时间范围批量获取博主发布的视频列表
- **短链解析** — 将 `v.douyin.com` 短链接解析为完整 URL
- **文件下载** — 实际的视频文件下载由 TikTokDownloader 完成

启动时 TikTokDownloader 运行在 `http://127.0.0.1:5555`，LumenBlader 的 `config.json` 中 `tiktok_downloader.api_base_url` 指向此地址。

### Cheat on Content — 内容分析方法论

[Cheat on Content](https://github.com/XBuilderLAB/cheat-on-content) 提供了一套「打分 → 预测 → 发布 → 复盘 → 进化 Rubric」的内容分析方法论。LumenBlader 的 AI 分析功能借鉴了其 **7 维度 Rubric 打分体系**：

| 维度 | 说明 |
|------|------|
| 选题吸引力 | 话题是否自带流量 |
| 内容深度 | 信息是否有实质 |
| 表达清晰度 | 结构是否易懂 |
| 情绪共鸣 | 是否触发情感反应 |
| 信息密度 | 每分钟有效信息量 |
| 独特角度 | 是否有差异化视角 |
| 行动召唤力 | 是否促使观众行动 |

Cheat on Content 本身是一个 Claude Code Skill（方法论框架），不作为 LumenBlader 的运行时依赖。如果你在 Claude Code 环境中使用，可以通过 `/cheat-init` 等命令启动完整的校准循环。

## 快速开始

### 环境要求

- Python 3.12+
- [TikTokDownloader](https://github.com/JoeanAmier/TikTokDownloader)（视频下载服务）
- （可选）[Cheat on Content](https://github.com/XBuilderLAB/cheat-on-content)（用于 Claude Code 中的进阶分析工作流）

### 目录结构要求

LumenBlader 假定三个项目在同一父目录下：

```
AIWeMedia/                     # 父目录
├── TikTokDownloader/          # 视频下载引擎（必须）
│   ├── .venv/                 # TikTokDownloader 的 Python 虚拟环境
│   └── main.py
├── LumenBlader/               # 本项目
│   ├── .venv/                 # LumenBlader 的 Python 虚拟环境
│   └── start.sh
├── cheat-on-content/          # 分析方法论 Skill（可选，供 Claude Code 使用）
└── materials/                 # 视频素材与分析报告存放目录
```

### 安装

```bash
# 1. 克隆 TikTokDownloader 并安装依赖
git clone https://github.com/JoeanAmier/TikTokDownloader.git
cd TikTokDownloader
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cd ..

# 2. 克隆 LumenBlader 并安装依赖
git clone https://github.com/Mhcjc/LumenBlader.git
cd LumenBlader
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 3. （可选）克隆 Cheat on Content，供 Claude Code 进阶分析
git clone https://github.com/XBuilderLAB/cheat-on-content.git
```

### 配置

编辑 LumenBlader 的 `config.json`，填入：

- **AI API Key 和 Base URL** — 用于内容分析的 LLM 服务
- **抖音/TikTok Cookie** — 用于下载（从浏览器开发者工具获取）
- **代理地址**（可选）— TikTok 需要

TikTokDownloader 首次启动时会引导你完成自身配置（语言、免责声明、运行模式选择 Web API）。

### 启动

**方式一：一键启动 TikTokDownloader + LumenBlader（推荐）**

```bash
./start.sh
```

此脚本会自动启动 TikTokDownloader（Web API 模式，端口 5555）和 LumenBlader（端口 8080）。

**方式二：仅启动 LumenBlader**

```bash
python run.py
```

适用于 TikTokDownloader 已单独运行的场景。

服务默认运行在 `http://localhost:8080`，TikTokDownloader API 在 `http://127.0.0.1:5555`。

## 项目结构

```
LumenBlader/
├── server/              # FastAPI 后端
│   ├── main.py          # 应用入口
│   ├── routers/         # API 路由（accounts, downloads, analysis, settings）
│   └── services/        # 业务逻辑（downloader, analyzer, file_manager）
├── frontend/            # 前端静态文件
│   ├── index.html       # 落地页
│   ├── app.html         # 工作台
│   ├── js/              # 页面逻辑
│   └── css/             # 样式
├── config.json          # 运行时配置
├── start.sh             # 一键启动脚本（同时启动 TikTokDownloader + LumenBlader）
├── run.py               # 仅启动 LumenBlader
└── requirements.txt     # Python 依赖
```

## 截图

> 启动后访问 `http://localhost:8080` 查看落地页，`http://localhost:8080/app` 进入工作台。

## License

[MIT](LICENSE) © Mhcjc
