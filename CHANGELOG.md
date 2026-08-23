# 更新日志

本项目遵循[语义化版本](https://semver.org/lang/zh-CN/)。格式参考
[Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/)。

## [未发布]

## [0.1.0] - 2026-08-23

首个可发布版本：面试官小P 核心闭环（模拟面试 + 辅导答疑 + 语音通话 + 题库）。

### 新增

- 统一 FastAPI 服务：Vue3 前端 + REST + SSE 对话 + 语音 WebSocket，单端口 8765
- 多用户账号：pbkdf2 密码散列、Bearer 令牌（30 天有效期）、会话持久化
- 模拟面试：出题 / 点评 / 深度追问 / 面试报告，支持自定义题目与岗位画像
- 辅导答疑：FTS5 全文检索 RAG，输出标准参考回答 + 加分点 + 变式题
- 题库：面试鸭 / LeetCode / JavaGuide 爬虫适配，数据清洗与自动打标签，CSV 导入
- 语音通话：ASR（阿里云 Paraformer）+ TTS（edge-tts / CosyVoice / 浏览器本地回退），
  支持打断与断线自动重连
- 定时爬取调度器（Windows 文件锁防止多实例重复调度）

### 安全

- 修复 SPA 静态文件路由路径遍历漏洞
- `update_question_fields` 增加字段白名单校验，防止 SQL 注入
- 登录 / 注册接口按 IP + 路径限流，防爆破
- 流式模式 LLM 调用失败时完整回滚会话状态（含迭代中途与上下文压缩场景）

### 质量与部署

- 后端 137 个测试用例，CI（lint + test 3.10 / 3.11）全绿
- ruff 静态检查与格式化全量通过
- Docker 多阶段构建升级 node:22，增加 `/health` 就绪探针与 HEALTHCHECK

## [0.0.1] - 2026-08-05

项目初始化：基于 DeepSeek 的 Python 后端面试模拟原型。
