# 面试官小P 🎤

基于 DeepSeek 大模型的 **Python/后端面试模拟与辅导 Agent**。以 Vue3 网页界面为载体（支持**多用户账号**、会话云端持久化），结合实时爬取的面试题库，提供**模拟面试**与**辅导答疑**两种模式，助你为真实面试做好充分准备。

> 🎓 **完全没接触过的小白？** 先看 [小白入门教程](TUTORIAL.md)，从装 Python 到跑起来手把手带你走。

## 功能特性

- **模拟面试**：自我介绍 → 六阶段递进出题（难度由浅入深）→ 每题点评 + 追问深挖 → 结束时输出 0-100 评分总结报告。
- **辅导答疑**：直接提问，小P 给出"标准参考回答 + 加分点 + 变式题"三段式解答，并自动检索本地题库辅助作答（FTS5 全文检索 RAG）。
- **定制面试**：输入**目标岗位 + 招聘信息（JD）**，小P 据此生成一套专属面试题（由浅入深、贴近 JD 技术点）再开始面试。
- **实时题库**：自动爬取面试鸭与 JavaGuide 题库，SQLite 本地存储、按内容哈希增量去重；启动即抓一次、每日定时与按间隔抓取，单实例锁防重复。
- **语音通话**：像打电话一样实时对话——持续收音、边说边答、开口即打断，edge-tts 边生成边播报。
- **多用户账号**：注册 / 登录，会话、收藏、定制面试按账号隔离并持久化，刷新或换设备不丢失。
- **流式输出**：回答逐字渲染（SSE），无需等待整段回复。
- **健壮性**：LLM 指数退避重试、上下文自动压缩、题库接口失败降级本地缓存、FTS5 不可用回退 LIKE、SQLite WAL + busy_timeout。

## 技术栈

| 类别 | 技术 |
|------|------|
| 前端界面 | Vue3 + Vite + Element Plus |
| 后端服务 | FastAPI（统一 REST + WebSocket + 静态托管，单端口） |
| 大模型 | DeepSeek（OpenAI 兼容 SDK） |
| 数据存储 | SQLite（WAL + FTS5 全文索引 + 用户/会话表） |
| 爬虫 | requests + BeautifulSoup + lxml |
| 定时任务 | APScheduler（单实例锁） |
| 测试 | pytest + ruff（GitHub Actions 自动执行） |

## 项目结构

```
智能面试/
├── pyproject.toml             # 单一依赖源 + pytest/ruff 配置
├── .env.example               # 环境变量模板（复制为 .env 后填写）
├── app/                       # 后端应用包
│   ├── voice_server.py        # 统一 Web 服务：Vue3 前端 + REST + 语音 WebSocket（单端口）
│   ├── routers/               # REST 路由（auth / session / questions / custom）
│   ├── agent/                 # 会话状态机 coach.py + DeepSeek 封装 llm.py
│   ├── crawler/               # 数据源适配器（mianshiya / javaguide / leetcode / ...）
│   └── ...
├── frontend/                  # Vue3 前端工程（Vite + Element Plus）
├── tests/                     # 单元测试（数据层、爬虫、LLM、状态机、语音、多用户 API）
├── scripts/                   # start.bat（Windows）/ start.sh（macOS·Linux）
├── deploy/                    # Dockerfile + docker-compose.yml
└── data/                      # 运行时数据（SQLite、日志、锁，已 gitignore）
```

## 快速开始

### 环境要求

- Python 3.10+
- 一个 DeepSeek API Key（[platform.deepseek.com](https://platform.deepseek.com) 获取）

### 安装与配置

```bash
# 1. 安装依赖（含 pytest / ruff 等开发依赖；仅运行可去掉 [dev]）
pip install -e ".[dev]"

# 2. 创建环境变量文件并填入密钥
copy .env.example .env
```

编辑 `.env`，至少配置：

```ini
DEEPSEEK_API_KEY=sk-你的key
```

> ⚠️ `.env` 已被 `.gitignore` 排除，请勿将真实密钥提交到版本控制或公开场合。

### 启动

**方式一（Windows 推荐）**：双击 `scripts/start.bat`，脚本自动安装依赖、构建 Vue3 前端（首次需 Node.js 18+）、端口被占用时自动改用 8766，并打开浏览器。

**方式二（命令行）**：

```bash
# 构建前端（首次或前端代码变更后）
cd frontend && npm install && npm run build && cd ..

# 启动统一服务（Vue3 前端 + REST + 语音，单端口）
python -m uvicorn app.voice_server:app --host 127.0.0.1 --port 8765
```

然后访问 <http://localhost:8765>，注册账号后即可使用（聊天页 `/`、语音通话 `/voice`）。

**方式三（Docker）**：

```bash
cd deploy && docker compose up -d
```

## 使用方法

### 模拟面试

点击「开始面试」，小P 按六个阶段逐题推进（前期偏简单、后期偏难）：

| 阶段 | 考察范围 | 期望难度 |
|------|----------|----------|
| Python 基础 | 语言特性、GIL、装饰器、生成器、内存管理等 | 简单 |
| 数据结构与算法 | 排序、动态规划、双指针、树图、贪心、二分、回溯等 | 中等 |
| 数据库 / SQL | SQL 基础、索引、事务 ACID、Redis 等 | 中等 |
| 网络与并发 | HTTP/TCP、操作系统、多线程 / 协程等 | 中等 |
| 项目深挖 | STAR 法则、技术难点、设计模式、框架工具 | 困难 |
| 场景设计题 | 系统设计、缓存策略、接口设计 | 困难 |

每答完一题先点评（优点 + 不足），再追问一个深挖细节；全部结束后输出评分报告与改进建议清单。

### 辅导答疑

直接在输入框提问（如"Redis 缓存穿透怎么答"），小P 会检索本地题库（FTS5 全文搜索）辅助作答，给出标准参考回答、加分点，以及一道同类变式题供练习。

### 定制面试

开始前输入**目标岗位 + 招聘信息 / JD**，点击"生成定制面试题并开始"。小P 根据 JD 技术栈生成一套递进式面试题（基础 → 核心 → 项目/场景设计），进入模拟面试逐题提问，答完后照常输出评分报告。不填 JD 也可只输入岗位名。

### 语音通话

点击文字版右下角 **📞** 进入 `/voice`（手机式界面），与文字版共用服务与账号：

- 点击「接通」，小P 会像真实电话一样先开口问候，你直接说话即可。
- 识别到一句话就发，小P 边生成边播报；**开口即打断**（播报时你说话即可打断，不会被小P 自己声音误触发）。
- 接通后说"开始面试 / 模拟面试"即可自动切到模拟面试。
- 通话中按钮变「挂断」，点击立即停播并断开。

语音识别由服务端阿里云 Paraformer 完成，需要 `.env` 配置 `DASHSCOPE_API_KEY`（与 CosyVoice 同 Key）；浏览器请用 Chrome / Edge。

## 题库与更新

- **手动抓取**：

  ```bash
  python -m app.crawler.run               # 全量（面试鸭 + JavaGuide）
  python -m app.crawler.run --limit 50   # 调试：每源最多 N 条
  ```

- **定时抓取**：启动后立即抓一次 → 每天 `CRAWL_TIME`（默认 02:00）抓一次 → 按 `CRAWL_INTERVAL_HOURS`（默认 24h）间隔抓取。重复抓取由 `content_hash` 增量去重，单实例锁防止多进程重复运行，日志写入 `data/scheduler.log`（自动轮转）。
- **数据源**：默认内置面试鸭、JavaGuide；牛客为占位（反爬较重暂未接入）；LeetCode 算法题已从题库移除，需要时置 `CRAWL_LEETCODE=1` 开启。新增源继承 `app/crawler/base.py` 的 `SourceAdapter` 并在 `app/crawler/run.py` 登记即可。

## 配置项

| 环境变量 | 默认值 | 说明 |
|----------|--------|------|
| `DEEPSEEK_API_KEY` | 无 | DeepSeek API 密钥（**必填**） |
| `DEEPSEEK_BASE_URL` | `https://api.deepseek.com` | API 地址（OpenAI 兼容） |
| `DEEPSEEK_MODEL` | `deepseek-chat` | 使用的模型名 |
| `LLM_TIMEOUT_SECONDS` | `120` | LLM 请求超时（秒） |
| `LLM_MAX_RETRIES` | `3` | LLM 失败重试次数（指数退避） |
| `CRAWL_TIME` | `02:00` | 每日定时抓取时间 |
| `CRAWL_INTERVAL_HOURS` | `24` | 间隔抓取小时数，`0` 关闭间隔抓取 |
| `CRAWL_PAGES_PER_CATEGORY` | `10` | 面试鸭每个分类抓取页数 |
| `CRAWL_WORKERS` | `3` | 面试鸭分类并行线程数 |
| `LEETCODE_CACHE_HOURS` | `72` | LeetCode 响应缓存有效期（小时） |
| `DB_TIMEOUT_SECONDS` | `10` | SQLite busy_timeout（秒） |
| `APP_HOST` | `127.0.0.1` | 统一服务监听地址（兼容旧 `VOICE_HOST`） |
| `APP_PORT` | `8765` | 统一服务端口（兼容旧 `VOICE_PORT`） |
| `TOKEN_TTL_DAYS` | `30` | 登录令牌有效期（天） |
| `VOICE_TTS` | `edge` | `edge`=edge-tts，`cosyvoice`=阿里云百炼 CosyVoice，`local`=浏览器本地语音 |
| `DASHSCOPE_API_KEY` | 无 | 阿里云百炼 Key（CosyVoice / 语音识别用） |
| `DISABLE_SCHEDULER` | 未设置 | 设为 `1` 可禁用后台爬取（测试/多实例部署用） |

> 完整参数（音色、语速、CosyVoice 配置、VAD 阈值等）见 [.env.example](.env.example)。

## 运行测试

```bash
python -m pytest   # 全量测试
ruff check .       # 静态检查
```

测试默认禁用调度器，LLM 与网络请求全部 mock，不触网、不消耗 API 额度。CI（GitHub Actions）在 Python 3.10 / 3.11 上执行 ruff 与 pytest。

## 常见问题

1. **题库为空，模拟面试无题可出**：先运行 `python -m app.crawler.run` 抓取，或检查 `data/scheduler.log`。
2. **LeetCode 抓取报 403**：无需处理，接口失败会自动重试并降级本地缓存，不影响整体爬取。
3. **语音输入不工作**：使用 Chrome / Edge、已登录，访问 <http://127.0.0.1:8765/health> 应返回 `{"status":"ok"}`；确认已配置 `DASHSCOPE_API_KEY`。
4. **多个实例会重复抓取吗**：不会，`data/scheduler.lock` 单实例锁保证只跑一次调度器；多实例部署时其余实例设 `DISABLE_SCHEDULER=1`。

## 贡献指南

欢迎提交 Issue 与 Pull Request：

- **开发约定**：请先阅读 [AGENTS.md](AGENTS.md)（命令、目录、代码纪律、测试要求）。
- **提交规范**：`type(scope): 中文描述`，一个需求一个提交；改解析器 / 状态机 / 数据库迁移需同步更新单测。
- **测试**：`python -m pytest` 必须全量离线通过（LLM、网络、语音全部 mock），`ruff check .` / `ruff format .` 保持清洁后再提交。
- 提交后经 PR 合入 `main`（分支受保护，需通过 CI 校验）。

## License

[MIT](LICENSE) © 2026 MianShiGuanXiaoP Contributors