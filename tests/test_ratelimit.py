"""限流模块测试：滑动窗口计数与 429 响应（不触网）。"""

import tempfile
import unittest
from pathlib import Path
from unittest import mock

import app.core.db as db
from app.core import config
from app.core.ratelimit import hit, rate_limit, reset_rate_limits
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient


class RateLimitTests(unittest.TestCase):
    def setUp(self):
        reset_rate_limits()

    def test_hit_respects_limit(self):
        self.assertTrue(hit("k", 3, 60))
        self.assertTrue(hit("k", 3, 60))
        self.assertTrue(hit("k", 3, 60))
        self.assertFalse(hit("k", 3, 60))

    def test_hit_expires_after_window(self):
        self.assertTrue(hit("k2", 1, 0.0))
        self.assertTrue(hit("k2", 1, 0.0), "窗口为 0 时应立即过期")

    def test_endpoint_returns_429(self):
        api = FastAPI()

        @api.get("/x")
        def x(_rate: None = Depends(rate_limit(limit=2, window=60))):
            return {"ok": True}

        client = TestClient(api)
        self.assertEqual(client.get("/x").status_code, 200)
        self.assertEqual(client.get("/x").status_code, 200)
        self.assertEqual(client.get("/x").status_code, 429)

    def test_auth_login_rate_limited(self):
        from app.main import app

        tmpdir = tempfile.TemporaryDirectory()
        db_path = Path(tmpdir.name) / "test_ratelimit.db"
        patch = mock.patch.object(config, "DB_PATH", db_path)
        patch.start()
        try:
            db.init_db()
            client = TestClient(app)
            for _ in range(10):
                resp = client.post(
                    "/api/auth/login", json={"username": "nobody", "password": "wrong"}
                )
                self.assertNotEqual(resp.status_code, 429, "前 10 次不应被限流")
            resp = client.post("/api/auth/login", json={"username": "nobody", "password": "wrong"})
            self.assertEqual(resp.status_code, 429, "超过 10 次/分钟应被限流")
        finally:
            patch.stop()
            tmpdir.cleanup()
