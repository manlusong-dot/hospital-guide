# 症状导诊功能优化报告

## 修改范围

- `backend/ai_core/process_kb.py`
  - 保留原有 `SYMPTOM_MAP` 兼容接口。
  - 新增 52 组可维护的 `SYMPTOM_RULES`，覆盖儿童发热、呼吸道、消化、神经内科、口腔、眼科、耳鼻喉、皮肤、外伤、康复、妇产科、检查检验等常见表达及组合症状。
  - 新增 `generate_department_candidates()` 候选生成接口。
  - 新增 `select_department_candidate()` 保守选择接口。
  - 新增 `detect_urgent_risk()` 独立急症风险提示接口。
  - 候选科室 ID 通过现有数据库科室列表过滤，不接受虚构 ID。

- `backend/ai_core/guide_engine.py`
  - `triage()` 改为规则候选优先、分数足够且拉开差距时直接选择。
  - 候选不足或分数接近时才调用现有 LLM。
  - LLM 只能从已召回的真实候选 ID 中选择，支持 `id`、`id:name`、`id：name` 格式；非法 ID 和无法解析结果均丢弃。
  - 删除无依据时默认推荐内科一区的行为，改为返回不确定提示和候选。
  - 返回 `status`、`confidence`、`candidates`、`match_reasons`、`urgent_warning`，方便演示和排查。

- `backend/api/guide.py`
  - 将候选、匹配理由和急症提示写入导诊事件。

- `frontend/miniprogram/pages/chat/chat.js`、`chat.wxml`、`chat.wxss`
  - 支持候选接近时人工选择。
  - 无确定科室时隐藏“生成流程卡/带我去”按钮。
  - 独立显示急症提示。

- `backend/tests/test_triage.py`
  - 新增 58 条离线样本和 9 个测试场景，覆盖明确命中、同义表达、无依据、冲突、非法科室 ID、LLM 解析失败、`id:name` 解析和急症提示。

## 实现逻辑

1. 对输入做大小写、空格和常用标点归一化。
2. 先按规则短语和组合症状计分，并记录命中的词语和理由。
3. 再用系统已有科室名称、别名、简介、提示和常见项目做低权重补充召回。
4. 候选最高分达到阈值且与第二名有足够差距时确定推荐；否则保留不确定状态。
5. 只有存在候选但无法确定时才调用 LLM，并限制在候选 ID 内选择。
6. 急症风险单独识别，普通科室结果不会覆盖急症提示。

## 测试结果

执行命令：

```text
python -m unittest discover -s backend/tests -v
```

结果：9 项测试通过，样本数 58。

- 修改前基线：38/58 条按原 `SYMPTOM_MAP` 的字符串包含和无命中默认逻辑复现得到；当前项目没有历史线上标注日志，因此这不是线上真实准确率。
- 修改后规则评分：58/58 条得到预期结果。
- 无明确科室依据的 6 条样本均保持不确定，不再默认推荐内科一区。
- 结果仅代表当前手工样本集，不代表真实人群准确率，也不宣称泛化提升。

同时通过 Python 编译检查、JavaScript 语法检查和后端路由导入检查。

## 已知限制

- 规则仍依赖人工维护，罕见病、复杂病史和跨专科症状可能进入不确定态。
- “系统科室描述”仅做低权重召回，不能替代医生诊断。
- LLM 候选选择仍可能有偏差，但输出已被真实候选 ID 和不确定分支约束。
- 急症词表是演示级风险提示，不是急诊分诊或医学诊断工具。

## 后续升级方式

可在不改 `triage()` 业务流程的情况下替换 `generate_department_candidates()` 的内部实现，接入经确认许可的数据、Embedding 检索或人工标注规则；保留 `select_department_candidate()` 作为统一的阈值、置信度和人工确认入口。
