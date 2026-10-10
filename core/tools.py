"""将本地规则引擎封装为 LangChain 工具，供 LLM 智能体调用。

数值全部来自本地数据库/确定性计算，LLM 不直接生成数据，保证不编造。
"""
from __future__ import annotations

from langchain_core.tools import tool

from . import analysis, database, knowledge, query, selector

db = database.MaterialDatabase()


def _all_names() -> str:
    return "、".join(m["name"] for m in db.all())


def _prop_labels() -> str:
    return "、".join(p["label"] for p in query.PROPERTIES)


@tool
def query_material_property(material: str, property: str) -> str:
    """查询某种材料的具体属性数值（来自本地数据库，数值精确可信）。

    Args:
        material: 材料名称，如 "304不锈钢"、"TC4钛合金"、"聚四氟乙烯"
        property: 属性名称，如 "密度"、"抗拉强度"、"屈服强度"、"弹性模量"、"硬度"、
                  "熔点"、"导热系数"、"热膨胀系数"、"最高使用温度"、"电阻率"、
                  "电导率"、"耐腐蚀性"、"价格"、"成分"
    """
    m = db.find_one(material)
    if m is None:
        return f"数据库中未找到材料「{material}」。可用材料：{_all_names()}"
    prop, _ = query.find_property(property)
    if prop is None:
        return f"不支持的属性「{property}」。可查询属性：{_prop_labels()}"
    return query.describe_property(m, prop)


@tool
def get_material_card(material: str) -> str:
    """获取某种材料的完整档案卡：成分 + 机械/热/电性能 + 耐蚀性 + 价格 + 应用。

    Args:
        material: 材料名称，如 "6061铝合金"、"氧化铝陶瓷"
    """
    m = db.find_one(material)
    if m is None:
        return f"数据库中未找到材料「{material}」。可用材料：{_all_names()}"
    return query.full_card(m)


@tool
def recommend_materials(requirements: str) -> str:
    """按应用场景需求做多准则加权评分，推荐最合适的材料（Top 5）。

    Args:
        requirements: 用户的需求描述原文或整理后的关键词，
            如 "轻量化 高强度"、"耐高温 耐腐蚀 陶瓷"、
            "导电好 便宜"。支持需求词：轻量化/高强度/刚度/耐磨/韧性/耐高温/
            导热/隔热/绝缘/导电/耐腐蚀/便宜，可加类别限定：金属/聚合物(塑料)/陶瓷/复合材料
    """
    return selector.recommend(db, requirements)


@tool
def compare_materials(text: str) -> str:
    """对比数据库中 2~4 种材料的各项属性，输出对照表。

    Args:
        text: 包含材料名称的对比请求原文，如 "对比6061铝合金和T2纯铜"
    """
    return analysis.compare(db, text)


@tool
def rank_or_stats(text: str) -> str:
    """按属性对材料排序（最大/最小/最轻/最硬…）或做统计（平均/中位数）。

    Args:
        text: 请求原文，如 "按抗拉强度排序"、"哪个材料最轻"、"金属的平均密度"
    """
    return analysis.route(db, text)


@tool
def lookup_term(term: str) -> str:
    """查询材料科学术语解释（屈服强度、淬火、时效强化、玻璃化转变温度等本地术语库）。

    Args:
        term: 术语名称，如 "屈服强度"、"热膨胀系数"
    """
    a = knowledge.answer(term)
    if a is None:
        return f"术语库未收录「{term}」。已收录：{knowledge.terms_preview()}"
    return a


@tool
def list_materials(category: str = "") -> str:
    """列出数据库中的材料。可按类别过滤：金属/聚合物/陶瓷/复合材料。

    Args:
        category: 类别名称，留空则列出全部并按类别分组
    """
    if category and any(w in category for w in database.CATEGORY_ALIASES):
        cat = db.match_category(category)
        if cat:
            mats = db.by_category(cat)
            return f"{cat}类材料（{len(mats)} 种）：" + "、".join(m["name"] for m in mats)
    lines = [f"数据库共 {len(db)} 种材料："]
    for cat in db.categories():
        mats = db.by_category(cat)
        lines.append(f"◆ {cat}（{len(mats)} 种）：" + "、".join(m["name"] for m in mats))
    return "\n".join(lines)


TOOLS = [query_material_property, get_material_card, recommend_materials,
         compare_materials, rank_or_stats, lookup_term, list_materials]
