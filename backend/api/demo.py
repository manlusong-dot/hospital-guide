# -*- coding: utf-8 -*-
"""挂号演示接口: 本地假数据流程, 不接真实支付。"""
from datetime import datetime, time
from typing import Optional
from uuid import uuid4

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

import dao
import event_pub

router = APIRouter()

SLOT_END_HOURS = {"上午": 12, "下午": 17, "晚上": 21}


def _slot_end_hour(slot: str):
    normalized = str(slot or "").strip()
    aliases = {
        "上午": ("上午", "早上"),
        "下午": ("下午",),
        "晚上": ("晚上", "晚间"),
    }
    for canonical, values in aliases.items():
        if normalized in values or any(value in normalized for value in values):
            return SLOT_END_HOURS[canonical]
    return None


def appointment_is_expired(visit_date: str, slot: str, now: datetime = None) -> bool:
    """判断预约时段是否已结束；演示预约按上午12点、下午17点、晚上21点截止。"""
    try:
        visit_day = datetime.strptime(str(visit_date), "%Y-%m-%d").date()
    except (TypeError, ValueError):
        return True
    current = now or datetime.now()
    if visit_day < current.date():
        return True
    if visit_day > current.date():
        return False
    # Unknown labels cannot be safely classified as expired. Keep harmless
    # display-label variations from blocking an appointment at midnight.
    end_hour = _slot_end_hour(slot)
    if end_hour is None:
        return False
    return current >= datetime.combine(visit_day, time(end_hour, 0))


class RegisterRequest(BaseModel):
    patient_name: str
    doctor_id: str
    visit_date: str
    slot: str


@router.get("/demo/doctors")
def list_doctors(dept_id: Optional[str] = None) -> list:
    return dao.list_doctors(dept_id)


@router.post("/demo/register")
def register(req: RegisterRequest) -> dict:
    doctor = dao.get_doctor(req.doctor_id)
    if doctor is None:
        raise HTTPException(status_code=404, detail=f"找不到医生: {req.doctor_id}")
    if not req.patient_name.strip():
        raise HTTPException(status_code=400, detail="请填写就诊人姓名")
    if not req.visit_date.strip() or not req.slot.strip():
        raise HTTPException(status_code=400, detail="请选择就诊日期和时段")
    reg_id = "R" + datetime.now().strftime("%Y%m%d") + uuid4().hex[:6]
    now = datetime.now().isoformat(timespec="seconds")
    dao.create_registration(reg_id, req.patient_name.strip(), doctor["id"], doctor["dept_id"],
                            req.visit_date.strip(), req.slot.strip(), now)
    dept = dao.get_department(doctor["dept_id"])
    result = {
        "registration_id": reg_id,
        "patient_name": req.patient_name.strip(),
        "doctor": doctor["name"],
        "dept": dept["name"] if dept else doctor["dept_id"],
        "visit_date": req.visit_date,
        "slot": req.slot,
        "status": "已预约(演示)",
    }
    event_pub.emit("registration", result)
    return result


@router.get("/demo/registrations")
def registrations(patient_name: Optional[str] = None) -> list:
    rows = dao.list_registrations(patient_name)
    result = []
    for r in rows:
        doctor = dao.get_doctor(r["doctor_id"])
        dept = dao.get_department(r["dept_id"])
        item = dict(r)
        item["doctor_name"] = doctor["name"] if doctor else r["doctor_id"]
        item["dept_name"] = dept["name"] if dept else r["dept_id"]
        item["floor"] = dept["floor"] if dept else None
        item["journey_completed"] = False
        session_id = r.get("journey_session_id")
        if session_id:
            session = dao.get_session(session_id)
            if session:
                try:
                    import json
                    item["journey_completed"] = bool(json.loads(session["state_json"] or "{}").get("finished", False))
                except (TypeError, ValueError):
                    item["journey_completed"] = False
        item["is_expired"] = appointment_is_expired(r["visit_date"], r["slot"])
        item["can_enter"] = item["journey_completed"] or not item["is_expired"]
        item["journey_status"] = "已完成" if item["journey_completed"] else ("已过期" if item["is_expired"] else "待就诊")
        result.append(item)
    return result
