"""材料数据库：加载、类别识别与材料模糊匹配。"""
from __future__ import annotations

import difflib
import json
from pathlib import Path

DATA_FILE = Path(__file__).resolve().parent.parent / "data" / "materials.json"

# 用户口语 -> 标准材料大类
CATEGORY_ALIASES = {
    "金属": ["金属", "合金", "钢材", "钢", "铁", "铜", "铝", "镁", "钛", "镍"],
    "聚合物": ["聚合物", "塑料", "树脂", "橡胶", "高分子"],
    "陶瓷": ["陶瓷", "玻璃"],
    "复合材料": ["复合材料", "复合", "纤维增强"],
}


def _normalize(s: str) -> str:
    """小写并去除空白，用于匹配。"""
    return "".join(s.lower().split())


class MaterialDatabase:
    def __init__(self, path: Path = DATA_FILE):
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        self.materials = data["materials"]
        self.note = data.get("note", "")

    def __len__(self) -> int:
        return len(self.materials)

    def all(self) -> list[dict]:
        return self.materials

    def categories(self) -> list[str]:
        seen: list[str] = []
        for m in self.materials:
            if m["category"] not in seen:
                seen.append(m["category"])
        return seen

    def by_category(self, category: str) -> list[dict]:
        return [m for m in self.materials if m["category"] == category]

    def match_category(self, text: str) -> str | None:
        """从文本中识别用户提到的材料大类（金属/聚合物/陶瓷/复合材料）。"""
        for cat, words in CATEGORY_ALIASES.items():
            if any(w in text for w in words):
                return cat
        return None

    def find_materials(self, text: str) -> list[dict]:
        """找出文本中提到的所有材料，按命中的别名列名长度降序。"""
        norm = _normalize(text)
        hits: list[tuple[int, str, dict]] = []
        for m in self.materials:
            best_len, best_alias = 0, ""
            for alias in [m["name"], *m.get("aliases", [])]:
                a = _normalize(alias)
                if a and a in norm and len(a) > best_len:
                    best_len, best_alias = len(a), a
            if best_len:
                hits.append((best_len, best_alias, m))
        hits.sort(key=lambda x: -x[0])
        return [m for _, _, m in hits]

    def find_one(self, text: str) -> dict | None:
        """找出文本中提及的最主要材料；未精确命中时做近似匹配（容错错别字）。"""
        found = self.find_materials(text)
        if found:
            return found[0]
        names: list[tuple[str, dict]] = []
        for m in self.materials:
            names.append((_normalize(m["name"]), m))
            for alias in m.get("aliases", []):
                names.append((_normalize(alias), m))
        close = difflib.get_close_matches(
            _normalize(text), [n for n, _ in names], n=1, cutoff=0.6
        )
        if close:
            for n, m in names:
                if n == close[0]:
                    return m
        return None
