"""数据分析模块：多材料对比表、属性排序、类别统计。"""
from __future__ import annotations

import statistics
import unicodedata

from . import query

_COMPARE_KEYS = ["density", "yield_strength", "tensile_strength", "elastic_modulus",
                 "hardness", "elongation", "melting_point", "thermal_conductivity",
                 "thermal_expansion", "max_service_temp", "resistivity", "conductivity",
                 "corrosion", "cost"]

# 口语最高级 -> 属性 + 方向
_SUPERLATIVE = [
    ("最轻", "density", "asc"), ("最重", "density", "desc"),
    ("密度最低", "density", "asc"), ("密度最高", "density", "desc"),
    ("最便宜", "cost", "asc"), ("最贵", "cost", "desc"),
    ("最硬", "hardness", "desc"), ("最强", "tensile_strength", "desc"),
    ("强度最高", "tensile_strength", "desc"), ("最耐热", "max_service_temp", "desc"),
    ("最耐高温", "max_service_temp", "desc"), ("最导电", "conductivity", "desc"),
]


def _width(s: str) -> int:
    """按显示宽度计算（全角字符记 2）。"""
    return sum(2 if unicodedata.east_asian_width(c) in "WF" else 1 for c in s)


def _pad(s: str, width: int) -> str:
    return str(s) + " " * max(0, width - _width(str(s)))


def _direction(text: str) -> str:
    if any(k in text for k in ["最小", "最低", "最轻", "从小到大", "升序", "最便宜"]):
        return "asc"
    return "desc"


def compare(db, text: str) -> str:
    mats = db.find_materials(text)
    if len(mats) < 2:
        one = mats[0] if mats else db.find_one(text)
        return (f"对比至少需要两种材料，我只识别到：{one['name'] if one else '（无）'}。\n"
                "示例：「对比6061铝合金和T2纯铜的密度与强度」")
    mats = mats[:4]
    header = [_pad("属性", 12)] + [_pad(m["name"], max(16, _width(m["name"]) + 2)) for m in mats]
    lines = ["｜".join(header)]
    for key in _COMPARE_KEYS:
        row = [_pad(query.PROP_BY_KEY[key]["label"], 12)]
        for m in mats:
            v = query.get_value(m, key)
            row.append(_pad(query.format_value(key, v) if v is not None else "—",
                            max(16, _width(m["name"]) + 2)))
        lines.append("｜".join(row))
    lines.append("")
    lines.append("注：数值为典型值；“—”表示数据库未收录。")
    return "\n".join(lines)


def rank(db, text: str) -> str:
    prop, direction = None, _direction(text)
    for word, key, d in _SUPERLATIVE:
        if word in text:
            prop, direction = query.PROP_BY_KEY[key], d
            break
    if prop is None:
        p, _ = query.find_property(text)
        if p is None:
            known = "、".join(x["label"] for x in query.PROPERTIES)
            return f"请指定要排序的属性。可排序属性：{known}\n示例：「按密度排序」「哪个材料导电性最好」"
        prop = p
    category = db.match_category(text)
    candidates = db.by_category(category) if category else db.all()
    ranked = [(query.get_value(m, prop["key"]), m) for m in candidates]
    ranked = [(v, m) for v, m in ranked if v is not None]
    ranked.sort(key=lambda x: x[0], reverse=(direction == "desc"))
    if not ranked:
        return f"「{prop['label']}」在候选材料中暂无数据。"
    scope = f"（范围：{category}类，共 {len(ranked)} 种有数据）" if category else f"（共 {len(ranked)} 种有数据）"
    lines = [f"按{prop['label']}{'升序' if direction == 'asc' else '降序'}排列{scope}：", ""]
    for i, (v, m) in enumerate(ranked[:8], 1):
        lines.append(f"{i:>2}. {m['name']}：{query.format_value(prop['key'], v)}")
    if len(ranked) > 8:
        lines.append(f"…… 其余 {len(ranked) - 8} 种略。")
    return "\n".join(lines)


def stats(db, text: str) -> str:
    p, _ = query.find_property(text)
    if p is None:
        known = "、".join(x["label"] for x in query.PROPERTIES)
        return f"请指定要统计的属性。可统计属性：{known}\n示例：「金属的平均密度」「陶瓷的硬度统计」"
    category = db.match_category(text)
    candidates = db.by_category(category) if category else db.all()
    values = [query.get_value(m, p["key"]) for m in candidates]
    values = [v for v in values if v is not None]
    if not values:
        return f"「{p['label']}」暂无统计数据。"
    scope = f"{category}类" if category else "全部材料"
    mean = statistics.mean(values)
    med = statistics.median(values)
    lines = [f"{scope}{p['label']}统计（n={len(values)}）：",
             f"  最小值 {query.format_value(p['key'], min(values))}",
             f"  最大值 {query.format_value(p['key'], max(values))}",
             f"  平均值 {query.format_value(p['key'], round(mean, 3))}",
             f"  中位数 {query.format_value(p['key'], round(med, 3))}"]
    return "\n".join(lines)


def route(db, text: str) -> str:
    """排序/统计入口：含 平均/统计 走统计，否则走排序。"""
    if any(k in text for k in ["平均", "统计", "中位数", "分布"]):
        return stats(db, text)
    return rank(db, text)
