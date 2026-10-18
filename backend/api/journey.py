# -*- coding: utf-8 -*-
"""就诊流程卡与步骤推进接口。步骤推进走状态机, 不经过大模型。"""
from datetime import datetime
from typing import Optional
from uuid import uuid4

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

import dao
import event_pub
from demo import appointment_is_expired
from guide_engine import build_process_card
from process_kb import JourneyState, PROCESS_STEPS

router = APIRouter()


class CardRequest(BaseModel):
    dept_id: str
    exams: Optional[list] = None


class SessionRequest(BaseModel):
    session_id: Optional[str] = None
    dept_id: str
    exams: Optional[list] = None
    start_key: Optional[str] = None
    registration_id: Optional[str] = None


class StepRequest(BaseModel):
    session_id: str
    action: str  # next / back / jump / finish
    key: Optional[str] = None


class ExamOrdersRequest(BaseModel):
    session_id: str
    exams: list[str]


@router.post("/journey/card")
def journey_card(req: CardRequest) -> dict:
    if dao.get_department(req.dept_id) is None:
        raise HTTPException(status_code=404, detail=f"找不到科室: {req.dept_id}")
    card = build_process_card(req.dept_id, req.exams)
    event_pub.emit("journey", {
        "trigger": "card",
        "dept": card["dept"],
        "steps": card["steps"],
        "current_step": card["steps"][0] if card["steps"] else None,
        "done_keys": [],
    })
    return card


@router.post("/journey/session")
def create_session(req: SessionRequest) -> dict:
    if dao.get_department(req.dept_id) is None:
        raise HTTPException(status_code=404, detail=f"找不到科室: {req.dept_id}")
    registration = None
    if req.registration_id:
        registration = dao.get_registration(req.registration_id)
        if registration is None:
            raise HTTPException(status_code=404, detail="预约记录不存在")
        if registration["dept_id"] != req.dept_id:
            raise HTTPException(status_code=400, detail="预约记录与就诊科室不一致")

    linked_session_id = registration.get("journey_session_id") if registration else None
    if linked_session_id:
        session_id = linked_session_id
        session = dao.get_session(session_id)
        if session is None:
            raise HTTPException(status_code=409, detail="预约已使用，但原就诊流程不存在，不能重新创建")
        state = JourneyState.from_json(session["state_json"])
        if state.dept_id != req.dept_id:
            raise HTTPException(status_code=400, detail="预约绑定的就诊科室不一致")
    else:
        session_id = req.session_id or uuid4().hex[:12]
        session = dao.get_session(session_id) if req.session_id else None
        if session is not None:
            state = JourneyState.from_json(session["state_json"])
            if state.dept_id != req.dept_id:
                raise HTTPException(status_code=400, detail="就诊会话与预约科室不一致")
        else:
            state = JourneyState(req.dept_id, req.exams or [], req.start_key or "")
            dao.create_session(session_id, state.to_json(), datetime.now().isoformat(timespec="seconds"))
        if registration:
            dao.link_registration_session(registration["id"], session_id)
            linked = dao.get_registration(registration["id"])
            if linked and linked.get("journey_session_id") != session_id:
                session_id = linked["journey_session_id"]
                session = dao.get_session(session_id)
                if session is None:
                    raise HTTPException(status_code=409, detail="预约已使用，但原就诊流程不存在，不能重新创建")
                state = JourneyState.from_json(session["state_json"])
    if registration and appointment_is_expired(registration["visit_date"], registration["slot"]):
        if not linked_session_id or not state.is_finished():
            raise HTTPException(status_code=409, detail="预约时间段已过，不能进入就诊流程")
    # 已有会话以会话中保存的医生医嘱为准，不能被前端重新生成的常见项目覆盖。
    card = build_process_card(req.dept_id, state.exams)
    result = {"session_id": session_id, "step": state.current_step(), "card": card}
    event_pub.emit("journey", {
        "trigger": "session",
        "session_id": session_id,
        "dept": card["dept"],
        "steps": card["steps"],
        "current_step": result["step"],
        "done_keys": state.done_keys,
    })
    return result


@router.post("/journey/orders")
def update_exam_orders(req: ExamOrdersRequest) -> dict:
    """保存医生开具的检查单项目，并据此生成检查须知和导航。"""
    session = dao.get_session(req.session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="会话不存在, 请先创建")
    state = JourneyState.from_json(session["state_json"])
    state.exams = [str(item).strip() for item in req.exams if str(item).strip()]
    # 保持原顺序并去重，避免重复检查项目造成重复提示。
    state.exams = list(dict.fromkeys(state.exams))
    dao.update_session_state(req.session_id, state.to_json())
    card = build_process_card(state.dept_id, state.exams)
    result = {"step": state.current_step(), "state": state.to_dict(), "card": card}
    event_pub.emit("journey", {
        "trigger": "doctor_orders",
        "session_id": req.session_id,
        "dept_id": state.dept_id,
        "exam_names": state.exams,
        "current_step": result["step"],
    })
    return result


@router.post("/journey/step")
def step_action(req: StepRequest) -> dict:
    session = dao.get_session(req.session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="会话不存在, 请先创建")
    state = JourneyState.from_json(session["state_json"])
    if state.is_finished():
        raise HTTPException(status_code=409, detail="本次就诊已完成，只能查看流程记录")
    if req.action == "next":
        step = state.advance()
        if state.current >= len(PROCESS_STEPS) - 1:
            state.finish()
    elif req.action == "back":
        step = state.back()
    elif req.action == "finish":
        if state.current < len(PROCESS_STEPS) - 1:
            raise HTTPException(status_code=400, detail="请先完成前面的就诊步骤")
        state.finish()
        step = state.current_step()
    elif req.action == "jump" and req.key:
        step = state.jump_to(req.key)
    else:
        raise HTTPException(status_code=400, detail="action 需为 next / back / jump / finish")
    dao.update_session_state(req.session_id, state.to_json())
    result = {"step": step, "state": state.to_dict()}
    event_pub.emit("journey", {
        "trigger": "step",
        "session_id": req.session_id,
        "action": req.action,
        "dept_id": state.dept_id,
        "current_step": step,
        "done_keys": state.done_keys,
    })
    return result


@router.get("/journey/session/{session_id}")
def get_session_state(session_id: str) -> dict:
    session = dao.get_session(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="会话不存在")
    state = JourneyState.from_json(session["state_json"])
    return {"session_id": session_id, "step": state.current_step(), "state": state.to_dict()}
