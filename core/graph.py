"""LangGraph 智能体：DeepSeek LLM 负责理解与表达，本地工具负责精确数据。

图结构：START -> agent（LLM 决定调工具或直接回答）-> tools -> agent ... -> END
"""
from __future__ import annotations

import os
from pathlib import Path

# 对话窗口：最多保留最近 N 条消息（含 user+assistant+tool），防止 token 爆炸
MAX_HISTORY = 20

SYSTEM_PROMPT = """你是材料科学领域的智能助手「材料助手」，面向工程师与学生。

工作规则：
1. 凡涉及具体材料数据（密度、强度、熔点、导热、电阻、价格、成分等），必须调用工具查询本地数据库，禁止凭记忆编造数值。
2. 数据库中没有的材料或数据，要如实告知，可以用材料学知识做定性说明，或建议数据库中性质相近的替代材料。
3. 选材推荐类问题调用 recommend_materials，把用户场景转写为需求关键词（轻量化/高强度/刚度/耐磨/韧性/耐高温/导热/隔热/绝缘/导电/耐腐蚀/便宜 + 可选类别：金属/聚合物/陶瓷/复合材料），如「做飞机机身」→「轻量化 高强度 刚度」。
4. 多材料对比调用 compare_materials；排序/最值/统计调用 rank_or_stats。
5. 概念解释先调用 lookup_term 查本地术语库，未收录再用专业知识回答。
6. 回答使用简体中文，简洁准确，关键数值带单位；工具返回的结果要提炼呈现，不要原样堆砌。
7. 用户问数据库没有的材料（如某牌号钢）时，可调用 list_materials 查看收录范围后再答复。"""


def _load_dotenv() -> None:
    """读取项目根目录 .env（KEY=VALUE），不覆盖已有环境变量。"""
    env_file = Path(__file__).resolve().parent.parent / ".env"
    if not env_file.exists():
        return
    for line in env_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, _, value = line.partition("=")
            os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def get_api_key() -> str | None:
    _load_dotenv()
    return os.environ.get("DEEPSEEK_API_KEY") or None


def _trim_history(messages: list) -> list:
    """裁剪消息历史：保留 SystemMessage + 最近 MAX_HISTORY 条对话消息。

    避免长对话 token 爆炸。ToolMessage 与其对应的 AIMessage（含 tool_calls）
    不会被拆开——如果截断点落在一对中间，向前回退到 AIMessage 之前。
    """
    if not messages:
        return []
    system = []
    rest = messages
    if getattr(messages[0], "type", "") == "system":
        system = [messages[0]]
        rest = messages[1:]
    if len(rest) <= MAX_HISTORY:
        return system + rest
    # 从尾部取最近 MAX_HISTORY 条
    window = rest[-MAX_HISTORY:]
    # 如果窗口第一条是 ToolMessage（它的 AIMessage 被截断了），向后跳过
    while window and getattr(window[0], "type", "") == "tool":
        window = window[1:]
    return system + window


def build_graph():
    """构建并编译智能体图。未配置 DEEPSEEK_API_KEY 时抛出 RuntimeError。"""
    api_key = get_api_key()
    if not api_key:
        raise RuntimeError("未配置 DEEPSEEK_API_KEY")

    from langchain_core.messages import SystemMessage
    from langchain_openai import ChatOpenAI
    from langgraph.graph import END, START, MessagesState, StateGraph
    from langgraph.prebuilt import ToolNode, tools_condition

    from . import tools

    llm = ChatOpenAI(
        model="deepseek-chat",
        api_key=api_key,
        base_url="https://api.deepseek.com",
        temperature=0.3,
    )
    llm_with_tools = llm.bind_tools(tools.TOOLS)

    def agent_node(state: MessagesState) -> dict:
        msgs = state["messages"]
        if not msgs or getattr(msgs[0], "type", "") != "system":
            msgs = [SystemMessage(content=SYSTEM_PROMPT), *msgs]
        return {"messages": [llm_with_tools.invoke(msgs)]}

    builder = StateGraph(MessagesState)
    builder.add_node("agent", agent_node)
    builder.add_node("tools", ToolNode(tools.TOOLS))
    builder.add_edge(START, "agent")
    builder.add_conditional_edges("agent", tools_condition, ["tools", END])
    builder.add_edge("tools", "agent")
    return builder.compile()


def ask(graph, text: str, history: list | None = None):
    """单轮对话：返回 (回答文本, 更新后的完整消息历史)。

    自动裁剪历史窗口防止 token 爆炸。
    """
    from langchain_core.messages import HumanMessage, SystemMessage

    seed = _trim_history(list(history or []))
    if not seed or getattr(seed[0], "type", "") != "system":
        seed = [SystemMessage(content=SYSTEM_PROMPT), *seed]
    seed.append(HumanMessage(content=text))
    state = graph.invoke({"messages": seed})
    msgs = state["messages"]
    reply = msgs[-1].content
    if isinstance(reply, list):  # 兼容 content blocks
        reply = "".join(b.get("text", "") for b in reply if isinstance(b, dict))
    return reply, msgs


def ask_stream(graph, text: str, history: list | None = None):
    """流式对话：逐块 yield 文本片段，最后 yield 更新后的消息历史。

    自动裁剪历史窗口防止 token 爆炸。

    用法：
        for chunk in ask_stream(graph, text, history):
            if isinstance(chunk, str):
                print(chunk, end="", flush=True)
            else:
                history = chunk  # 最后一个 yield 是 list[Message]
    """
    from langchain_core.messages import HumanMessage, SystemMessage

    seed = _trim_history(list(history or []))
    if not seed or getattr(seed[0], "type", "") != "system":
        seed = [SystemMessage(content=SYSTEM_PROMPT), *seed]
    seed.append(HumanMessage(content=text))

    final_msgs: list = []
    for event in graph.stream({"messages": seed}, stream_mode="messages"):
        msg, _node = event
        # 处理 agent 节点的 LLM 流式输出（AIMessageChunk / AIMessage，跳过 ToolMessage）
        if hasattr(msg, "content"):
            tp = getattr(msg, "type", "")
            if tp in ("AIMessageChunk", "AIMessage", "ai"):
                content = msg.content
                if isinstance(content, str) and content:
                    yield content
        final_msgs.append(msg)

    # 汇总最终消息历史
    if final_msgs:
        yield final_msgs
