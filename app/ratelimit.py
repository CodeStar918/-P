"""轻量内存限流：按客户端 IP + 请求路径做滑动窗口计数。

用于登录/注册等敏感接口防爆破。单实例部署下够用；多实例部署时请替换为
Redis 等共享存储实现（保持 rate_limit 依赖签名不变即可）。
"""

import time
from collections import defaultdict, deque
from collections.abc import Callable

from fastapi import HTTPException, Request

_MAX_KEYS = 10_000
_buckets: dict[str, deque[float]] = defaultdict(deque)


def _prune(key: str, window: float) -> None:
    cutoff = time.monotonic() - window
    q = _buckets[key]
    while q and q[0] <= cutoff:
        q.popleft()


def hit(key: str, limit: int, window: float) -> bool:
    """记录一次访问：未超限返回 True；超限返回 False。"""
    _prune(key, window)
    q = _buckets[key]
    if len(q) >= limit:
        return False
    q.append(time.monotonic())
    if len(_buckets) > _MAX_KEYS:
        for stale_key in list(_buckets)[: len(_buckets) // 2]:
            _buckets.pop(stale_key, None)
    return True


def reset_rate_limits() -> None:
    """清空限流状态（测试用）。"""
    _buckets.clear()


def rate_limit(limit: int = 10, window: float = 60.0) -> Callable:
    """FastAPI 依赖：按客户端 IP 与请求路径限流，超限返回 429。"""

    async def _check(request: Request) -> None:
        ip = request.client.host if request.client else "unknown"
        if not hit(f"{ip}:{request.url.path}", limit, window):
            raise HTTPException(status_code=429, detail="请求过于频繁，请稍后再试")

    return _check
