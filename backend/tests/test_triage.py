import sys
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend" / "ai_core"))
sys.path.insert(0, str(ROOT / "backend" / "database"))

import dao  # noqa: E402
import guide_engine  # noqa: E402
from process_kb import (  # noqa: E402
    SYMPTOM_MAP,
    detect_urgent_risk,
    generate_department_candidates,
    select_department_candidate,
)


CASES = [
    ("牙疼两天", "kqk"), ("牙龈出血", "kqk"), ("孩子发烧", "erke"),
    ("小儿咳嗽", "erke"), ("高热不退", "grb"), ("一直咳嗽", "nkmz1"),
    ("干咳", "nkmz1"), ("感冒鼻塞", "nkmz1"), ("胸闷心慌", "nkmz1"),
    ("血压高", "nkmz1"), ("拉肚子", "nkmz1"), ("胃痛", "nkmz1"),
    ("恶心想吐", "nkmz1"), ("大便干燥便秘", "nkmz1"), ("头疼", "nkmz2"),
    ("天旋地转", "nkmz2"), ("睡不着", "nkmz2"), ("手脚麻", "nkmz2"),
    ("血糖高", "nkmz2"), ("甲状腺有问题", "nkmz2"), ("眼睛红", "yk"),
    ("视力下降", "yk"), ("耳朵嗡嗡响", "ebhk"), ("鼻出血", "ebhk"),
    ("皮肤瘙痒", "pfk"), ("湿疹", "pfk"), ("荨麻疹过敏", "pfk"),
    ("摔伤了", "wkmz"), ("脚踝扭伤", "wkmz"), ("疑似骨折", "wkmz"),
    ("腰疼", "kftt"), ("膝盖疼", "kftt"), ("怀孕建档", "ckmz"),
    ("孕检产检", "ckmz"), ("月经不调", "fkmz"), ("白带异常", "fkmz"),
    ("单位体检", "pttc"), ("想做胃镜", "xhnj"), ("预约肠镜", "xhnj"),
    ("腹部B超", "csk"), ("心脏彩超", "csk"), ("抽血化验", "jyk"),
    ("查血常规", "jyk"), ("拍胸片", "fs"), ("做CT", "fs"),
    ("核磁检查", "fs"), ("做心电图", "gnjc"), ("想针灸", "zyk"),
    ("肿瘤复查", "zlmz"), ("肾结石", "ssj"), ("去输液", "zsys"),
    ("需要急救", "jzzs"),
    ("浑身没劲", None), ("最近身体不舒服", None), ("不知道看什么科", None),
    ("食欲差", None), ("全身乏力", None), ("想咨询一下", None),
]


def legacy_match(text):
    text = text.lower()
    scores = {}
    for keywords, dept_id in SYMPTOM_MAP:
        hits = sum(1 for keyword in keywords if keyword in text)
        if hits:
            scores[dept_id] = scores.get(dept_id, 0) + hits
    ranked = sorted(scores.items(), key=lambda item: -item[1])
    return ranked[0][0] if ranked else "nkmz1"


class TriageRuleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.departments = dao.list_departments()

    def test_at_least_50_cases_are_defined(self):
        self.assertGreaterEqual(len(CASES), 50)

    def test_case_evaluation_and_baseline(self):
        baseline_correct = 0
        new_correct = 0
        uncertain_correct = 0
        for text, expected in CASES:
            baseline_correct += int(expected is not None and legacy_match(text) == expected)
            candidates = generate_department_candidates(text, self.departments)
            decision = select_department_candidate(candidates)
            actual = decision.get("dept_id")
            new_correct += int(actual == expected)
            uncertain_correct += int(expected is None and decision["status"] == "uncertain")
        self.assertGreaterEqual(new_correct, 45)
        self.assertGreaterEqual(uncertain_correct, 5)
        print({
            "cases": len(CASES),
            "baseline_correct": baseline_correct,
            "new_rule_correct": new_correct,
            "new_uncertain_correct": uncertain_correct,
        })

    def test_conflict_is_uncertain(self):
        candidates = generate_department_candidates("牙疼又胸痛", self.departments)
        decision = select_department_candidate(candidates)
        self.assertEqual(decision["status"], "uncertain")
        self.assertIsNone(decision["dept_id"])

    def test_unknown_does_not_default_to_a_department(self):
        candidates = generate_department_candidates("浑身没劲", self.departments)
        decision = select_department_candidate(candidates)
        self.assertEqual(decision["status"], "uncertain")
        self.assertIsNone(decision["dept_id"])

    def test_invalid_department_ids_are_filtered(self):
        candidates = generate_department_candidates("牙疼", [{"id": "not-real"}])
        self.assertEqual(candidates, [])

    def test_llm_id_name_and_invalid_response(self):
        candidates = generate_department_candidates("牙疼又胸痛", self.departments)
        with patch.object(guide_engine.llm_client, "chat_with_system", return_value="kqk：口腔科"):
            self.assertEqual(guide_engine._llm_pick_department("牙疼又胸痛", candidates), "kqk")
        with patch.object(guide_engine.llm_client, "chat_with_system", return_value="外科"):
            self.assertIsNone(guide_engine._llm_pick_department("牙疼又胸痛", candidates))

    def test_emergency_warning_is_independent(self):
        risk = detect_urgent_risk("剧烈胸痛并伴有冷汗")
        self.assertTrue(risk["is_emergency"])
        self.assertIn("剧烈胸痛", risk["matched_terms"])

    def test_triage_keeps_reasons_and_no_fallback(self):
        with patch.object(guide_engine, "_llm_pick_department", return_value=None) as llm_picker:
            result = guide_engine.triage("浑身没劲")
        self.assertIsNone(result["dept"])
        self.assertEqual(result["status"], "uncertain")
        self.assertIn("无法", result["suggestion"])
        llm_picker.assert_not_called()

    def test_high_confidence_rule_skips_llm(self):
        with patch.object(guide_engine, "_llm_pick_department") as llm_picker:
            result = guide_engine.triage("牙疼两天")
        self.assertEqual(result["dept"]["id"], "kqk")
        llm_picker.assert_not_called()


if __name__ == "__main__":
    unittest.main()
