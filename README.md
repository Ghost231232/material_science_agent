# 材料科学智能选材助手

基于 **DeepSeek + LangGraph** 的材料科学智能代理系统，面向工程师与学生，提供材料属性查询、场景选材推荐、数据分析对比和术语问答。

## 架构设计

混合架构：LLM 负责自然语言理解，本地规则引擎保证数值精确不编造。

```
用户输入 → LangGraph StateGraph
              └─ agent 节点（DeepSeek，绑定 7 个工具）
                   ↕ tools_condition 循环
              └─ tools 节点（本地确定性引擎）
                    ├ query_material_property / get_material_card
                    ├ recommend_materials（多准则加权评分）
                    ├ compare_materials / rank_or_stats
                    └ lookup_term / list_materials
```

**为什么不纯 LLM？** 材料数据（密度、强度、熔点等）是精确数值，LLM 会"编造"。所有数值来自本地 JSON 数据库，LLM 只负责理解意图和组织回答。

## 功能

| 功能 | 示例 | 实现 |
|------|------|------|
| 属性查询 | "304不锈钢的密度" | 别名匹配 + difflib 近似匹配 |
| 场景选材 | "做飞机机身用什么材料" | 需求关键词提取 → 多准则加权归一评分 |
| 材料对比 | "对比TC4和6061的强度" | 多材料 × 多属性对照表 |
| 排序统计 | "哪个金属导电性最好" | 按属性排序 / 类别统计 |
| 术语问答 | "什么是时效强化" | 39 条材料科学术语库 |

## 快速开始

```bash
# 安装依赖
pip install -r requirements.txt
pip install pytest  # 运行测试

# 纯规则模式（无需 API Key，离线可用）
python agent.py --no-llm

# LLM 模式（需要 DeepSeek API Key）
# 1. 在项目根目录创建 .env 文件
# 2. 写入一行：DEEPSEEK_API_KEY=sk-你的密钥
python agent.py
```

单次提问：
```bash
python agent.py "304不锈钢的密度"
```

## 项目结构

```
material_science/
├── agent.py              # 入口：双模式自动切换
├── requirements.txt      # 依赖清单
├── .env                  # DeepSeek API Key（不入 Git）
├── core/
│   ├── database.py       # 数据库加载 + 类别识别 + 模糊匹配
│   ├── query.py          # 属性注册表 + 查询 + 档案卡生成
│   ├── selector.py       # 多准则加权评分选材引擎
│   ├── analysis.py       # 材料对比 / 排序 / 统计
│   ├── knowledge.py      # 39 条材料科学术语库
│   ├── tools.py          # 核心模块 → LangChain @tool 封装
│   └── graph.py          # LangGraph agent↔tools 循环图
├── data/
│   └── materials.json     # 30 种材料 × 15 项属性
├── tests/
│   └── test_core.py      # 32 个单元测试
└── site/                 # 静态展示站
    └── index.html
```

## 数据覆盖

- **30 种材料**：金属 12 + 聚合物 10 + 陶瓷 5 + 复合材料 3
- **15 项属性**：化学成分、密度、屈服/抗拉强度、弹性模量、硬度、延伸率、熔点、导热系数、热膨胀系数、最高使用温度、电阻率、电导率、耐腐蚀性、参考价格
- **39 条术语**：涵盖力学性能、热处理、物理性质、材料分类等

## 测试

```bash
python -m pytest tests/ -v
```

32 个测试覆盖：数据库加载与模糊匹配、属性查询与格式化、选材评分排序、对比排序统计、术语问答。

## 技术栈

- Python 3.13
- LangGraph 1.x（agent 循环图）
- LangChain（工具定义与调用）
- DeepSeek API（deepseek-chat 模型）
- 纯 Python 规则引擎（零依赖离线模式）
