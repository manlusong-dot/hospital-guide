# -*- coding: utf-8 -*-
"""就医引导引擎: 智能导诊 + 流程卡生成 + 对话编排。

分工: 状态机/知识库负责确定性流程, 大模型负责大白话解释与答疑。
大模型不可用时自动降级为知识库直答, 保证演示不中断。
"""
import os
import re
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(BASE, "database"))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import dao
import llm_client
from process_kb import (
    PROCESS_STEPS,
    JourneyState,
    detect_urgent_risk,
    generate_department_candidates,
    select_department_candidate,
)

SYSTEM_PROMPT = (
    "你是深圳大学医院的就医陪伴助手, 服务对象是中老年人和带小孩的家长。"
    "说话要求: 句子短, 一次只说一件事, 不用专业术语, 重要的话放前面, 数字用阿拉伯数字。"
    "只回答就医相关问题; 拿不准的病情问题建议当面问医生, 不要自己下诊断。"
)

_NEXT_WORDS = ("下一步", "继续", "好了", "完成了", "搞定", "弄完了", "做完")
_BACK_WORDS = ("上一步", "回去", "返回上", "退一步")

# 常见问答关键词, 命中这些时不推进步骤, 直接回答问题
_QA_KEYWORDS = [
    "药怎么吃", "怎么吃", "吃药", "用法", "用量", "一天几次", "副作用",
    "多少钱", "费用", "报销", "医保",
    "报告多久", "报告出来", "取报告",
    "空腹", "憋尿", "注意什么",
    "在哪", "在哪里", "怎么走", "怎么去",
    "多久", "多长时间", "几点",
    "需要", "要带", "带什么",
    "什么意思", "是什么", "为什么",
    "怎么办", "怎么处理",
    "复诊", "复查",
    "挂号", "预约",
    "症状", "病情", "严重吗",
]


def triage(symptoms: str) -> dict:
    """症状 -> 推荐科室。规则先行，候选不足时才让 LLM 在候选中选择。"""
    departments = dao.list_departments()
    candidates = generate_department_candidates(symptoms, departments)
    decision = select_department_candidate(candidates)
    used_llm = False
    selected_id = decision.get("dept_id")
    if decision["status"] != "confident" and candidates:
        picked = _llm_pick_department(symptoms, candidates)
        used_llm = picked is not None
        if picked:
            selected_id = picked
    primary = dao.get_department(selected_id) if selected_id else None
    candidate_views = []
    for candidate in candidates[:5]:
        dept = dao.get_department(candidate["dept_id"])
        if dept:
            view = dict(dept)
            view.update({k: candidate[k] for k in ("score", "matched_terms", "reasons", "rank")})
            view["reason_text"] = "；".join(candidate.get("reasons", []))
            candidate_views.append(view)
    alternatives = [d for d in candidate_views if not primary or d["id"] != primary["id"]][:3]
    selected_view = next(
        (candidate for candidate in candidate_views if primary and candidate["id"] == primary["id"]),
        candidate_views[0] if candidate_views else None,
    )
    risk = detect_urgent_risk(symptoms)
    if risk["is_emergency"]:
        suggestion = risk["message"] + "。普通科室推荐仅供参考，不要等待普通门诊。"
    elif primary:
        suggestion = f"根据症状依据，建议先挂{primary['name']}(在{primary['floor']}楼)"
    else:
        suggestion = "目前无法根据描述确定唯一科室，请补充症状或选择下方候选科室。"
    return {
        "dept": primary,
        "alternatives": alternatives,
        "candidates": candidate_views,
        "status": "llm_selected" if used_llm and primary else decision["status"],
        "confidence": "uncertain" if not primary else ("medium" if used_llm else "high"),
        "match_reasons": (selected_view["reasons"] if selected_view else []),
        "match_reason_text": ("；".join(selected_view["reasons"]) if selected_view else ""),
        "urgent_warning": risk,
        "exam_prep": _preps_for_dept(primary),
        "used_llm": used_llm,
        "suggestion": suggestion,
    }


def _llm_pick_department(symptoms: str, candidates: list):
    """只允许 LLM 从已经召回的真实科室候选中选择。"""
    if not candidates:
        return None
    lines = []
    for candidate in candidates[:8]:
        dept = dao.get_department(candidate["dept_id"])
        if not dept:
            continue
        evidence = "、".join(candidate.get("matched_terms", [])[:5]) or "弱匹配"
        lines.append(f"{dept['id']}:{dept['name']}（依据:{evidence}）")
    allowed_ids = [candidate["dept_id"] for candidate in candidates[:8] if dao.get_department(candidate["dept_id"])]
    if not allowed_ids:
        return None

    prompt = (
        "根据患者症状从候选科室中选择最合适的一个。只能返回候选列表中的科室id。\n"
        "患者症状: " + symptoms + "\n"
        "候选科室:\n" + "\n".join(lines) + "\n"
        "允许的id: " + ",".join(allowed_ids) + "\n"
        "如果无法判断，只回答 UNKNOWN。不要输出候选列表之外的id。"
    )
    try:
        answer = llm_client.chat_with_system(SYSTEM_PROMPT, prompt, max_tokens=20, temperature=0.1)
    except RuntimeError:
        return None
    answer = answer.strip()
    if answer.upper() == "UNKNOWN":
        return None
    # 兼容 id、id:name、id：name 和带解释文本的返回，但只认候选 ID。
    for dept_id in sorted(allowed_ids, key=len, reverse=True):
        if re.search(rf"(?<![A-Za-z0-9_]){re.escape(dept_id)}(?![A-Za-z0-9_])", answer):
            return dept_id
    return None


def _preps_for_dept(dept: dict) -> list:
    if not dept:
        return []
    exams = [e.strip().lower() for e in (dept.get("common_exams") or "").split(",") if e.strip()]
    if not exams:
        return []
    result = []
    for prep in dao.list_exam_prep():
        kws = [k.strip().lower() for k in (prep.get("keywords") or "").split(",") if k.strip()]
        kws.append(prep["exam_name"].lower())
        for exam in exams:
            if any(exam in kw or kw in exam for kw in kws):
                result.append(prep)
                break
    return result


# 检查项目 -> 导航地点(按顺序匹配, 命中即停)
EXAM_NAV = [
    ("抽血", "检验科"), ("验血", "检验科"), ("血常规", "检验科"), ("生化", "检验科"),
    ("b超", "超声科"), ("彩超", "超声科"),
    ("胃镜", "消化内镜中心"), ("肠镜", "消化内镜中心"),
    ("ct", "放射科"), ("核磁", "放射科"), ("x光", "放射科"), ("拍片", "放射科"), ("放射", "放射科"),
    ("心电", "功能检查中心"),
]


def normalize_exam_orders(exams) -> list:
    """只保留用户明确录入的医生检查单项目，不从科室常见项目推测。"""
    if not isinstance(exams, list):
        return []
    result = []
    seen = set()
    for exam in exams:
        name = str(exam or "").strip()
        if not name:
            continue
        key = name.lower()
        if key not in seen:
            seen.add(key)
            result.append(name)
    return result


def _resolve_nav(target: str, label: str, dept, exam_names: list) -> tuple:
    """把步骤模板里的占位目标解析成(可导航的地点, 显示名)。"""
    if target == "@dept":
        name = dept["name"] if dept else ""
        return name, name
    if target == "@register":
        # 挂号点按楼层区分，避免模糊名称总是命中 2 楼节点。
        floor = int(dept.get("floor") or 1) if dept else 1
        register_id = "1f_poi_cfy1" if floor == 1 else f"{floor}f_poi_cfy"
        if dao.find_nav_node(register_id):
            return register_id, label or "挂号收费处"
        return "分层挂号收费", label or "挂号收费处"
    if target == "@exam":
        if not exam_names:
            return "", "请以医生开的检查单为准"
        joined = ",".join(exam_names).lower()
        for kw, place in EXAM_NAV:
            if kw in joined:
                return place, place
        return "", "请按检查单上的地点办理"
    return target, label


def build_process_card(dept_id: str, exams: list = None) -> dict:
    """生成结构化就诊流程卡。"""
    dept = dao.get_department(dept_id)
    # 检查项目必须来自医生实际开具的检查单。科室的常见项目仅用于后台知识展示，
    # 不能据此替患者生成检查项目或导航目的地。
    exam_names = normalize_exam_orders(exams)
    preps = _preps_for_dept(dept)
    steps = []
    for i, s in enumerate(PROCESS_STEPS):
        nav_target, nav_label = _resolve_nav(s["nav_target"], s["nav_label"], dept, exam_names)
        if s["key"] == "report":
            # 取报告地点必须跟随实际检查单；没有检查单时不提供默认检验科导航。
            nav_target, nav_label = _resolve_nav("@exam", "", dept, exam_names)
        item = {
            "key": s["key"], "title": s["title"], "desc": s["desc"],
            "tips": s["tips"], "index": i,
            "nav_target": nav_target, "nav_label": nav_label,
        }
        if s["key"] == "register" and dept:
            item["poi"] = f"挂号收费处(可直达{dept['name']}, {dept['floor']}楼)"
        elif s["key"] == "exam":
            item["poi"] = (
                "医生检查单: " + ", ".join(exam_names)
                if exam_names else "未录入医生检查单，暂不生成检查导航"
            )
        elif s["key"] == "medicine":
            item["poi"] = "1楼西药房取药窗口"
        steps.append(item)
    return {
        "dept": dept,
        "exam_names": exam_names,
        "exam_source": "doctor_order" if exam_names else "none",
        "exam_notice": (
            "以下项目来自医生开具的检查单，请按单办理"
            if exam_names else "请先让医生开具检查单；AI不会根据症状自行安排检查"
        ),
        "exam_prep": preps,
        "steps": steps,
    }


def _chat_navigation(state: JourneyState, user_msg: str, dept: dict | None) -> dict | None:
    """为聊天中的地点问题生成可执行的院内导航动作。"""
    text = user_msg.strip().lower()
    if any(word in text for word in ("挂号", "预约")):
        if dept:
            target, label = _resolve_nav("@register", "挂号收费处", dept, [])
            floor = dept.get("floor")
        else:
            target, label, floor = "1f_poi_cfy1", "挂号收费处", 1
        return {
            "kind": "register",
            "target": target,
            "label": label,
            "start": "主入口",
            "notice": f"请先到{floor}楼{label}办理挂号，点击下方按钮查看路线。",
        }

    step = state.current_step()
    if dept and (
        any(word in text for word in ("候诊", "签到", "怎么走", "在哪里", "在哪"))
        or step["key"] in ("checkin", "first_visit")
    ):
        return {
            "kind": "department",
            "target": dept["nav_node_id"],
            "label": dept["name"],
            "start": "主入口",
            "notice": "请到科室外的候诊区签到，坐下静候叫号，叫到号后再进入诊室。",
        }
    return None


def chat_reply(state: JourneyState, user_msg: str) -> dict:
    """对话主入口: 识别步骤推进指令, 自动导诊匹配科室, 其余交给大模型用大白话回答。"""
    command = _detect_command(user_msg)
    is_question = _is_question(user_msg)

    if command == "next":
        state.advance()
    elif command == "back":
        state.back()

    # 聊天模式下没有科室时, 自动从症状匹配科室并推进到第2步
    if not state.dept_id:
        chat_candidates = generate_department_candidates(user_msg, dao.list_departments())
        chat_decision = select_department_candidate(chat_candidates)
        dept_ids = [chat_decision["dept_id"]] if chat_decision.get("dept_id") else []
        if not dept_ids and chat_candidates:
            picked = _llm_pick_department(user_msg, chat_candidates)
            if picked:
                dept_ids = [picked]
        if dept_ids:
            state.dept_id = dept_ids[0]
            state.advance()  # 从第1步(预检分诊)推进到第2步(就诊前准备)

    step = state.current_step()
    dept = dao.get_department(state.dept_id) if state.dept_id else None
    navigation = _chat_navigation(state, user_msg, dept)

    # 没有医生检查单时，AI只能解释流程，不能替患者决定检查项目或目的地。
    if step["key"] == "exam" and not state.exams and any(
        word in user_msg for word in ("检查", "检验", "抽血", "B超", "彩超", "拍片", "CT", "核磁")
    ):
        return {
            "reply": "检查项目和检查地点请以医生实际开具的检查单为准。当前没有录入检查单，我不能根据症状替您安排检查；请先向医生确认。",
            "step": step,
            "state": state.to_dict(),
            "is_question": True,
            "navigation": None,
        }

    # 用药问题使用固定安全回复，避免模型在缺少药名和处方时猜测剂量。
    if _is_medication_question(user_msg):
        return {
            "reply": _medication_reply(dept),
            "step": step,
            "state": state.to_dict(),
            "is_question": True,
        }

    # 如果是问答类问题, 不显示步骤进度, 直接回答
    if is_question:
        context = f"就诊科室: {dept['name']}({dept['floor']}楼)。\n" if dept else ""
        context += "请用简短的大白话直接回答用户的问题, 不要提及步骤进度。"
    else:
        context = f"当前进度: 第{step['index'] + 1}步/共{step['total']}步 {step['title']} - {step['desc']}。\n"
        if dept:
            context += f"就诊科室: {dept['name']}({dept['floor']}楼)。\n"
        context += "本步提示: " + "; ".join(step["tips"])
        if command:
            context += "\n用户刚刚完成了步骤切换, 请用一句话告诉他现在要做什么。"

    try:
        reply = llm_client.chat_with_system(
            SYSTEM_PROMPT,
            context + "\n\n用户说: " + user_msg,
            max_tokens=1024,
        )
        reply = reply.replace("**", "")
    except RuntimeError:
        # README 承诺: 大模型不可用时自动降级为知识库兜底回答, 流程推进不受影响。
        if is_question:
            reply = "这个问题建议您咨询医生或药师, 我可以帮您查看就诊流程。"
        else:
            reply = _fallback_reply(step, dept)

    if navigation and navigation["kind"] == "register":
        reply = navigation["notice"]

    # 如果用户在最后一步说"好了/完成了", 标记就诊结束
    if step["index"] == step["total"] - 1 and command == "next":
        state.finish()

    return {
        "reply": reply,
        "step": step,
        "state": state.to_dict(),
        "is_question": is_question,
        "navigation": navigation,
    }


def _detect_command(msg: str) -> str:
    text = msg.strip()
    if any(w in text for w in _NEXT_WORDS):
        return "next"
    if any(w in text for w in _BACK_WORDS):
        return "back"
    return ""


def _is_question(msg: str) -> bool:
    """判断用户是否在问一个具体问题(而非推进流程)。"""
    text = msg.strip()
    # 包含问号或疑问词
    if "?" in text or "？" in text:
        return True
    # 匹配问答关键词
    return any(kw in text for kw in _QA_KEYWORDS)


def _is_medication_question(msg: str) -> bool:
    """用药问题走确定性安全回复，避免模型猜测剂量或药名。"""
    text = msg.strip().lower()
    medication_words = ("药", "处方", "药袋", "剂量", "用法", "服用", "吃")
    question_words = ("怎么", "如何", "用法", "剂量", "一次", "几次", "吃", "服")
    return any(word in text for word in medication_words) and any(
        word in text for word in question_words
    )


def _medication_reply(dept) -> str:
    dept_name = dept["name"] if dept else "当前科室"
    return (
        f"您当前的就诊科室是{dept_name}。药物请以医生处方和药袋上的用法为准，"
        "我不能仅凭“药怎么吃”判断剂量。请提供药品名称、规格和药袋上的用法，我可以帮您核对说明。"
        "不要自行加量、混用止痛药或提前停药；如果出现面部或喉咙肿胀、呼吸困难、持续出血或高热，请立即就医。"
    )


def _fallback_reply(step: dict, dept) -> str:
    text = f"现在是第{step['index'] + 1}步: {step['title']}。{step['desc']}。"
    if dept:
        text += f"地点在{dept['name']}, {dept['floor']}楼。"
    text += "提示: " + "; ".join(step["tips"]) + "。"
    return text
