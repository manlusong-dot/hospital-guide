# -*- coding: utf-8 -*-
"""output 层透传: 把系统产出交给"下一个模块"。

透传方式(二选一或同时):
1. 落盘: 每条产出写入 backend/output/outbox/ 目录, 下一模块直接读文件;
2. 推送: 设置环境变量 NEXT_MODULE_ENDPOINT 后, 每条产出以 JSON POST 到该地址。

事件类型与载荷结构见 text/接口约定.md。

设计要求: 落盘是本地快操作, 同步做; 网络推送放到后台守护线程,
失败静默降级, 绝不阻塞 / 拖垮主业务流程。
"""
import json
import os
import threading
import urllib.request
from datetime import datetime
from uuid import uuid4

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTBOX = os.path.join(BASE, "output", "outbox")


def build_record(event_type: str, payload: dict) -> dict:
    """把一次产出格式化成统一事件 envelope。"""
    return {
        "event": event_type,
        "time": datetime.now().isoformat(timespec="seconds"),
        "payload": payload,
    }


def forward(event_type: str, payload: dict) -> dict:
    """透传一条产出事件。

    总是同步落盘一份(便于排错与下游读文件); 若配置了 NEXT_MODULE_ENDPOINT,
    另起后台线程异步 POST。本函数立即返回, 不等待网络。
    """
    os.makedirs(OUTBOX, exist_ok=True)
    record = build_record(event_type, payload or {})
    safe_time = record["time"].replace(":", "-")[:19]
    filename = f"{safe_time}_{event_type}_{uuid4().hex[:8]}.json"
    path = os.path.join(OUTBOX, filename)
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(record, f, ensure_ascii=False, indent=1)
    except OSError:
        path = ""

    endpoint = os.environ.get("NEXT_MODULE_ENDPOINT", "").strip()
    if endpoint:
        # 后台线程推送, 失败静默; daemon 进程退出即回收, 不阻塞主流程。
        t = threading.Thread(
            target=_post_safely, args=(endpoint, record), name="bridge-push", daemon=True
        )
        t.start()
    return {"saved": path, "pushed": bool(endpoint)}


def _post_safely(endpoint: str, record: dict) -> None:
    try:
        ok = _post(endpoint, record)
    except Exception:
        ok = False
    # 静默: 推送失败不影响主流程, 落盘文件仍可被下游补读。
    return ok


def _post(endpoint: str, record: dict) -> bool:
    req = urllib.request.Request(
        endpoint,
        data=json.dumps(record, ensure_ascii=False).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=5) as resp:
        return 200 <= resp.status < 300
