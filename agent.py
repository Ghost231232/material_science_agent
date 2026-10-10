"""材料科学智能代理 —— 文本交互入口。

功能：
  1. 材料属性查询（成分/机械/热/电性能）
  2. 应用场景选材推荐
  3. 材料数据对比与统计分析
  4. 材料科学术语与知识问答

两种模式（自动选择）：
  · LLM 模式：配置 DEEPSEEK_API_KEY（环境变量或项目根目录 .env 文件），
    由 DeepSeek + LangGraph 驱动，理解自然语言更灵活；
  · 规则模式：无 Key 或加 --no-llm 参数时，纯本地关键词引擎，离线可用。

用法：
  python agent.py                     # 交互对话（自动选模式）
  python agent.py --no-llm            # 强制纯规则模式
  python agent.py "304不锈钢的密度"   # 单次提问
"""
from __future__ import annotations

import sys

from core import analysis, database, knowledge, query, selector

HELP = """材料科学智能代理 · 功能与示例
──────────────────────────────
1) 属性查询：材料成分、机械/热/电性能一键查询
   「304不锈钢的密度」「TC4的导热系数和熔点」「查一下尼龙66」
2) 选材推荐：按应用场景需求多准则打分排序
   「推荐一种轻量化高强度的材料」「需要耐高温耐腐蚀的陶瓷」
3) 数据分析：多材料对比、属性排序、类别统计
   「对比6061铝合金和T2纯铜」「按抗拉强度排序」「金属的平均密度」
4) 知识问答：材料科学术语解释
   「什么是屈服强度」「解释淬火」「疲劳强度是什么意思」
其他：「材料列表」查看数据库 ｜「术语列表」查看已收录术语 ｜「退出」结束"""

BANNER = "材料科学智能代理已启动（内置 30 种典型材料数据）。输入 help 查看示例，exit 退出。"


def _list_materials(db, text: str) -> str:
    category = db.match_category(text)
    if category:
        mats = db.by_category(category)
        lines = [f"数据库中的{category}类材料（{len(mats)} 种）："]
    else:
        lines = [f"数据库共收录 {len(db)} 种材料："]
        for cat in db.categories():
            mats = db.by_category(cat)
            lines.append(f"◆ {cat}（{len(mats)} 种）")
            lines.append("  " + "、".join(m["name"] for m in mats))
        return "\n".join(lines)
    for m in mats:
        apps = "、".join(m.get("applications", [])[:2])
        lines.append(f"  {m['name']}：{apps}")
    return "\n".join(lines)


def respond(text: str, db: database.MaterialDatabase) -> str:
    """意图路由：一条文本 -> 一段回答。"""
    t = text.strip()
    low = t.lower()
    if not t:
        return ""
    if low in {"exit", "quit", "退出", "再见", "bye", "q"}:
        return "__EXIT__"
    if low in {"help", "帮助", "?", "？", "功能", "说明"}:
        return HELP
    if "术语列表" in t:
        return knowledge.list_terms()
    if "列表" in t or "数据库" in t or "有哪些材料" in t:
        return _list_materials(db, t)

    # 预解析：属性 + 材料（供各意图共用）
    prop, _ = query.find_property(t)
    material = db.find_one(t)
    has_other_intent = any(k in t for k in ["推荐", "选材", "选用", "选择材料", "建议用",
                                            "对比", "比较", "排序", "排名", "最大", "最小",
                                            "最高", "最低", "最轻", "最重", "最硬", "最强",
                                            "最贵", "最便宜", "最耐", "最好", "平均", "统计", "中位数"])

    # 1) 知识问答（术语解释）：同时命中具体材料+属性、或带其他意图时让位
    if not (material and prop) and not has_other_intent:
        ka = knowledge.answer(t)
        if ka:
            return ka

    # 2) 多材料对比
    if any(k in t for k in ["对比", "比较", "比一比", "区别", "差异", "哪个好"]):
        return analysis.compare(db, t)

    # 3) 排序 / 统计
    if has_other_intent and any(k in t for k in ["排序", "排名", "最大", "最小", "最高", "最低",
                                                 "最轻", "最重", "最硬", "最强", "最贵",
                                                 "最便宜", "最耐", "最好", "平均", "统计", "中位数"]):
        return analysis.route(db, t)

    # 4) 选材推荐
    if any(k in t for k in ["推荐", "选材", "选用", "选择材料", "选什么", "建议用",
                            "适合", "什么材料", "哪种材料"]):
        return selector.recommend(db, t)

    # 5) 属性查询 / 材料档案
    if material:
        if prop:
            return query.describe_property(material, prop)
        return query.full_card(material)
    if prop:
        return (f"您想查询「{prop['label']}」，但没识别出材料名称。\n"
                "示例：「304不锈钢的密度」「钛合金的熔点」。输入「材料列表」可查看全部材料。")
    return ("抱歉，我没有理解这个问题。您可以：\n"
            "· 查属性：「304不锈钢的密度」\n"
            "· 选材料：「推荐一种耐高温耐腐蚀的材料」\n"
            "· 问概念：「什么是屈服强度」\n"
            "输入 help 查看完整示例。")


def _build_llm_graph():
    """尝试构建并编译 LLM 图；返回 (图, 图模块, 失败原因)。"""
    try:
        from core import graph as graph_mod

        return graph_mod.build_graph(), graph_mod, None
    except RuntimeError as e:
        return None, None, str(e)
    except ImportError:
        return None, None, "未安装 langgraph/langchain-openai（pip install langgraph langchain-openai），已使用纯规则模式。"


def _run_llm_turn(graph_mod, graph, text: str, history: list) -> tuple[str, list]:
    """LLM 模式一轮对话，异常时回退规则引擎。"""
    try:
        reply, history = graph_mod.ask(graph, text, history)
        return reply, history
    except Exception as e:  # 网络/Key 错误等，降级保底
        err = f"[LLM 调用失败：{e}，本轮已回退规则模式]\n"
        return err + respond(text, db), history


def main() -> None:
    try:
        sys.stdout.reconfigure(errors="replace")
    except Exception:
        pass
    global db
    db = database.MaterialDatabase()

    args = [a for a in sys.argv[1:] if a != "--no-llm"]
    force_rules = "--no-llm" in sys.argv

    graph = None
    mode_note = ""
    if not force_rules:
        graph, graph_mod, reason = _build_llm_graph()
        if graph:
            mode_note = "LLM 模式（DeepSeek + LangGraph）"
        elif reason and "未配置" not in reason:
            mode_note = f"提示：{reason}"
        else:
            mode_note = ("提示：未检测到 DEEPSEEK_API_KEY，当前为纯规则模式。\n"
                         "启用 LLM：在项目根目录创建 .env 文件，写入一行 DEEPSEEK_API_KEY=sk-xxx，重新运行即可。")

    if args:  # 单次提问模式
        if graph:
            out, _ = _run_llm_turn(graph_mod, graph, " ".join(args), [])
        else:
            out = respond(" ".join(args), db)
        print(out)
        return

    banner = [BANNER if not graph else "材料科学智能代理已启动（内置 30 种典型材料数据，DeepSeek 驱动）。输入 help 查看示例，exit 退出。"]
    if mode_note:
        banner.append(mode_note)
    print("\n".join(banner))

    history: list = []
    while True:
        try:
            text = input("材料助手> ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\n再见！")
            break
        if text.lower() in {"exit", "quit", "退出", "再见", "bye", "q"}:
            print("再见！")
            break
        if text.lower() in {"help", "帮助", "?", "？", "功能", "说明"} or not text:
            print(HELP if text else "")
            continue
        if graph:
            out, history = _run_llm_turn(graph_mod, graph, text, history)
        else:
            out = respond(text, db)
        if out == "__EXIT__":
            print("再见！")
            break
        if out:
            print(out)


if __name__ == "__main__":
    main()
