"""BUG 检测报告第一批修复的回归测试。

覆盖问题编号（见 BUG 检测报告）：
- #1  题库 tags 查询参数契约（axios 序列化修复后的后端回归）
- #8  SQLite WAL 模式
- #11 /api/session/history 的 limit 越界（-1 拉全表）
- #18 LLM 重试范围收紧（4xx 不再重试）
- #2  javaguide 乱码存量修复工具（repair_text 判定与还原）
"""

import sqlite3
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

from app import config, db
from app.agent import llm
from app.crawler.fix_mojibake import repair_text
from app.ratelimit import reset_rate_limits
from app.voice_server import app
from fastapi.testclient import TestClient
from openai import APIStatusError, RateLimitError


def _isolate_rate_limit():
    """注册类测试与既有用例共享 /api/auth 限流桶（5 次/60s），前后清空防串扰。"""
    reset_rate_limits()


def _api_error(status: int) -> APIStatusError:
    """构造带 status_code 的 APIStatusError（openai SDK 签名）。"""
    resp = SimpleNamespace(status_code=status, headers={}, request=SimpleNamespace())
    return APIStatusError(f"http {status}", response=resp, body=None)


class WalModeTests(unittest.TestCase):
    """bug #8：init_db 后必须处于 WAL 模式（读写不互斥）。"""

    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self._patch = mock.patch.object(config, "DB_PATH", Path(self._tmpdir.name) / "wal.db")
        self._patch.start()

    def tearDown(self):
        self._patch.stop()
        self._tmpdir.cleanup()

    def test_wal_enabled_after_init(self):
        db.init_db()
        conn = sqlite3.connect(config.DB_PATH)
        try:
            mode = conn.execute("PRAGMA journal_mode").fetchone()[0]
        finally:
            conn.close()
        self.assertEqual(mode.lower(), "wal")


class HistoryLimitTests(unittest.TestCase):
    """bug #11：limit 无下界时 SQLite LIMIT -1 等价无限制，可拉全表。"""

    def setUp(self):
        _isolate_rate_limit()
        self._tmpdir = tempfile.TemporaryDirectory()
        self._patch = mock.patch.object(config, "DB_PATH", Path(self._tmpdir.name) / "limit.db")
        self._patch.start()
        db.init_db()
        self.client = TestClient(app)
        r = self.client.post(
            "/api/auth/register", json={"username": "limituser", "password": "pass123456"}
        )
        self.hdr = {"Authorization": f"Bearer {r.json()['token']}"}

    def tearDown(self):
        self._patch.stop()
        _isolate_rate_limit()
        self._tmpdir.cleanup()

    def test_negative_and_zero_limit_rejected(self):
        for bad in (-1, 0, 201, 10**9):
            resp = self.client.get("/api/session/history", params={"limit": bad}, headers=self.hdr)
            self.assertEqual(resp.status_code, 422, f"limit={bad} 应被 422 拒绝")

    def test_valid_limit_accepted(self):
        resp = self.client.get("/api/session/history", params={"limit": 1}, headers=self.hdr)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["items"], [])

    def test_rows_exposed_fields_are_light(self):
        """瘦列回归：历史行不再携带 state_json/jd 等大字段。"""
        db.create_session("coach", job_title="t", user_id=999999, state_json='{"big": 1}')
        items = db.list_sessions_by_user(999999, limit=10)
        self.assertEqual(len(items), 1)
        self.assertNotIn("state_json", items[0])
        self.assertNotIn("jd", items[0])
        self.assertIn("score", items[0])


class LlmRetryScopeTests(unittest.TestCase):
    """bug #18：4xx 客户端错误立即抛出，瞬时错误才重试。"""

    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self._patch = mock.patch.object(config, "DB_PATH", Path(self._tmpdir.name) / "llm.db")
        self._patch.start()
        db.init_db()

    def tearDown(self):
        self._patch.stop()
        self._tmpdir.cleanup()

    def _run_chat(self, exc: Exception, max_retries: int = 3) -> tuple[int, object]:
        """mock 客户端永远抛 exc，返回（create 调用次数, 抛出的异常）。"""
        calls = {"n": 0}

        def boom(**kwargs):
            calls["n"] += 1
            raise exc

        fake = SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=boom)))
        with (
            mock.patch.object(llm, "get_client", return_value=fake),
            mock.patch.object(llm.time, "sleep"),
        ):
            try:
                llm.chat([{"role": "user", "content": "hi"}], max_retries=max_retries)
                raised = None
            except Exception as e:
                raised = e
        return calls["n"], raised

    def test_4xx_no_retry(self):
        for status in (400, 401, 403, 422):
            n, raised = self._run_chat(_api_error(status))
            self.assertEqual(n, 1, f"http {status} 不应重试")
            self.assertIsInstance(raised, APIStatusError)

    def test_5xx_and_ratelimit_retry(self):
        rate_limit = RateLimitError(
            "rate",
            response=SimpleNamespace(status_code=429, headers={}, request=SimpleNamespace()),
            body=None,
        )
        for exc in (_api_error(500), _api_error(503), rate_limit):
            n, raised = self._run_chat(exc)
            self.assertEqual(n, 3, f"{type(exc).__name__} 应重试满 3 次")
            self.assertIs(raised, exc)

    def test_connection_error_retry(self):
        n, _ = self._run_chat(ConnectionError("boom"))
        self.assertEqual(n, 3)


class TagsContractTests(unittest.TestCase):
    """bug #1 回归：tags 数组查询参数过滤正常（前端 axios 序列化已对齐 tags=a&tags=b）。"""

    def setUp(self):
        _isolate_rate_limit()
        self._tmpdir = tempfile.TemporaryDirectory()
        self._patch = mock.patch.object(config, "DB_PATH", Path(self._tmpdir.name) / "tags.db")
        self._patch.start()
        db.init_db()
        db.upsert_question(source="probe", title="Redis 持久化方式", tags=["Redis"])
        db.upsert_question(source="probe", title="Django ORM", tags=["Django"])
        self.client = TestClient(app)
        r = self.client.post(
            "/api/auth/register", json={"username": "tagsuser", "password": "pass123456"}
        )
        self.hdr = {"Authorization": f"Bearer {r.json()['token']}"}

    def tearDown(self):
        self._patch.stop()
        _isolate_rate_limit()
        self._tmpdir.cleanup()

    def test_tags_filter_matches_contract(self):
        body = self.client.get(
            "/api/questions", params={"tags": ["Redis"]}, headers=self.hdr
        ).json()
        items = body.get("items", body)
        self.assertEqual(len(items), 1)
        self.assertIn("Redis", items[0]["title"])


def _mojibake(text: str) -> str:
    """按真实故障路径构造乱码样本：UTF-8 字节被按 latin-1 误解码。"""
    return text.encode("utf-8").decode("latin-1")


class RepairTextTests(unittest.TestCase):
    """bug #2 存量乱码修复工具：latin-1 误解码的 UTF-8 文本可无损还原。"""

    def test_mojibake_restored(self):
        # 真实故障路径 round-trip：中文 -> mojibake -> repair 还原
        for original in (
            "Java 语言有哪些特点？",
            "⭐️ JVM vs JDK vs JRE",
            "为什么说 Java 语言“编译与解释并存”？",
        ):
            self.assertEqual(repair_text(_mojibake(original)), original)

    def test_ascii_unchanged(self):
        self.assertEqual(repair_text("Java SE vs Java EE"), "Java SE vs Java EE")
        self.assertEqual(repair_text(""), "")

    def test_normal_chinese_unchanged(self):
        text = "在项目中如何利用 Redis 实现分布式 Session？"
        self.assertEqual(repair_text(text), text)

    def test_none_and_latin1_passthrough(self):
        self.assertIsNone(repair_text(None))
        # latin-1 原生文本（非法 UTF-8 序列）不动
        raw = "caf\xe9"
        self.assertEqual(repair_text(raw), raw)


if __name__ == "__main__":
    unittest.main()
