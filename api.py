"""FastAPI 后端接口：让前端直接调用材料科学智能代理。

提供 REST 接口和 WebSocket 流式接口。
"""
from __future__ import annotations

import json
from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from core import database, graph as graph_mod
from core.tools import TOOLS

app = FastAPI(title="材料科学智能选材助手 API", version="1.0")

# 允许前端跨域访问
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

db = database.MaterialDatabase()

# 尝试加载 LLM 图（可能没有 API Key）
_graph = None
_graph_mod = None
try:
    _graph_mod = graph_mod
    _graph = graph_mod.build_graph()
except Exception:
    pass  # 无 Key 或依赖缺失，走规则模式


class Query(BaseModel):
    text: str
    history: list = []


class MaterialQuery(BaseModel):
    material: str
    property: str = ""


@app.get("/api/materials")
def list_materials(category: str = ""):
    """列出数据库中的材料。"""
    if category and any(w in category for w in database.CATEGORY_ALIASES):
        cat = db.match_category(category)
        if cat:
            mats = db.by_category(cat)
            return {"category": cat, "count": len(mats), "materials": [{"name": m["name"], "category": m["category"]} for m in mats]}
    return {"count": len(db), "materials": [{"name": m["name"], "category": m["category"]} for m in db.all()]}


@app.get("/api/materials/{name}")
def get_material(name: str):
    """获取某种材料的完整档案。"""
    from core import query
    m = db.find_one(name)
    if m is None:
        return {"error": f"未找到材料「{name}」"}
    return {"name": m["name"], "data": m}


@app.get("/api/tools")
def list_tools():
    """列出可用工具。"""
    return {"tools": [{"name": t.name, "description": t.description} for t in TOOLS]}


@app.post("/api/chat")
def chat(q: Query):
    """对话接口（非流式）。

    有 DeepSeek Key 时走 LLM，否则走规则引擎。
    """
    if _graph and _graph_mod:
        try:
            reply, _ = _graph_mod.ask(_graph, q.text, q.history)
            return {"reply": reply, "mode": "llm"}
        except Exception as e:
            pass  # 降级规则模式
    # 规则模式
    from agent import respond
    reply = respond(q.text, db)
    return {"reply": reply, "mode": "rules"}


@app.websocket("/ws/chat")
async def ws_chat(ws: WebSocket):
    """WebSocket 流式对话：逐块推送 LLM 输出。

    消息格式：{"text": "用户输入", "history": [...]}
    """
    await ws.accept()
    if not _graph or not _graph_mod:
        # 无 LLM，走规则模式整块返回
        while True:
            try:
                data = await ws.receive_json()
                from agent import respond
                reply = respond(data["text"], db)
                await ws.send_json({"type": "chunk", "content": reply})
                await ws.send_json({"type": "done", "mode": "rules"})
            except WebSocketDisconnect:
                break
        return

    history: list = []
    while True:
        try:
            data = await ws.receive_json()
            text = data.get("text", "")
            history = data.get("history", history)

            # 流式推送
            chunks = []
            for chunk in _graph_mod.ask_stream(_graph, text, history):
                if isinstance(chunk, str):
                    await ws.send_json({"type": "chunk", "content": chunk})
                    chunks.append(chunk)
                else:
                    history = chunk  # 更新历史
            await ws.send_json({"type": "done", "mode": "llm"})
        except WebSocketDisconnect:
            break
        except Exception as e:
            # 降级规则模式
            from agent import respond
            reply = respond(text, db)
            await ws.send_json({"type": "chunk", "content": reply})
            await ws.send_json({"type": "done", "mode": "rules", "error": str(e)})


# 静态文件服务（前端展示站）
site_dir = Path(__file__).parent / "site"
if site_dir.exists():
    app.mount("/", StaticFiles(directory=str(site_dir), html=True), name="site")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)
