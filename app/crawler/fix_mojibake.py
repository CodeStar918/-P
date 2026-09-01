"""修复 javaguide 来源题目的历史乱码数据（一次性工具）。

根因：javaguide 源站响应头无 charset，requests 按 ISO-8859-1 解码 UTF-8 页面，
中文以 mojibake 形式入库（如 "Java è¯­è¨" 应为 "Java 语言"）。
爬虫已在 _fetch_topic 中显式 resp.encoding="utf-8" 根治新增数据；
本工具还原存量：把 "latin-1 可编码、按 UTF-8 可解码" 的文本做逆向转码。

判定安全性：
- 纯 ASCII 文本 round-trip 后不变，自动跳过；
- 正常中文无法按 latin-1 编码（超出范围），不会被误改；
- 仅 latin-1 编码 + UTF-8 严格解码都成功且结果不同才更新。

用法：
    python -m app.crawler.fix_mojibake          # 干跑：只统计与预览
    python -m app.crawler.fix_mojibake apply    # 写库
"""

import sys
from contextlib import closing

from app.core import db

#: 需要修复的文本列
_TEXT_COLUMNS = ("title", "content", "answer")


def repair_text(text: str | None) -> str | None:
    """尝试把 latin-1 误解码的 UTF-8 文本还原；非乱码原样返回。"""
    if not text:
        return text
    try:
        raw = text.encode("latin-1")
    except UnicodeEncodeError:
        # 正常中文/emoji 无法按 latin-1 编码 → 不是 mojibake
        return text
    try:
        fixed = raw.decode("utf-8")
    except UnicodeDecodeError:
        # latin-1 可编码但不是合法 UTF-8 → 原生 latin-1 文本，不动
        return text
    return fixed if fixed != text else text


def fix_all(apply: bool) -> tuple[int, int]:
    """扫描 javaguide 题目并修复，返回（扫描数, 修复数）。"""
    scanned = fixed = 0
    preview: list[str] = []
    with closing(db.get_conn()) as conn, conn:
        rows = conn.execute(
            "SELECT id, title, content, answer FROM questions WHERE source = 'javaguide'"
        ).fetchall()
        for row in rows:
            scanned += 1
            updates = {}
            for col in _TEXT_COLUMNS:
                new = repair_text(row[col])
                if new != row[col]:
                    updates[col] = new
            if not updates:
                continue
            fixed += 1
            if len(preview) < 3:
                preview.append(f"  {row['title'][:40]!r} -> {(updates.get('title') or '')[:40]!r}")
            if apply:
                sets = ", ".join(f"{c} = ?" for c in updates)
                conn.execute(
                    f"UPDATE questions SET {sets} WHERE id = ?",  # 列名来自白名单常量
                    (*updates.values(), row["id"]),
                )
    if preview:
        print("样例（前 3 条）：")
        print("\n".join(preview))
    return scanned, fixed


def main() -> None:
    apply = "apply" in sys.argv[1:]
    scanned, fixed = fix_all(apply=apply)
    mode = "已写库" if apply else "干跑（加 apply 参数写库）"
    print(f"扫描 javaguide 题目 {scanned} 条，识别乱码 {fixed} 条 —— {mode}")


if __name__ == "__main__":
    main()
