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
| 外部依赖 | [TikTokDownloader](https://github.com/JoeanAmier/TikTokDownloader) |

## 快速开始

### 环境要求

- Python 3.12+
- [TikTokDownloader](https://github.com/JoeanAmier/TikTokDownloader)（视频下载服务）

### 安装

```bash
git clone https://github.com/YOUR_USERNAME/ai-we-media.git
cd ai-we-media
pip install -r requirements.txt
```

### 配置

编辑 `config.json`，填入：

- AI API Key 和 Base URL
- 抖音/TikTok Cookie（用于下载）
- 代理地址（可选）

### 启动

**方式一：同时启动 TikTokDownloader + LumenBlader**

```bash
./start.sh
```

**方式二：仅启动 LumenBlader**

```bash
python run.py
```

服务默认运行在 `http://localhost:8080`。

## 项目结构

```
ai-we-media/
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
├── start.sh             # 一键启动脚本
├── run.py               # 服务入口
└── requirements.txt     # Python 依赖
```

## 截图

> 启动后访问 `http://localhost:8080` 查看落地页，`http://localhost:8080/app` 进入工作台。

## License

[MIT](LICENSE) © Mhcjc
