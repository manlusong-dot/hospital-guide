# -*- coding: utf-8 -*-
"""业务侧事件发布的安全薄封装。

后端各接口在产出结果后调用 emit(event_type, payload) 透传给下一模块。
本模块保证:
- 懒加载 backend.output.bridge, 找不到/导入失败时降级为"只记录不推送", 绝不影响主流程;
- emit 内部吞掉一切异常, 业务接口不会因为透传而 5xx。
"""
import os
import sys
from typing import Any

# backend/api/event_pub.py -> backend/ -> 项目根
_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

_forward = None
_load_failed = False


def _load_forward():
    global _forward, _load_failed
    if _forward is not None or _load_failed:
        return _forward
    try:
        from backend.output.bridge import forward  # type: ignore
        _forward = forward
    except Exception:
        _load_failed = True
        _forward = None
    return _forward


def emit(event_type: str, payload: Any) -> None:
    """透传一条事件。任何异常都被吞掉, 不影响接口返回。"""
    try:
        fn = _load_forward()
        if fn is None:
            return
        fn(event_type, payload if isinstance(payload, dict) else {"data": payload})
    except Exception:
        # 静默降级: 透传是旁路, 主流程不能被它拖垮。
        return None
