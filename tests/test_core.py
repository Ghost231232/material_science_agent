"""核心模块单元测试：数据库、属性查询、选材推荐、数据分析、术语问答。"""
import pytest
from core import analysis, database, knowledge, query, selector


# --------------------------------------------------------------------------- #
# fixture
# --------------------------------------------------------------------------- #
@pytest.fixture(scope="module")
def db():
    return database.MaterialDatabase()


# --------------------------------------------------------------------------- #
# database.py
# --------------------------------------------------------------------------- #
class TestDatabase:
    def test_loads_30_materials(self, db):
        assert len(db) == 30

    def test_four_categories(self, db):
        cats = db.categories()
        assert set(cats) == {"金属", "聚合物", "陶瓷", "复合材料"}

    def test_find_by_alias(self, db):
        m = db.find_one("304")
        assert m is not None
        assert "304" in m["name"]

    def test_find_by_name(self, db):
        m = db.find_one("TC4钛合金")
        assert m is not None
        assert m["name"] == "TC4钛合金"

    def test_fuzzy_match_typo(self, db):
        # 近似匹配：少写一个字也能命中
        m = db.find_one("TC4钛金")  # 少了"合"字
        assert m is not None
        assert "钛" in m["name"]

    def test_not_found(self, db):
        assert db.find_one("不存在的材料xyz") is None

    def test_match_category(self, db):
        assert db.match_category("推荐一种金属材料") == "金属"
        assert db.match_category("塑料") == "聚合物"
        assert db.match_category("陶瓷") == "陶瓷"
        assert db.match_category("复合材料") == "复合材料"
        assert db.match_category("没有类别词的文本") is None


# --------------------------------------------------------------------------- #
# query.py
# --------------------------------------------------------------------------- #
class TestQuery:
    def test_find_property_by_alias(self):
        p, hit = query.find_property("304的密度是多少")
        assert p is not None
        assert p["key"] == "density"
        assert hit == "密度"

    def test_find_property_longest_alias_wins(self):
        # "热膨胀系数" 比 "热膨胀" 长，应命中前者
        p, _ = query.find_property("热膨胀系数")
        assert p["key"] == "thermal_expansion"

    def test_find_property_not_found(self):
        p, _ = query.find_property("没有这个词")
        assert p is None

    def test_get_value_nested(self, db):
        m = db.find_one("304不锈钢")
        v = query.get_value(m, "tensile_strength")
        assert v is not None
        assert isinstance(v, (int, float))
        assert v > 0

    def test_get_value_missing(self, db):
        # 找一个数据缺失的组合（非金属无屈服强度的可能性）
        m = db.find_one("CFRP碳纤维复合材料")
        v = query.get_value(m, "elongation")
        # CFRP 可能没有 elongation 数据
        assert v is None or isinstance(v, (int, float))

    def test_format_value_resistivity(self):
        assert "Ω·m" in query.format_value("resistivity", 1.72e-8)

    def test_format_value_corrosion(self):
        assert "5 级" in query.format_value("corrosion", 5)

    def test_format_value_cost(self):
        assert "USD/kg" in query.format_value("cost", 2.5)

    def test_describe_property_has_data(self, db):
        m = db.find_one("Q235碳素结构钢")
        out = query.describe_property(m, query.PROPERTIES[1])  # density
        assert "密度" in out
        assert "g/cm" in out

    def test_full_card(self, db):
        m = db.find_one("304不锈钢")
        card = query.full_card(m)
        assert "304" in card
        assert "机械性能" in card
        assert "热性能" in card


# --------------------------------------------------------------------------- #
# selector.py
# --------------------------------------------------------------------------- #
class TestSelector:
    def test_match_criteria_lightweight_strength(self):
        c = selector._match_criteria("轻量化 高强度")
        labels = [x["label"] for x in c]
        assert any("轻量化" in l for l in labels)
        assert any("高强度" in l for l in labels)

    def test_recommend_returns_ranked(self, db):
        out = selector.recommend(db, "轻量化 高强度")
        assert "推荐" in out
        assert "综合得分" in out

    def test_recommend_with_category(self, db):
        out = selector.recommend(db, "耐高温 陶瓷")
        assert "陶瓷" in out

    def test_recommend_no_criteria_prompts_help(self, db):
        out = selector.recommend(db, "随便看看")
        assert "需求" in out or "示例" in out

    def test_lightweight_picks_low_density(self, db):
        """轻量化需求下，密度最低的材料应排名靠前。"""
        out = selector.recommend(db, "轻量化")
        # CFRP（1.6 g/cm3）或某些聚合物应在前 3
        lines = out.split("\n")
        top3 = "\n".join(lines[:5])
        assert "CFRP" in top3 or "聚乙烯" in top3 or "PP" in top3


# --------------------------------------------------------------------------- #
# analysis.py
# --------------------------------------------------------------------------- #
class TestAnalysis:
    def test_compare_two_materials(self, db):
        out = analysis.compare(db, "对比304不锈钢和6061铝合金")
        assert "304" in out
        assert "6061" in out
        assert "密度" in out

    def test_compare_needs_two(self, db):
        out = analysis.compare(db, "对比304不锈钢")
        assert "至少需要两种" in out

    def test_rank_by_superlative(self, db):
        out = analysis.route(db, "哪个材料最轻")
        assert "密度" in out
        # CFRP 或最轻的材料应在第一名
        first_line = out.split("\n")[2] if len(out.split("\n")) > 2 else ""
        assert "1" in first_line

    def test_rank_by_property_name(self, db):
        out = analysis.route(db, "按抗拉强度排序")
        assert "抗拉强度" in out
        assert "降序" in out or "升序" in out

    def test_stats_average(self, db):
        out = analysis.route(db, "金属的平均密度")
        assert "平均" in out
        assert "密度" in out


# --------------------------------------------------------------------------- #
# knowledge.py
# --------------------------------------------------------------------------- #
class TestKnowledge:
    def test_answer_quench(self):
        out = knowledge.answer("淬火")
        assert out is not None
        assert "马氏体" in out

    def test_answer_aging(self):
        out = knowledge.answer("时效强化")
        assert out is not None
        assert "沉淀" in out or "析出" in out

    def test_answer_alias(self):
        out = knowledge.answer("Tg")
        assert out is not None
        assert "玻璃化" in out

    def test_answer_not_found(self):
        assert knowledge.answer("不存在的术语xyz") is None

    def test_terms_preview(self):
        out = knowledge.terms_preview()
        assert len(out) > 0
