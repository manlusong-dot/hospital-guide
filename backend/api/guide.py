# -*- coding: utf-8 -*-
"""智能导诊接口。"""
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

import dao
import event_pub
from guide_engine import triage

router = APIRouter()


class TriageRequest(BaseModel):
    symptoms: str


@router.post("/triage")
def triage_endpoint(req: TriageRequest) -> dict:
    if not req.symptoms.strip():
        raise HTTPException(status_code=400, detail="请先描述症状")
    result = triage(req.symptoms)
    event_pub.emit("triage", {
        "symptoms": req.symptoms.strip(),
        "dept": result["dept"],
        "alternatives": result["alternatives"],
        "candidates": result.get("candidates", []),
        "status": result.get("status"),
        "match_reasons": result.get("match_reasons", []),
        "urgent_warning": result.get("urgent_warning"),
        "exam_prep": result["exam_prep"],
        "suggestion": result["suggestion"],
    })
    return result


@router.get("/departments")
def list_departments(floor: Optional[int] = None, category: Optional[str] = None) -> list:
    return dao.list_departments(floor, category)


@router.get("/departments/{dept_id}")
def get_department(dept_id: str) -> dict:
    dept = dao.get_department(dept_id)
    if dept is None:
        raise HTTPException(status_code=404, detail=f"找不到科室: {dept_id}")
    return dept


@router.get("/exam-prep")
def exam_prep() -> list:
    return dao.list_exam_prep()


@router.get("/medicine")
def medicine() -> list:
    return dao.list_medicine_guide()
