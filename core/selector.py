"""选材推荐引擎：解析应用场景需求，对材料多准则加权打分排序。"""
from __future__ import annotations

import math

from . import query

# 评价准则：需求关键词 -> 属性 + 方向 + 权重
CRITERIA = [
    {"label": "轻量化（低密度）", "keywords": ["轻量化", "重量轻", "轻", "减重", "自重"], "prop": "density", "better": "min", "weight": 3, "log": False},
    {"label": "高强度", "keywords": ["高强度", "强度", "承重", "结实", "受力", "载荷", "结构"], "prop": "tensile_strength", "better": "max", "weight": 3, "log": False},
    {"label": "高刚度", "keywords": ["刚度", "刚性", "不易变形"], "prop": "elastic_modulus", "better": "max", "weight": 2, "log": False},
    {"label": "高硬度耐磨", "keywords": ["耐磨", "硬度高", "硬"], "prop": "hardness", "better": "max", "weight": 2, "log": False},
    {"label": "韧性好（抗冲击）", "keywords": ["韧性", "抗冲击", "耐撞", "不易碎"], "prop": "elongation", "better": "max", "weight": 2, "log": False},
    {"label": "耐高温", "keywords": ["耐高温", "高温", "耐热", "防火"], "prop": "max_service_temp", "better": "max", "weight": 3, "log": False},
    {"label": "导热好（散热）", "keywords": ["导热", "散热", "热交换", "换热"], "prop": "thermal_conductivity", "better": "max", "weight": 3, "log": False},
    {"label": "保温隔热", "keywords": ["保温", "隔热", "绝热"], "prop": "thermal_conductivity", "better": "min", "weight": 3, "log": False},
    {"label": "电绝缘", "keywords": ["绝缘", "不导电"], "prop": "resistivity", "better": "max", "weight": 3, "log": True},
    {"label": "导电好", "keywords": ["导电"], "prop": "conductivity", "better": "max", "weight": 3, "log": False},
    {"label": "耐腐蚀", "keywords": ["耐腐蚀", "耐蚀", "防锈", "防腐", "化学介质", "酸碱", "海水"], "prop": "corrosion", "better": "max", "weight": 3, "log": False},
    {"label": "低成本", "keywords": ["便宜", "低成本", "经济", "廉价", "性价比", "省钱", "成本"], "prop": "cost", "better": "min", "weight": 2, "log": False},
]

_DEMAND_EXAMPLE = ("示例：「推荐一种轻量化高强度的材料」「需要耐高温耐腐蚀的陶瓷」\n"
                   "可表达的需求：轻量化 / 高强度 / 刚度 / 耐磨 / 韧性 / 耐高温 / 导热 / 隔热 / "
                   "绝缘 / 导电 / 耐腐蚀 / 便宜，并可限定 金属/聚合物/陶瓷/复合材料")


def _match_criteria(text: str) -> list[dict]:
    matched: list[dict] = []
    for c in CRITERIA:
        if any(k in text for k in c["keywords"]) and c not in matched:
            matched.append(c)
    return matched


def _score(criterion: dict, candidates: list[dict]) -> dict[str, float]:
    """对某一准则把所有候选归一化到 [0,1]。缺失数据记 0 分。"""
    values = {}
    for m in candidates:
        v = query.get_value(m, criterion["prop"])
        if v is not None:
            values[id(m)] = v if not criterion["log"] else math.log10(max(v, 1e-30))
    result = {id(m): 0.0 for m in candidates}
    if not values:
        return result
    lo, hi = min(values.values()), max(values.values())
    if hi == lo:
        for k in values:
            result[k] = 1.0
        return result
    for m in candidates:
        v = values.get(id(m))
        if v is None:
            continue
        if criterion["better"] == "max":
            result[id(m)] = (v - lo) / (hi - lo)
        else:
            result[id(m)] = (hi - v) / (hi - lo)
    return result


def recommend(db, text: str) -> str:
    criteria = _match_criteria(text)
    category = db.match_category(text)

    if not criteria:
        if category:
            mats = db.by_category(category)
            lines = [f"您提到「{category}」类材料，数据库中共 {len(mats)} 种：",
                     "、".join(m["name"] for m in mats), "", "请补充使用需求（如强度、耐温、成本等），我再为您精准推荐。",
                     _DEMAND_EXAMPLE]
            return "\n".join(lines)
        return "请描述一下使用场景和性能需求。\n" + _DEMAND_EXAMPLE

    candidates = db.by_category(category) if category else db.all()
    # 计算加权综合得分
    total = {id(m): 0.0 for m in candidates}
    weight_sum = 0.0
    for c in criteria:
        s = _score(c, candidates)
        w = c["weight"]
        weight_sum += w
        for m in candidates:
            total[id(m)] += w * s[id(m)]
    for m in candidates:
        total[id(m)] /= weight_sum

    ranked = sorted(candidates, key=lambda m: -total[id(m)])[:5]
    scope = f"「{category}」类 {len(candidates)} 种材料" if category else f"全部 {len(candidates)} 种材料"

    lines = [f"根据需求【{' + '.join(c['label'] for c in criteria)}】，"
             f"已在{scope}中评分排序，推荐如下（满分 100）：", ""]
    for i, m in enumerate(ranked, 1):
        score = round(total[id(m)] * 100)
        bar = "█" * max(1, round(score / 10)) if score > 0 else "▏"
        lines.append(f"{i}. {m['name']}（{m['category']}）  综合得分 {score}  {bar}")
        detail = []
        for c in criteria:
            v = query.get_value(m, c["prop"])
            if v is not None:
                arrow = "↓越低越好" if c["better"] == "min" else "↑越高越好"
                detail.append(f"{query.PROP_BY_KEY[c['prop']]['label']} {query.format_value(c['prop'], v)}（{arrow}）")
        if detail:
            lines.append("   • " + "；".join(detail))
        apps = m.get("applications", [])
        if apps:
            lines.append(f"   • 典型应用：{'、'.join(apps[:3])}")
    lines.append("")
    lines.append("提示：以上为基于典型值的初步推荐，工程应用请结合工艺性、疲劳/冲击工况与标准规范进一步验证。")
    return "\n".join(lines)
