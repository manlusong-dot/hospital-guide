# 医院就医陪伴小程序（深圳大学医院）

AI 软件开发大赛项目：面向中老年人和儿童家长的就医全流程陪伴助手。智能导诊、就诊流程卡、院内导航（平面图画路线）、用药与检查须知、AI 大白话答疑、挂号演示。

## 目录结构


```
医院辅助/
├── backend/        后端（服务端全部代码）
│   ├── api/        FastAPI 服务（19 个 REST 接口）
│   ├── database/   SQLite：schema.sql / seed_data.py / init_db.py / dao.py
│   ├── data_source/  平面图、路网标注、爬取的医生数据（换医院只改这里）
│   ├── ai_core/    就诊流程状态机 + 导诊 + 大模型封装
│   ├── navigation/ Dijkstra 多楼层寻路（移植 simpleroutingsvg 思路）
│   ├── crawler/    医生数据爬取脚本
│   └── .env        大模型配置（不入库,见 .env.example）
├── frontend/       前端
│   ├── admin/      Vue 管理端与平面图路网标注工具
│   └── miniprogram/ 微信小程序（原生,7 页面,适老化 UI）
├── backend/output/ 输出桥接与下游事件落盘
├── README.md
└── .gitignore
```

## 环境要求

- Python 3.10+
- 微信开发者工具（稳定版）
- Ollama（本地大模型运行环境）或任意 OpenAI 兼容的大模型 API

## 快速开始

1. **安装依赖**
   ```
   cd 医院辅助
   python -m pip install -r backend/api/requirements.txt
   ```

2. **配置大模型**：
   - **本地 Ollama（推荐）**：安装 Ollama → 运行 `ollama pull qwen2.5:7b` → 启动 `ollama serve`。将 `backend/.env.example` 复制为 `backend/.env`，默认配置地址为 `http://127.0.0.1:11434/v1`。
   - **云端 API**：编辑 `backend/.env`，填入你的 base_url / api_key / model（支持任意 OpenAI 兼容接口）。

3. **初始化数据库**（可重复执行，每次重建）
   ```
   python backend/database/init_db.py
   ```
   成功会打印各表行数，并提示"科室路网节点校验通过"。

4. **启动后端**
   请在项目根目录（也就是包含 `backend/`、`frontend/` 的“医院辅助”目录）执行：
   ```
   python -m uvicorn backend.api.main:app --reload
   ```
   看到 `Uvicorn running on http://127.0.0.1:8000` 即成功。接口文档在 http://127.0.0.1:8000/docs 。

   如果当前已经进入了 `backend/` 目录，请先返回项目根目录再启动：
   ```
   cd ..
   python -m uvicorn backend.api.main:app --reload
   ```
   否则 Python 找不到顶层模块 `backend`，会报 `ModuleNotFoundError: No module named 'backend'`。

5. **打开小程序**：微信开发者工具 → 导入项目 → 选 `frontend/miniprogram/` 目录 → AppID 用测试号或填自己的 → 编译运行。后端地址在 `frontend/miniprogram/utils/config.js`（默认 127.0.0.1:8000，真机预览时改成电脑局域网 IP）。

## 测试

```
python -m unittest discover -s backend/tests -p "test_*.py"
```

需要验证 AI 对话接口时，再按 `backend/tests/chat_smoke.py` 中的说明配置模型服务后运行：

```
python backend/tests/chat_smoke.py
```

## 换一家医院

1. 平面图放 `backend/data_source/floor_maps/`（floor1.jpg 起）；
2. 浏览器打开 `frontend/admin/public/map-annotator.html`，逐层标注节点/连线，导出 JSON 放 `backend/data_source/nav_data/`；
3. 改 `backend/database/seed_data.py`（科室/检查须知/用药常识/医生），跑 `init_db.py`。
   `backend/` 其余代码与 `frontend/miniprogram/` 的代码不用动。

## 下游模块对接

系统产出（导诊结果/流程卡/导航路线/对话/挂号事件）统一经 `backend/output/bridge.py` 透传，
事件格式见 `backend/output/bridge.py` 中的事件结构。设置环境变量 `NEXT_MODULE_ENDPOINT` 即可实时推送。

## 常见问题

- **启动报 WinError 10013**：8000 端口被占，关掉占用进程或换端口。
- **小程序提示"无法连接服务"**：后端没启动，或 `utils/config.js` 的地址不对。
- **AI 不回答/回答生硬**：检查 `.env` 的 key；大模型不可用时会自动降级为知识库兜底回答，流程推进不受影响。
- **导入开发者工具报 AppID 不存在**：测试号只能在图形界面选，CLI 不支持。

## 致谢

- 寻路设计参考 simpleroutingsvg（SVG 室内地图 + Dijkstra）
- UI 风格参考开源医院挂号模板
- 医生数据来自深圳大学医院公开信息
