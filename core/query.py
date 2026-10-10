"""属性查询引擎：解析属性关键词，生成查询结果与材料档案卡。"""
from __future__ import annotations

# 属性注册表：key -> 属性定义（取值路径、单位、中文别名）
PROPERTIES = [
    {"key": "composition", "label": "化学成分", "aliases": ["成分", "化学成分", "组成", "元素组成"], "path": ("composition",), "unit": ""},
    {"key": "density", "label": "密度", "aliases": ["密度"], "path": ("density",), "unit": "g/cm^3"},
    {"key": "yield_strength", "label": "屈服强度", "aliases": ["屈服强度", "屈服极限"], "path": ("mechanical", "yield_strength"), "unit": "MPa"},
    {"key": "tensile_strength", "label": "抗拉强度", "aliases": ["抗拉强度", "拉伸强度", "抗拉"], "path": ("mechanical", "tensile_strength"), "unit": "MPa"},
    {"key": "elastic_modulus", "label": "弹性模量", "aliases": ["弹性模量", "杨氏模量"], "path": ("mechanical", "elastic_modulus"), "unit": "GPa"},
    {"key": "hardness", "label": "硬度", "aliases": ["硬度"], "path": ("mechanical", "hardness"), "unit": "HV"},
    {"key": "elongation", "label": "延伸率", "aliases": ["延伸率", "伸长率"], "path": ("mechanical", "elongation"), "unit": "%"},
    {"key": "melting_point", "label": "熔点", "aliases": ["熔点", "熔化温度"], "path": ("thermal", "melting_point"), "unit": "°C"},
    {"key": "thermal_conductivity", "label": "导热系数", "aliases": ["导热系数", "热导率", "导热"], "path": ("thermal", "thermal_conductivity"), "unit": "W/(m·K)"},
    {"key": "thermal_expansion", "label": "热膨胀系数", "aliases": ["热膨胀系数", "热膨胀", "膨胀系数"], "path": ("thermal", "thermal_expansion"), "unit": "10^-6/K"},
    {"key": "max_service_temp", "label": "最高使用温度", "aliases": ["最高使用温度", "使用温度", "耐温"], "path": ("thermal", "max_service_temp"), "unit": "°C"},
    {"key": "resistivity", "label": "电阻率", "aliases": ["电阻率"], "path": ("electrical", "resistivity"), "unit": "Ω·m"},
    {"key": "conductivity", "label": "电导率", "aliases": ["电导率", "导电性", "导电"], "path": ("electrical", "conductivity_IACS"), "unit": "%IACS"},
    {"key": "corrosion", "label": "耐腐蚀性", "aliases": ["耐腐蚀", "耐蚀性", "抗腐蚀", "耐蚀"], "path": ("corrosion_resistance",), "unit": "级(1-5)"},
    {"key": "cost", "label": "参考价格", "aliases": ["价格", "成本", "费用"], "path": ("cost",), "unit": "USD/kg"},
]

PROP_BY_KEY = {p["key"]: p for p in PROPERTIES}

# 展示用分组档案卡
_CARD_SECTIONS = [
    ("机械性能", ["yield_strength", "tensile_strength", "elastic_modulus", "hardness", "elongation"]),
    ("热性能", ["melting_point", "thermal_conductivity", "thermal_expansion", "max_service_temp"]),
    ("电性能", ["resistivity", "conductivity"]),
]


def find_property(text: str):
    """按别名长度优先匹配属性，返回 (属性定义, 命中别名) 或 (None, None)。"""
    best = (None, None, 0)
    for p in PROPERTIES:
        for a in p["aliases"]:
            if a in text and len(a) > best[2]:
                best = (p, a, len(a))
    if best[0] is None:
        return None, None
    return best[0], best[1]


def get_value(material: dict, prop_key: str):
    """按属性定义从材料数据中取值，缺失返回 None。"""
    spec = PROP_BY_KEY[prop_key]
    node = material
    for k in spec["path"]:
        if not isinstance(node, dict) or node.get(k) is None:
            return None
        node = node[k]
    return node


def format_value(prop_key: str, value) -> str:
    """属性值的展示格式。"""
    if value is None:
        return "—"
    if prop_key == "composition":
        return str(value)
    if prop_key == "resistivity":
        return f"{value:.1e} Ω·m"
    if prop_key == "corrosion":
        return f"{value:g}/5 级"
    if prop_key == "cost":
        return f"≈{value:g} USD/kg"
    if prop_key == "conductivity":
        return f"{value:g} %IACS"
    unit = PROP_BY_KEY[prop_key]["unit"]
    return f"{value:g} {unit}".strip()


def describe_property(material: dict, prop) -> str:
    """单材料单属性的回答。"""
    name = material["name"]
    value = get_value(material, prop["key"])
    if value is None:
        known = "、".join(
            PROP_BY_KEY[k]["label"]
            for k in ["density", "yield_strength", "tensile_strength", "elastic_modulus",
                      "hardness", "elongation", "melting_point", "thermal_conductivity",
                      "thermal_expansion", "max_service_temp", "resistivity",
                      "conductivity", "corrosion", "cost", "composition"]
            if get_value(material, k) is not None
        )
        return f"{name} 的「{prop['label']}」数据缺失。\n可查询属性：{known}"
    line = f"{name} 的{prop['label']}为 {format_value(prop['key'], value)}。"
    if prop["key"] == "conductivity":
        line += "\n（%IACS：以标准退火纯铜为 100% 的相对电导率）"
    elif prop["key"] == "corrosion":
        line += "\n（5 级制：1=差，5=优异）"
    elif prop["key"] == "cost":
        line += "\n（相对参考价，非实时市场价）"
    return line


def full_card(material: dict) -> str:
    """材料的完整档案卡。"""
    aliases = material.get("aliases", [])
    lines = [f"■ {material['name']}" + (f"（别名：{' / '.join(aliases[:4])}）" if aliases else "")]
    tags = [f"类别：{material['category']}"]
    if material.get("condition"):
        tags.append(f"状态：{material['condition']}")
    lines.append("｜".join(tags))
    lines.append(f"化学成分：{material.get('composition', '—')}")
    for title, keys in _CARD_SECTIONS:
        parts = [f"{PROP_BY_KEY[k]['label']} {format_value(k, get_value(material, k))}" for k in keys]
        if any(get_value(material, k) is not None for k in keys):
            lines.append(f"{title}：" + "｜".join(parts))
    lines.append(f"其他：耐腐蚀性 {format_value('corrosion', material['corrosion_resistance'])}｜"
                 f"参考价格 {format_value('cost', material['cost'])}")
    apps = material.get("applications", [])
    if apps:
        lines.append(f"典型应用：{'、'.join(apps)}")
    return "\n".join(lines)
