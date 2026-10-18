# -*- coding: utf-8 -*-
import re
"""就诊全流程知识库与状态机。

流程推进是确定性的(状态机), 不依赖大模型, 防止 AI 乱编流程。
大模型只负责把步骤翻译成大白话和回答问题。
"""

# 就诊全流程步骤模板: nav_target 是可被 /api/navigate 解析的地点关键词,
# "@dept" 表示去就诊科室, "@register" 表示去当前楼层挂号点,
# "@exam" 表示按检查项目动态决定; nav_label 是给用户看的地点名
PROCESS_STEPS = [
    {"key": "triage", "title": "预检分诊", "desc": "先说说哪里不舒服, 确定挂哪个科",
     "nav_target": "", "nav_label": "", "tips": ["把症状、持续时间想清楚", "有旧病历和检查报告一起带上"]},
    {"key": "prep", "title": "就诊前准备", "desc": "带齐证件, 按医生医嘱确认检查准备事项",
     "nav_target": "", "nav_label": "", "tips": ["带身份证和医保卡", "检查前要求以医生开具的检查单为准", "前一天早点休息"]},
    {"key": "register", "title": "挂号", "desc": "到分层挂号收费处挂号, 或提前手机预约",
     "nav_target": "@register", "nav_label": "挂号收费处", "tips": ["第一次来要先办就诊卡", "不知道挂哪个科可以问导医台"]},
    {"key": "checkin", "title": "到院签到候诊", "desc": "到科室外面的候诊区签到, 坐下静候叫号",
     "nav_target": "@dept", "nav_label": "@dept", "tips": ["候诊室在科室外面, 不要直接进诊室", "留意叫号屏幕和广播, 叫到号再进去"]},
    {"key": "first_visit", "title": "医生首诊", "desc": "向医生说清楚症状, 配合问诊",
     "nav_target": "@dept", "nav_label": "@dept", "tips": ["按时间顺序说症状", "医生开的单子要收好"]},
    {"key": "pay", "title": "缴费", "desc": "拿着检查单或处方先去缴费",
     "nav_target": "划价收费", "nav_label": "收费处", "tips": ["缴费后单据留好", "可以用医保卡或手机支付"]},
    {"key": "exam", "title": "检查检验", "desc": "仅按医生开具的检查单完成检查检验",
     "nav_target": "@exam", "nav_label": "@exam", "tips": ["看清检查单上的楼层和检查前要求", "空腹、憋尿等要求以医生检查单为准"]},
    {"key": "report", "title": "取报告", "desc": "等检查报告出来, 自助机打印或窗口领取",
     "nav_target": "检验科", "nav_label": "取报告处(检验科)", "tips": ["报告一般1-2小时, 具体看检查项目", "取报告小票要收好"]},
    {"key": "second_visit", "title": "复诊看报告", "desc": "带报告回诊室, 让医生看结果",
     "nav_target": "@dept", "nav_label": "@dept", "tips": ["回诊室可能要重新刷号", "把所有报告按顺序放好"]},
    {"key": "final", "title": "终诊结论", "desc": "医生给出诊断结果和治疗方案",
     "nav_target": "@dept", "nav_label": "@dept", "tips": ["听不清就请医生写下来", "问清楚要不要复诊"]},
    {"key": "medicine", "title": "取药用药", "desc": "缴费后到药房取药, 按医嘱服药",
     "nav_target": "西药房取药窗口", "nav_label": "西药房取药窗口", "tips": ["取药时核对姓名和药名", "看清楚怎么吃、吃多久"]},
    {"key": "followup", "title": "复诊安排", "desc": "记好复诊时间, 按时回来",
     "nav_target": "@dept", "nav_label": "@dept", "tips": ["把复诊时间写在日历上", "病情有变化随时来"]},
]

# 症状关键词 -> 科室 id(与 input/database/seed_data.py 的 departments.id 对应)
SYMPTOM_MAP = [
    (["发烧", "发热", "发冷"], "grb"),
    (["咳嗽", "感冒", "嗓子疼", "咽痛", "有痰", "气短", "哮喘"], "nkmz1"),
    (["头痛", "头晕", "失眠", "手麻", "中风"], "nkmz2"),
    (["肚子疼", "胃疼", "胃胀", "拉肚子", "腹泻", "便秘", "恶心", "呕吐", "反酸"], "nkmz1"),
    (["胸闷", "心慌", "胸痛", "血压", "高血压", "心脏"], "nkmz1"),
    (["血糖", "糖尿病", "甲亢", "甲状腺"], "nkmz2"),
    (["牙疼", "牙齿", "拔牙", "补牙", "洗牙", "口腔"], "kqk"),
    (["眼睛", "视力", "看不清", "眼干", "近视"], "yk"),
    (["耳朵", "耳鸣", "鼻炎", "流鼻涕", "打鼾", "喉咙", "咽喉"], "ebhk"),
    (["皮肤", "痒", "疹子", "湿疹", "过敏", "皮炎", "长痘", "荨麻疹"], "pfk"),
    (["外伤", "伤口", "缝合", "拆线", "扭伤", "骨折"], "wkmz"),
    (["腰疼", "腰痛", "颈椎", "肩膀疼", "腿疼", "疼痛", "康复"], "kftt"),
    (["怀孕", "产检", "孕妇", "建档"], "ckmz"),
    (["妇科", "月经", "白带"], "fkmz"),
    (["孩子", "小孩", "宝宝", "儿童", "小儿"], "erke"),
    (["体检", "健康检查", "入学体检"], "pttc"),
    (["胃镜", "肠镜", "胃肠镜"], "xhnj"),
    (["b超", "彩超", "超声"], "csk"),
    (["抽血", "验血", "化验", "查血"], "jyk"),
    (["拍片", "ct", "核磁", "x光", "放射"], "fs"),
    (["心电图", "心电"], "gnjc"),
    (["中医", "调理", "针灸", "推拿"], "zyk"),
    (["肿瘤", "化疗"], "zlmz"),
    (["碎石", "结石"], "ssj"),
    (["打针", "输液", "吊针"], "zsys"),
]

# 导诊规则配置。phrases 是同义词/口语表达，all_of 用于需要组合判断的场景。
# weight 越高表示区分度越高；这些规则只引用系统已有的 departments.id。
SYMPTOM_RULES = [
    {"dept_id": "grb", "phrases": ["发烧", "发热", "高热", "体温高", "体温升高", "烧不退"], "weight": 7},
    {"dept_id": "grb", "phrases": ["寒战", "打冷战", "一阵冷一阵热"], "weight": 6},
    {"dept_id": "nkmz1", "phrases": ["咳嗽", "干咳", "咳得厉害", "咳痰", "有痰"], "weight": 5},
    {"dept_id": "nkmz1", "phrases": ["感冒", "鼻塞", "流鼻涕", "嗓子疼", "咽痛", "喉咙痛"], "weight": 5},
    {"dept_id": "nkmz1", "all_of": ["感冒", "鼻塞"], "phrases": [], "weight": 10},
    {"dept_id": "nkmz1", "phrases": ["咽干", "嗓子干", "喉咙干"], "weight": 4},
    {"dept_id": "nkmz1", "phrases": ["气短", "胸闷", "胸口闷", "心慌", "心悸"], "weight": 6},
    {"dept_id": "nkmz1", "phrases": ["胸痛", "胸口疼", "心脏不舒服"], "weight": 7},
    {"dept_id": "nkmz1", "phrases": ["血压高", "高血压", "血压忽高忽低"], "weight": 7},
    {"dept_id": "nkmz1", "phrases": ["肚子疼", "腹痛", "胃疼", "胃痛", "胃胀", "反酸"], "weight": 6},
    {"dept_id": "nkmz1", "phrases": ["拉肚子", "腹泻", "水样便", "便秘", "大便干"], "weight": 6},
    {"dept_id": "nkmz1", "phrases": ["恶心", "呕吐", "想吐", "吃不下饭"], "weight": 5},
    {"dept_id": "nkmz2", "phrases": ["头痛", "头疼", "头晕", "眩晕", "天旋地转"], "weight": 6},
    {"dept_id": "nkmz2", "phrases": ["失眠", "睡不着", "睡眠不好"], "weight": 5},
    {"dept_id": "nkmz2", "phrases": ["手麻", "脚麻", "肢体麻木", "说话含糊"], "weight": 7},
    {"dept_id": "nkmz2", "phrases": ["记忆力下降", "注意力不集中", "反应变慢"], "weight": 6},
    {"dept_id": "nkmz2", "phrases": ["血糖高", "血糖低", "糖尿病", "尿糖"], "weight": 7},
    {"dept_id": "nkmz2", "phrases": ["甲亢", "甲减", "甲状腺", "脖子粗"], "weight": 7},
    {"dept_id": "kqk", "phrases": ["牙疼", "牙痛", "牙龈肿", "牙龈出血", "牙齿松动"], "weight": 8},
    {"dept_id": "kqk", "phrases": ["拔牙", "补牙", "洗牙", "镶牙", "口腔溃疡"], "weight": 7},
    {"dept_id": "yk", "phrases": ["眼睛疼", "眼睛红", "眼红", "眼干", "眼痒"], "weight": 7},
    {"dept_id": "yk", "phrases": ["视力下降", "看不清", "近视", "飞蚊症", "眼底"], "weight": 7},
    {"dept_id": "yk", "phrases": ["怕光", "畏光", "眼睛流泪"], "weight": 6},
    {"dept_id": "ebhk", "phrases": ["耳朵疼", "耳痛", "耳鸣", "耳朵嗡嗡响", "听不清"], "weight": 7},
    {"dept_id": "ebhk", "phrases": ["鼻炎", "鼻出血", "鼻塞", "打鼾", "喉咙异物"], "weight": 6},
    {"dept_id": "ebhk", "phrases": ["耳闷", "耳堵", "耳朵堵"], "weight": 6},
    {"dept_id": "pfk", "phrases": ["皮肤痒", "瘙痒", "皮疹", "疹子", "湿疹"], "weight": 7},
    {"dept_id": "pfk", "phrases": ["过敏", "荨麻疹", "皮炎", "长痘", "脱发"], "weight": 7},
    {"dept_id": "wkmz", "phrases": ["外伤", "伤口", "割伤", "撞伤", "摔伤"], "weight": 8},
    {"dept_id": "wkmz", "phrases": ["扭伤", "骨折", "脱臼", "缝合", "拆线"], "weight": 8},
    {"dept_id": "kftt", "phrases": ["腰疼", "腰痛", "颈椎疼", "颈椎", "肩膀疼"], "weight": 7},
    {"dept_id": "kftt", "phrases": ["腿疼", "膝盖疼", "关节疼", "康复", "理疗"], "weight": 7},
    {"dept_id": "ckmz", "phrases": ["怀孕", "孕妇", "产检", "孕检", "建档", "胎心"], "weight": 8},
    {"dept_id": "fkmz", "phrases": ["妇科", "月经不调", "月经", "白带", "阴道出血"], "weight": 8},
    {"dept_id": "erke", "phrases": ["孩子", "小孩", "宝宝", "儿童", "小儿", "婴儿"], "weight": 7},
    {"dept_id": "erke", "all_of": ["孩子", "发烧"], "phrases": [], "weight": 12},
    {"dept_id": "erke", "all_of": ["儿童", "发热"], "phrases": [], "weight": 12},
    {"dept_id": "erke", "all_of": ["小儿", "发热"], "phrases": [], "weight": 12},
    {"dept_id": "erke", "all_of": ["小孩", "发热"], "phrases": [], "weight": 12},
    {"dept_id": "erke", "all_of": ["宝宝", "发热"], "phrases": [], "weight": 12},
    {"dept_id": "erke", "all_of": ["宝宝", "咳嗽"], "phrases": [], "weight": 12},
    {"dept_id": "pttc", "phrases": ["体检", "健康检查", "入学体检", "单位体检"], "weight": 8},
    {"dept_id": "xhnj", "phrases": ["胃镜", "肠镜", "胃肠镜", "无痛胃镜", "做镜子"], "weight": 9},
    {"dept_id": "csk", "phrases": ["b超", "彩超", "超声", "腹部超声", "心脏彩超"], "weight": 9},
    {"dept_id": "jyk", "phrases": ["抽血", "验血", "化验", "查血", "血常规"], "weight": 8},
    {"dept_id": "fs", "phrases": ["拍片", "x光", "胸片", "ct", "核磁", "磁共振"], "weight": 8},
    {"dept_id": "gnjc", "phrases": ["心电图", "心电", "动态心电", "肺功能"], "weight": 8},
    {"dept_id": "zyk", "phrases": ["中医", "调理", "针灸", "推拿", "拔罐"], "weight": 8},
    {"dept_id": "zlmz", "phrases": ["肿瘤", "化疗", "放疗", "肿块"], "weight": 8},
    {"dept_id": "ssj", "phrases": ["碎石", "结石", "肾结石", "尿路结石"], "weight": 8},
    {"dept_id": "zsys", "phrases": ["打针", "输液", "吊针", "静脉滴注"], "weight": 8},
    {"dept_id": "jzzs", "phrases": ["急诊", "急救", "紧急处理"], "weight": 10},
]

EMERGENCY_RULES = [
    ("呼吸困难", "出现呼吸困难，请立即前往急诊或拨打120"),
    ("喘不上气", "出现喘不上气，请立即前往急诊或拨打120"),
    ("嘴唇发紫", "出现嘴唇发紫，请立即前往急诊或拨打120"),
    ("意识不清", "出现意识不清，请立即前往急诊或拨打120"),
    ("昏迷", "出现昏迷，请立即前往急诊或拨打120"),
    ("抽搐", "出现抽搐，请立即前往急诊或拨打120"),
    ("突然晕倒", "出现突然晕倒，请立即前往急诊或拨打120"),
    ("剧烈胸痛", "出现剧烈胸痛，请立即前往急诊或拨打120"),
    ("胸痛伴冷汗", "出现胸痛伴冷汗，请立即前往急诊或拨打120"),
    ("大量出血", "出现大量出血，请立即前往急诊或拨打120"),
    ("呕血", "出现呕血，请立即前往急诊或拨打120"),
    ("黑便", "出现黑便，请立即前往急诊"),
    ("喉咙肿呼吸", "出现喉咙肿胀并影响呼吸，请立即前往急诊或拨打120"),
    ("高热惊厥", "出现高热惊厥，请立即前往急诊或拨打120"),
]

_GENERIC_PROFILE_TERMS = {"科", "门诊", "检查", "治疗", "疾病", "医院", "患者", "就诊"}


def _normalize_symptom_text(text: str) -> str:
    text = str(text or "").strip().lower()
    return re.sub(r"[\s,，。；;、!！?？:：()（）\[\]【】/\\_-]+", "", text)


def detect_urgent_risk(symptom_text: str) -> dict:
    """独立识别急症风险，不改变普通科室候选。"""
    text = _normalize_symptom_text(symptom_text)
    matched = [(term, message) for term, message in EMERGENCY_RULES if _normalize_symptom_text(term) in text]
    return {
        "is_emergency": bool(matched),
        "level": "emergency" if matched else "none",
        "matched_terms": [term for term, _ in matched],
        "message": matched[0][1] if matched else "",
    }


def generate_department_candidates(symptom_text: str, departments: list = None) -> list:
    """生成可解释的科室候选；接口独立，未来可替换为向量/Embedding 检索。"""
    text = _normalize_symptom_text(symptom_text)
    if not text:
        return []
    valid_ids = {d["id"] for d in departments} if departments else None
    scores = {}

    def entry(dept_id):
        if valid_ids is not None and dept_id not in valid_ids:
            return None
        return scores.setdefault(dept_id, {"dept_id": dept_id, "score": 0.0, "matched_terms": [], "reasons": []})

    for rule in SYMPTOM_RULES:
        item = entry(rule["dept_id"])
        if item is None:
            continue
        all_of = [_normalize_symptom_text(p) for p in rule.get("all_of", [])]
        phrases = [_normalize_symptom_text(p) for p in rule.get("phrases", [])]
        if all_of and all(p and p in text for p in all_of):
            item["score"] += float(rule["weight"])
            item["matched_terms"].extend(rule["all_of"])
            item["reasons"].append("组合命中: " + " + ".join(rule["all_of"]))
        else:
            hits = [original for original, normalized in zip(rule.get("phrases", []), phrases) if normalized and normalized in text]
            if hits:
                item["score"] += float(rule["weight"]) + max(0, len(hits) - 1) * 0.5
                item["matched_terms"].extend(hits)
                item["reasons"].append("症状命中: " + "、".join(hits))

    # 规则没有命中时，利用真实科室的名称、别名、简介和提示做低权重候选召回。
    if departments:
        for dept in departments:
            item = entry(dept["id"])
            if item is None:
                continue
            raw_profile = "|".join(str(dept.get(k) or "") for k in ("name", "aliases", "intro", "tips", "common_exams"))
            profile_terms = [p.strip() for p in re.split(r"[,，、;；|/]", raw_profile) if p.strip()]
            hits = []
            for term in profile_terms:
                normalized = _normalize_symptom_text(term)
                if len(normalized) >= 2 and normalized not in _GENERIC_PROFILE_TERMS and normalized in text:
                    hits.append(term)
            if hits:
                item["score"] += min(3.0, 1.0 + 0.5 * len(hits))
                item["matched_terms"].extend(hits)
                item["reasons"].append("科室资料命中: " + "、".join(hits[:3]))

    candidates = [item for item in scores.values() if item["score"] > 0]
    candidates.sort(key=lambda item: (-item["score"], item["dept_id"]))
    for index, item in enumerate(candidates):
        item["rank"] = index + 1
        item["score"] = round(item["score"], 2)
    return candidates


def select_department_candidate(candidates: list, min_score: float = 4.0, min_margin: float = 2.0) -> dict:
    """从候选中做保守选择；接口独立，便于未来替换排序/检索实现。"""
    if not candidates:
        return {"status": "uncertain", "dept_id": None, "reason": "没有足够匹配依据"}
    top = candidates[0]
    if top["score"] < min_score:
        return {"status": "uncertain", "dept_id": None, "reason": "匹配依据不足"}
    if len(candidates) > 1 and top["score"] - candidates[1]["score"] < min_margin:
        return {"status": "uncertain", "dept_id": None, "reason": "多个科室匹配接近"}
    return {"status": "confident", "dept_id": top["dept_id"], "reason": "最高分且与下一候选有明显差距"}


class JourneyState:
    """就诊流程状态机。步骤推进完全确定, 不经过大模型。"""

    def __init__(self, dept_id: str = "", exams: list = None, start_key: str = ""):
        self.dept_id = dept_id
        self.exams = exams or []
        self.current = 0
        self.done_keys: list = []
        self.finished = False
        if start_key:
            self.current = next(
                (index for index, step in enumerate(PROCESS_STEPS) if step["key"] == start_key),
                0,
            )
            self.done_keys = [step["key"] for step in PROCESS_STEPS[:self.current]]

    def current_step(self) -> dict:
        step = dict(PROCESS_STEPS[self.current])
        step["index"] = self.current
        step["total"] = len(PROCESS_STEPS)
        return step

    def advance(self) -> dict:
        if self.current < len(PROCESS_STEPS) - 1:
            self.done_keys.append(PROCESS_STEPS[self.current]["key"])
            self.current += 1
        return self.current_step()

    def back(self) -> dict:
        if self.current > 0:
            self.current -= 1
            if self.done_keys and self.done_keys[-1] == PROCESS_STEPS[self.current]["key"]:
                self.done_keys.pop()
        return self.current_step()

    def jump_to(self, key: str) -> dict:
        for i, s in enumerate(PROCESS_STEPS):
            if s["key"] == key:
                self.current = i
                return self.current_step()
        return self.current_step()

    def finish(self):
        """标记本次就诊完成。"""
        current_key = PROCESS_STEPS[self.current]["key"]
        if current_key not in self.done_keys:
            self.done_keys.append(current_key)
        self.finished = True

    def is_finished(self) -> bool:
        return self.finished

    def to_dict(self) -> dict:
        return {"dept_id": self.dept_id, "exams": self.exams,
                "current": self.current, "done_keys": self.done_keys,
                "finished": self.finished}

    def to_json(self) -> str:
        import json
        return json.dumps(self.to_dict(), ensure_ascii=False)

    @classmethod
    def from_dict(cls, d: dict) -> "JourneyState":
        state = cls(d.get("dept_id", ""), d.get("exams", []))
        state.current = int(d.get("current", 0))
        state.done_keys = list(d.get("done_keys", []))
        state.finished = bool(d.get("finished", False))
        return state

    @classmethod
    def from_json(cls, text: str) -> "JourneyState":
        import json
        return cls.from_dict(json.loads(text or "{}"))


def match_departments(symptom_text: str) -> list:
    """兼容旧调用方，返回规则候选 ID 排名。"""
    return [item["dept_id"] for item in generate_department_candidates(symptom_text)]
