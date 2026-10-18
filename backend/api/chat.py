# -*- coding: utf-8 -*-
"""AI 对话接口: 维护会话状态, 调引导引擎生成回答。"""
from datetime import datetime
from typing import Optional
from uuid import uuid4

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

import dao
import event_pub
from guide_engine import chat_reply
from process_kb import JourneyState

router = APIRouter()


class ChatRequest(BaseModel):
    session_id: Optional[str] = None
    message: str
    dept_id: Optional[str] = None


@router.post("/chat")
def chat_endpoint(req: ChatRequest) -> dict:
    message = req.message.strip()
    if not message:
        return {"reply": "您想问什么呢? 可以跟我说说哪里不舒服。", "step": None, "session_id": req.session_id}
    session_id = req.session_id or uuid4().hex[:12]
    now = datetime.now().isoformat(timespec="seconds")
    session = dao.get_session(session_id)
    if session is None:
        state = JourneyState(req.dept_id or "", [])
        dao.create_session(session_id, state.to_json(), now)
    else:
        state = JourneyState.from_json(session["state_json"])

    try:
        result = chat_reply(state, message)
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    dao.update_session_state(session_id, state.to_json())
    if state.is_finished():
        dao.update_session_finished(session_id, True)
    dao.save_chat(session_id, "user", message, now)
    dao.save_chat(session_id, "assistant", result["reply"], now)
    resp = {
        "session_id": session_id,
        "reply": result["reply"],
        "step": result["step"],
        "state": result["state"],
        "is_question": result.get("is_question", False),
        "navigation": result.get("navigation"),
    }
    event_pub.emit("chat", {
        "session_id": session_id,
        "user_message": message,
        "reply": result["reply"],
        "step": result["step"],
    })
    return resp


@router.get("/chat/history/{session_id}")
def chat_history(session_id: str) -> list:
    logs = dao.get_chat_logs(session_id, limit=50)
    return list(reversed(logs))


@router.get("/chat/sessions")
def list_sessions(limit: int = 20) -> list:
    """列出最近的就诊会话。"""
    sessions = dao.list_sessions(limit)
    result = []
    for s in sessions:
        try:
            state = JourneyState.from_json(s.get("state_json", "{}"))
            dept = dao.get_department(state.dept_id) if state.dept_id else None
            result.append({
                "session_id": s["id"],
                "created_at": s["created_at"],
                "finished": bool(s.get("finished", False) or state.is_finished()),
                "dept_name": dept["name"] if dept else "未知科室",
                "current_step": state.current + 1,
                "total_steps": len(state.done_keys) + (1 if not state.is_finished() else 0),
            })
        except Exception:
            result.append({
                "session_id": s["id"],
                "created_at": s["created_at"],
                "finished": False,
                "dept_name": "未知科室",
                "current_step": 0,
                "total_steps": 0,
            })
    return result
