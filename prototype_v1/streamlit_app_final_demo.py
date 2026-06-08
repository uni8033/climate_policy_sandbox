from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime
import html
import json
import os
from pathlib import Path
from typing import Callable

try:
    import streamlit as st
except ImportError:  # pragma: no cover
    raise SystemExit("请先安装 streamlit，再运行 streamlit_app_final_demo.py")

from climate_policy_engine import ClimatePolicySandbox, FEATURE_LABELS, FEATURE_ORDER

BASE_DIR = Path(__file__).resolve().parent
SOURCE_CATALOG_PATH = BASE_DIR / "data" / "source_catalog.json"
REAL_WORLD_ENTITIES_PATH = BASE_DIR / "data" / "real_world_entities.json"
REAL_POLICY_PROFILES_PATH = BASE_DIR / "data" / "real_policy_profiles.json"
RESULTS_DIR = BASE_DIR / "results"
RUN_HISTORY_DIR = RESULTS_DIR / "demo_history"
RUN_HISTORY_INDEX_PATH = RESULTS_DIR / "demo_run_history_index.json"
OPENCODE_GO_BASE_URL = "https://opencode.ai/zen/go/v1"
OPENCODE_GO_API_PATH = "chat/completions"
OPENCODE_GO_MODEL = "deepseek-v4-pro"
DEFAULT_POLICY_TEXT = "2035年前在加强森林保护、碳汇和土地利用治理的同时，逐步停止新建无减排措施煤电，并为高脆弱国家提供适应融资与技术转移支持。"

st.set_page_config(
    page_title="气候政策博弈沙盘 Final Showcase",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    .stApp {
        background:
            radial-gradient(circle at top left, rgba(34, 197, 94, 0.07), transparent 26%),
            radial-gradient(circle at top right, rgba(245, 158, 11, 0.08), transparent 24%),
            linear-gradient(180deg, #f7faf8 0%, #eef3ef 100%);
        color: #16232c;
    }
    .block-container {
        max-width: 1380px;
        padding-top: 1.2rem;
        padding-bottom: 2.8rem;
    }
    .hero-shell {
        border-radius: 28px;
        padding: 1.55rem 1.6rem;
        color: #f8fbfa;
        background:
            radial-gradient(circle at 86% 18%, rgba(255, 255, 255, 0.12), transparent 18%),
            linear-gradient(135deg, #102934 0%, #184454 48%, #216c62 100%);
        box-shadow: 0 18px 48px rgba(16, 41, 52, 0.18);
        border: 1px solid rgba(255, 255, 255, 0.10);
        margin-bottom: 1rem;
    }
    .hero-title {
        margin: 0;
        font-size: 2.35rem;
        font-weight: 800;
        letter-spacing: -0.02em;
        color: #ffffff;
    }
    .hero-subtitle {
        margin-top: 0.55rem;
        max-width: 980px;
        font-size: 1.04rem;
        line-height: 1.62;
        color: #e7f4f0;
    }
    .hero-chip-row {
        display: flex;
        flex-wrap: wrap;
        gap: 0.55rem;
        margin-top: 0.95rem;
    }
    .hero-chip {
        display: inline-block;
        padding: 0.35rem 0.7rem;
        border-radius: 999px;
        background: rgba(255, 255, 255, 0.12);
        color: #f3fbf8;
        border: 1px solid rgba(255, 255, 255, 0.14);
        font-size: 0.84rem;
    }
    div[data-testid="stMetric"] {
        background: transparent;
        border: none;
        padding: 0.15rem 0.1rem 0.55rem 0.1rem;
        border-radius: 0;
        box-shadow: none;
        border-bottom: 1px solid rgba(15, 23, 42, 0.08);
    }
    div[data-testid="stMetricLabel"] {
        color: #60707b;
    }
    div[data-testid="stMetricValue"] {
        color: #16232c;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 0.4rem;
        background: rgba(255, 255, 255, 0.72);
        border-radius: 16px;
        padding: 0.2rem;
        border: 1px solid rgba(15, 23, 42, 0.08);
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 12px;
        height: 42px;
        padding-left: 0.95rem;
        padding-right: 0.95rem;
    }
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #e6f4ee 0%, #fbf2de 100%);
    }
    .stTextArea textarea, .stTextInput input {
        border-radius: 14px !important;
    }
    .stButton button[kind="primary"] {
        border-radius: 14px;
        height: 46px;
        font-weight: 700;
    }
    .stExpander {
        background: rgba(255, 255, 255, 0.84);
        border-radius: 16px;
        border: 1px solid rgba(15, 23, 42, 0.08);
    }
    [data-testid="stSidebar"] {
        border-right: 1px solid rgba(15, 23, 42, 0.08);
    }
    [data-testid="stSidebar"] [data-testid="stSidebarContent"] {
        scrollbar-width: thin;
        scrollbar-color: rgba(31, 122, 110, 0.78) rgba(16, 41, 52, 0.08);
    }
    [data-testid="stSidebar"] [data-testid="stSidebarContent"]::-webkit-scrollbar {
        width: 10px;
    }
    [data-testid="stSidebar"] [data-testid="stSidebarContent"]::-webkit-scrollbar-track {
        background: rgba(16, 41, 52, 0.08);
        border-radius: 999px;
    }
    [data-testid="stSidebar"] [data-testid="stSidebarContent"]::-webkit-scrollbar-thumb {
        background: linear-gradient(180deg, #2a7a70 0%, #4d9782 100%);
        border-radius: 999px;
        border: 2px solid rgba(255, 255, 255, 0.72);
    }
    .scroll-panel {
        border: 1px solid rgba(15, 23, 42, 0.10);
        border-radius: 16px;
        background: rgba(255, 255, 255, 0.72);
        padding: 0.9rem 1rem;
        overflow-y: auto;
        white-space: normal;
        line-height: 1.7;
        scrollbar-width: thin;
        scrollbar-color: rgba(31, 122, 110, 0.78) rgba(16, 41, 52, 0.08);
    }
    .scroll-panel::-webkit-scrollbar {
        width: 10px;
    }
    .scroll-panel::-webkit-scrollbar-track {
        background: rgba(16, 41, 52, 0.08);
        border-radius: 999px;
    }
    .scroll-panel::-webkit-scrollbar-thumb {
        background: linear-gradient(180deg, #2a7a70 0%, #4d9782 100%);
        border-radius: 999px;
        border: 2px solid rgba(255, 255, 255, 0.72);
    }
    .scroll-panel-title {
        font-weight: 700;
        color: #102934;
        margin-bottom: 0.65rem;
    }
    .scroll-panel-body {
        color: #16232c;
        font-size: 0.98rem;
    }
    </style>
    <div class="hero-shell">
      <h1 class="hero-title">气候政策多利益相关方博弈沙盘</h1>
      <div class="hero-subtitle">
        以气候谈判为场景，整合真实国家样本、六阶段协商流程与情景实验结果，
        用于展示不同政策方案在可行性、公平性与阻力上的差异。
      </div>
      <div class="hero-chip-row">
        <span class="hero-chip">六阶段谈判流程</span>
        <span class="hero-chip">9 个真实国家样本</span>
        <span class="hero-chip">6 组情景实验</span>
        <span class="hero-chip">LULUCF / 森林维度</span>
        <span class="hero-chip">数据来源与可靠性标注</span>
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)

source_catalog = json.loads(SOURCE_CATALOG_PATH.read_text(encoding="utf-8"))
source_lookup = {item["id"]: item for item in source_catalog}
real_world_entities = json.loads(REAL_WORLD_ENTITIES_PATH.read_text(encoding="utf-8"))
real_policy_profiles = json.loads(REAL_POLICY_PROFILES_PATH.read_text(encoding="utf-8"))
policy_lookup = {item["entity_id"]: item for item in real_policy_profiles}

RUN_HISTORY_DIR.mkdir(parents=True, exist_ok=True)

SCENARIO_SHORT_LABELS = {
    "基线情景": "基线",
    "高雄心低补偿": "高雄心\n低补偿",
    "高雄心配套补偿": "高雄心\n配套补偿",
    "过渡优先": "过渡优先",
    "公平融资优先": "公平融资",
    "森林治理优先": "森林治理",
}

FEATURE_SHORT_LABELS = {
    "化石能源退出强度": "化石退出",
    "碳边境约束强度": "碳边境",
    "气候资金支持": "气候资金",
    "技术转移支持": "技术转移",
    "过渡期灵活性": "过渡灵活性",
    "CCS 过渡技术支持": "CCS",
    "适应/损失补偿支持": "适应补偿",
    "森林/LULUCF 支持": "LULUCF",
}

default_api_key = os.getenv("OPENAI_API_KEY", "")
default_base_url = os.getenv("OPENAI_BASE_URL", OPENCODE_GO_BASE_URL)
default_api_path = os.getenv("OPENAI_API_PATH", OPENCODE_GO_API_PATH)
default_model_name = os.getenv("OPENAI_MODEL", OPENCODE_GO_MODEL)
default_mode_index = 1 if default_api_key else 0

for key, value in {
    "api_key_input_final": default_api_key,
    "base_url_input_final": default_base_url,
    "api_path_input_final": default_api_path,
    "model_name_input_final": default_model_name,
}.items():
    if key not in st.session_state:
        st.session_state[key] = value


def render_note(title: str, body: str) -> None:
    st.caption(title)
    st.markdown(body)


def load_run_history() -> list[dict]:
    if not RUN_HISTORY_INDEX_PATH.exists():
        return []
    try:
        return json.loads(RUN_HISTORY_INDEX_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []


def save_run_history(records: list[dict]) -> None:
    RUN_HISTORY_INDEX_PATH.write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")


def short_scenario_label(label: str) -> str:
    return SCENARIO_SHORT_LABELS.get(label, label)


def short_feature_label(label: str) -> str:
    return FEATURE_SHORT_LABELS.get(label, label)


def build_single_history_entry(report: dict, policy_text: str, narrator_mode: str) -> dict:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    snapshot_name = f"{timestamp}_single.json"
    snapshot_path = RUN_HISTORY_DIR / snapshot_name
    snapshot_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return {
        "id": timestamp,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "experiment_mode": "单次推演",
        "agent_mode": report["agent_mode"]["label"],
        "narrator_mode": narrator_mode,
        "policy_text": policy_text,
        "summary": {
            "共识水平": report["consensus_label"],
            "可行性": report["final_scores"]["feasibility"],
            "公平性": report["final_scores"]["fairness"],
            "阻力强度": report["final_scores"]["resistance"],
        },
        "snapshot_path": str(snapshot_path),
    }


def build_batch_history_entry(batch_result: dict, payload: dict, policy_text: str, narrator_mode: str) -> dict:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    snapshot_name = f"{timestamp}_batch.json"
    snapshot_path = RUN_HISTORY_DIR / snapshot_name
    snapshot_path.write_text(json.dumps(batch_result, ensure_ascii=False, indent=2), encoding="utf-8")
    return {
        "id": timestamp,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "experiment_mode": "情景实验",
        "agent_mode": batch_result["agent_mode"],
        "narrator_mode": narrator_mode,
        "policy_text": policy_text,
        "summary": {
            "最佳可行性情景": payload["best_feasibility"]["情景"],
            "最佳公平性情景": payload["best_fairness"]["情景"],
            "最低阻力情景": payload["lowest_resistance"]["情景"],
        },
        "snapshot_path": str(snapshot_path),
    }


def append_run_history(entry: dict) -> None:
    records = load_run_history()
    records.insert(0, entry)
    save_run_history(records[:50])


if "policy_text_input_final" not in st.session_state:
    history_records = load_run_history()
    st.session_state["policy_text_input_final"] = history_records[0]["policy_text"] if history_records else DEFAULT_POLICY_TEXT


def render_history_sidebar() -> None:
    records = load_run_history()
    with st.sidebar.expander("历史记录", expanded=False):
        if not records:
            st.caption("当前还没有保存的推演记录。")
            return
        record_options = {f"{item['timestamp']} | {item['experiment_mode']} | {item['policy_text'][:18]}...": item for item in records[:20]}
        selected_label = st.selectbox("已保存记录", list(record_options.keys()))
        selected = record_options[selected_label]
        st.caption(f"主体模式：{selected['agent_mode']} | 叙事模式：{selected['narrator_mode']}")
        for key, value in selected["summary"].items():
            st.write(f"- {key}：{value}")
        if st.button("载入这条政策", key="load_history_policy"):
            st.session_state["policy_text_input_final"] = selected["policy_text"]
            st.rerun()
        if st.button("回放这次结果", key="replay_history_result"):
            st.session_state["replay_history_path"] = selected["snapshot_path"]
            st.session_state["policy_text_input_final"] = selected["policy_text"]
            st.rerun()
        st.caption(f"结果文件：{selected['snapshot_path']}")


def render_help_sidebar() -> None:
    with st.sidebar:
        st.title("帮助 / 使用说明")
        st.caption("这一区域用于现场解释 workflow、模式差异和关键指标。")

        with st.expander("快速理解", expanded=True):
            st.write("- 这不是气候预测模型，而是政策谈判沙盘。")
            st.write("- 规则引擎负责计算立场、分数和约束。")
            st.write("- 真实模型模式只负责把已计算出的立场写成更自然的发言。")

        with st.expander("单次推演 Workflow", expanded=True):
            st.write("1. 输入一条政策文本。")
            st.write("2. 系统先把文本识别成 8 个政策维度，形成初始政策画像。")
            st.write("3. 每个主体基于自身偏好权重、基础倾向和现实约束，给出第一轮立场陈述。")
            st.write("4. 系统汇总各主体的主要冲突点，识别谁与谁更容易结盟、谁是摇摆方。")
            st.write("5. 根据冲突与联盟关系，生成一组可能的交换条件和妥协方向。")
            st.write("6. 秘书处根据这些交换条件修订政策属性，形成谈判后的版本。")
            st.write("7. 各主体对修订版再次表决，得到最终立场分布、共识水平和综合评分。")
            st.caption("一句话理解：单次推演是在看一场具体谈判是如何一步步推进到最终表决的。")

        with st.expander("情景实验 Workflow", expanded=False):
            st.write("1. 输入同一条政策文本。")
            st.write("2. 系统先识别出文本的基础政策画像。")
            st.write("3. 然后依次叠加 6 个预设情景，形成 6 个略有差异的政策版本。")
            st.write("4. 每个情景都会完整跑一遍单次推演的六阶段流程。")
            st.write("5. 系统最后把 6 次结果并排比较，输出可行性、公平性、阻力强度和约束触发情况。")
            st.write("6. 再自动总结哪种情景更容易达成共识，哪种情景更公平，哪种情景阻力更小。")
            st.caption("一句话理解：情景实验不是多轮聊天，而是同一政策在不同设计方案下的对照实验。")

        with st.expander("模式区别", expanded=False):
            st.write("`单次推演`：看一场谈判过程。")
            st.write("`情景实验`：看多种政策设计的结果差异。")
            st.write("`抽象角色模式`：用典型谈判阵营解释结构。")
            st.write("`真实国家样本模式`：用 9 个真实国家样本展示真实性与约束。")
            st.write("`模板模式`：更稳定、更快，适合演示。")
            st.write("`真实模型模式`：发言更自然，但更慢，也更依赖 API。")

        with st.expander("核心指标怎么读", expanded=False):
            st.write("`可行性`：最终有多少主体支持这项政策，数值越高越容易推动。")
            st.write("`公平性`：政策是否给了融资、技术、适应、过渡和森林治理等配套支持。")
            st.write("`阻力强度`：政策推进会遇到多大阻力，越高表示越难谈成。")
            st.write("`共识水平`：对最终表决氛围的概括，如较强共识、有限妥协等。")

        with st.expander("六个默认情景", expanded=False):
            st.write("`基线情景`：直接沿用文本识别结果。")
            st.write("`高雄心低补偿`：减排更强，但配套支持不足。")
            st.write("`高雄心配套补偿`：减排更强，同时补上融资和技术支持。")
            st.write("`过渡优先`：更强调过渡期和 CCS，降低转型冲击。")
            st.write("`公平融资优先`：弱化贸易约束，强化融资和适应支持。")
            st.write("`森林治理优先`：突出森林、碳汇和土地利用治理。")

        with st.expander("关键名词", expanded=False):
            st.write("`NDC`：各国在《巴黎协定》框架下提交的气候承诺。")
            st.write("`LULUCF`：土地利用、土地利用变化和林业，常与森林和碳汇有关。")
            st.write("`CCS`：碳捕集与封存，这里把它视作过渡技术路线。")
            st.write("`碳边境约束`：对高碳产品设置边境规则或额外成本。")
            st.write("`现实约束`：某些国家在融资、适应、化石退出等议题上的谈判底线。")

        st.caption("完整说明文档：`prototype_v1/demo_explainer_guide.md`")
    render_history_sidebar()


def normalize_model_name(model_name: str) -> str:
    alias_map = {
        "DeepSeek V4 Pro": OPENCODE_GO_MODEL,
        "deepseek v4 pro": OPENCODE_GO_MODEL,
        "DeepSeek-V4-Pro": OPENCODE_GO_MODEL,
        "DeepSeekV4Pro": OPENCODE_GO_MODEL,
    }
    normalized = model_name.strip()
    return alias_map.get(normalized, normalized)


def render_stat_band(items: list[dict]) -> None:
    columns = st.columns(len(items), gap="large")
    for column, item in zip(columns, items):
        with column:
            st.caption(str(item["label"]))
            st.markdown(f"### {item['value']}")
            if item.get("sub"):
                st.caption(str(item["sub"]))
    st.divider()


def make_grouped_metric_chart(data: list[dict], title: str) -> None:
    spec = {
        "mark": {"type": "bar", "cornerRadiusTopLeft": 4, "cornerRadiusTopRight": 4},
        "encoding": {
            "x": {
                "field": "情景简称" if data and "情景简称" in data[0] else "情景",
                "type": "nominal",
                "title": None,
                "sort": None,
                "axis": {"labelAngle": 0, "labelLineHeight": 16, "labelLimit": 120, "labelOverlap": False},
            },
            "y": {"field": "数值", "type": "quantitative", "title": None, "scale": {"domain": [0, 100]}},
            "xOffset": {"field": "指标"},
            "color": {
                "field": "指标",
                "type": "nominal",
                "scale": {"range": ["#1f7a6e", "#c6922d", "#c86572"]},
                "legend": {"orient": "top"},
            },
            "tooltip": [
                {"field": "情景", "type": "nominal"},
                {"field": "指标", "type": "nominal"},
                {"field": "数值", "type": "quantitative"},
            ],
        },
        "height": 360,
        "title": title,
        "config": {
            "view": {"stroke": None},
            "background": None,
            "axis": {"labelColor": "#44545f", "titleColor": "#44545f", "gridColor": "#e7ece9"},
            "title": {"color": "#16232c", "fontSize": 15, "anchor": "start"},
        },
    }
    st.vega_lite_chart(data, spec, use_container_width=True)


def make_simple_bar_chart(data: list[dict], x_field: str, y_field: str, title: str, color: str, domain: list[int] | None = None) -> None:
    scale = {"domain": domain} if domain else {}
    spec = {
        "mark": {"type": "bar", "cornerRadiusTopLeft": 4, "cornerRadiusTopRight": 4, "color": color},
        "encoding": {
            "x": {"field": x_field, "type": "nominal", "title": None, "axis": {"labelAngle": -15}},
            "y": {"field": y_field, "type": "quantitative", "title": None, "scale": scale},
            "tooltip": [{"field": x_field, "type": "nominal"}, {"field": y_field, "type": "quantitative"}],
        },
        "height": 320,
        "title": title,
        "config": {
            "view": {"stroke": None},
            "background": None,
            "axis": {"labelColor": "#44545f", "titleColor": "#44545f", "gridColor": "#e7ece9"},
            "title": {"color": "#16232c", "fontSize": 15, "anchor": "start"},
        },
    }
    st.vega_lite_chart(data, spec, use_container_width=True)


def make_heatmap(data: list[dict], x_field: str, y_field: str, color_field: str, title: str, color_scheme: str = "tealblues") -> None:
    spec = {
        "layer": [
            {
                "mark": {"type": "rect", "cornerRadius": 6},
                "encoding": {
                    "x": {
                        "field": x_field,
                        "type": "nominal",
                        "title": None,
                        "sort": None,
                        "axis": {"labelAngle": 0, "labelLineHeight": 16, "labelLimit": 120, "labelOverlap": False},
                    },
                    "y": {"field": y_field, "type": "nominal", "title": None},
                    "color": {
                        "field": color_field,
                        "type": "quantitative",
                        "scale": {"scheme": color_scheme},
                        "legend": {"orient": "top"},
                    },
                    "tooltip": [
                        {"field": x_field, "type": "nominal"},
                        {"field": y_field, "type": "nominal"},
                        {"field": color_field, "type": "quantitative"},
                    ],
                },
            },
            {
                "mark": {"type": "text", "fontSize": 11, "color": "#17323d"},
                "encoding": {
                    "x": {"field": x_field, "type": "nominal"},
                    "y": {"field": y_field, "type": "nominal"},
                    "text": {"field": color_field, "type": "quantitative"},
                },
            },
        ],
        "height": 320,
        "title": title,
        "config": {
            "view": {"stroke": None},
            "background": None,
            "axis": {"labelColor": "#44545f", "titleColor": "#44545f"},
            "title": {"color": "#16232c", "fontSize": 15, "anchor": "start"},
        },
    }
    st.vega_lite_chart(data, spec, use_container_width=True)


def make_horizontal_bar_chart(data: list[dict], x_field: str, y_field: str, title: str, color: str, domain: list[int] | None = None) -> None:
    scale = {"domain": domain} if domain else {}
    spec = {
        "mark": {"type": "bar", "cornerRadiusEnd": 6, "color": color},
        "encoding": {
            "y": {"field": y_field, "type": "nominal", "title": None, "sort": "-x"},
            "x": {"field": x_field, "type": "quantitative", "title": None, "scale": scale},
            "tooltip": [{"field": y_field, "type": "nominal"}, {"field": x_field, "type": "quantitative"}],
        },
        "height": 320,
        "title": title,
        "config": {
            "view": {"stroke": None},
            "background": None,
            "axis": {"labelColor": "#44545f", "titleColor": "#44545f", "gridColor": "#e7ece9"},
            "title": {"color": "#16232c", "fontSize": 15, "anchor": "start"},
        },
    }
    st.vega_lite_chart(data, spec, use_container_width=True)


def build_experiment_payload(batch_result: dict) -> dict:
    grouped_rows = []
    feature_heat_rows = []
    constraint_heat_rows = []
    best_feasibility = max(batch_result["comparison_table"], key=lambda item: item["可行性"])
    best_fairness = max(batch_result["comparison_table"], key=lambda item: item["公平性"])
    lowest_resistance = min(batch_result["comparison_table"], key=lambda item: item["阻力强度"])

    for row in batch_result["comparison_table"]:
        for metric in ["可行性", "公平性", "阻力强度"]:
            grouped_rows.append(
                {
                    "情景": row["情景"],
                    "情景简称": short_scenario_label(row["情景"]),
                    "指标": metric,
                    "数值": row[metric],
                }
            )

    for scenario_item in batch_result["scenario_reports"]:
        scenario_label = scenario_item["scenario"]["label"]
        final_attrs = scenario_item["report"]["stage_results"][-1]["policy_attributes"]
        for feature in FEATURE_ORDER:
            feature_heat_rows.append(
                {
                    "情景": scenario_label,
                    "情景简称": short_scenario_label(scenario_label),
                    "政策维度": FEATURE_LABELS[feature],
                    "政策维度简称": short_feature_label(FEATURE_LABELS[feature]),
                    "数值": final_attrs[feature],
                }
            )
        counts = Counter(hit["feature"] for hit in scenario_item["constraint_hits"])
        for feature in FEATURE_ORDER:
            feature_label = FEATURE_LABELS[feature]
            constraint_heat_rows.append(
                {
                    "情景": scenario_label,
                    "情景简称": short_scenario_label(scenario_label),
                    "约束类型": feature_label,
                    "约束类型简称": short_feature_label(feature_label),
                    "触发次数": counts.get(feature_label, 0),
                }
            )

    return {
        "grouped_rows": grouped_rows,
        "feature_heat_rows": feature_heat_rows,
        "constraint_heat_rows": constraint_heat_rows,
        "best_feasibility": best_feasibility,
        "best_fairness": best_fairness,
        "lowest_resistance": lowest_resistance,
    }


def build_single_payload(report: dict) -> dict:
    final_attrs = report["stage_results"][-1]["policy_attributes"]
    status_counts = Counter(
        item.get("status_label") or item.get("status") or "未知"
        for item in report["final_positions"]
    )
    status_rows = [{"立场": key, "数量": value} for key, value in status_counts.items()]
    feature_rows = [{"政策维度": FEATURE_LABELS[key], "数值": final_attrs[key]} for key in FEATURE_ORDER]
    stage_rows = []
    for stage in report["stage_results"]:
        if "agent_results" not in stage:
            continue
        counts = Counter(item["status_label"] for item in stage["agent_results"])
        for status, value in counts.items():
            stage_rows.append({"阶段": stage["label"], "立场": status, "数量": value})
    final_stage = report["stage_results"][-1]
    final_constraints = Counter()
    for item in final_stage.get("agent_results", []):
        for violation in item.get("constraint_violations", []):
            final_constraints[violation["feature"]] += 1
    constraint_rows = [{"约束类型": key, "触发次数": value} for key, value in final_constraints.items()]
    return {
        "status_rows": status_rows,
        "feature_rows": feature_rows,
        "stage_rows": stage_rows,
        "constraint_rows": constraint_rows,
    }


def get_display_status(item: dict) -> str:
    return str(item.get("status_label") or item.get("status") or "未知")


def build_live_agent_rows(agent_results: list[dict]) -> list[dict]:
    return [
        {
            "主体": item["role"],
            "阵营": item["bloc"],
            "立场": get_display_status(item),
            "得分": item["score"],
        }
        for item in agent_results
    ]


def build_live_feature_rows(policy_attrs: dict) -> list[dict]:
    return [{"政策维度": FEATURE_LABELS[key], "数值": policy_attrs[key]} for key in FEATURE_ORDER]


def render_scroll_panel(title: str, content: str, height: int = 240) -> str:
    escaped = html.escape(content).replace("\n", "<br>")
    return (
        f'<div class="scroll-panel" style="height:{height}px;">'
        f'<div class="scroll-panel-title">{html.escape(title)}</div>'
        f'<div class="scroll-panel-body">{escaped}</div></div>'
    )


def render_table_panel(title: str, rows: list[dict], height: int = 260) -> str:
    if not rows:
        return render_scroll_panel(title, "暂无数据", height=height)
    columns = list(rows[0].keys())
    header_html = "".join(
        f'<th style="text-align:left; padding:0.6rem 0.75rem; border-bottom:1px solid rgba(15,23,42,0.08); color:#60707b; font-weight:600;">{html.escape(str(column))}</th>'
        for column in columns
    )
    body_rows = []
    for row in rows:
        cells = "".join(
            f'<td style="padding:0.65rem 0.75rem; border-bottom:1px solid rgba(15,23,42,0.06); vertical-align:top;">{html.escape(str(row.get(column, "")))}</td>'
            for column in columns
        )
        body_rows.append(f"<tr>{cells}</tr>")
    body_html = "".join(body_rows)
    return (
        f'<div class="scroll-panel" style="height:{height}px; padding:0.75rem 0.9rem;">'
        f'<div class="scroll-panel-title">{html.escape(title)}</div>'
        '<table style="width:100%; border-collapse:collapse; font-size:0.95rem; color:#16232c;">'
        f"<thead><tr>{header_html}</tr></thead><tbody>{body_html}</tbody></table></div>"
    )


def format_statement_entry(stage_name: str, item: dict, scenario_label: str | None = None) -> str:
    prefix = f"[{scenario_label}] " if scenario_label else ""
    return (
        f"{prefix}{stage_name} | {item['role']} | {get_display_status(item)} | 得分 {item['score']}\n"
        f"{item.get('statement', '暂无发言文本')}"
    )


def render_statement_panel(
    current_placeholder,
    history_placeholder,
    current_entry: str,
    history_entries: list[str],
) -> None:
    current_placeholder.markdown(render_scroll_panel("当前发言", current_entry, height=210), unsafe_allow_html=True)
    history_placeholder.markdown(
        render_scroll_panel("累计发言记录", "\n\n--------------------\n\n".join(history_entries[-12:]), height=320),
        unsafe_allow_html=True,
    )


LIVE_STAGE_LABELS = {
    "policy_parse": "政策属性识别",
    "position_statement": "立场陈述",
    "conflict_id": "冲突识别",
    "alliance_mapping": "联盟与分裂",
    "bargaining": "条件交换",
    "secretariat_revision": "秘书处修订",
    "final_vote": "最终表决",
    "final_summary": "结果汇总",
}


render_help_sidebar()


def expected_single_trace_steps(agent_count: int) -> int:
    return max(1, 6 + agent_count * 2)


def run_single_trace(
    sandbox: ClimatePolicySandbox,
    policy: dict,
    on_event: Callable[[dict], None] | None = None,
) -> dict:
    def emit(stage_id: str, message: str, **payload: object) -> None:
        if on_event:
            on_event({"stage_id": stage_id, "message": message, **payload})

    policy_text = str(policy["policy_text"])
    initial_attrs = sandbox._normalize_attributes(dict(policy["attributes"]), policy_text)
    emit(
        "policy_parse",
        "已完成政策属性识别",
        policy_attributes=initial_attrs,
        summary_text="系统已将输入文本映射为 8 个结构化政策维度。",
    )

    initial_vote = []
    for index, agent in enumerate(sandbox.agents, start=1):
        result = sandbox.evaluate_agent(agent, initial_attrs, policy_text=policy_text, stage_index=1)
        initial_vote.append(result)
        emit(
            "position_statement",
            f"立场陈述 {index}/{len(sandbox.agents)}：{agent.name}",
            agent_result=result,
            agent_results=list(initial_vote),
        )

    conflict_summary = sandbox._observer_stage_summary(initial_vote, initial_attrs, "初始表态")
    emit(
        "conflict_id",
        "已完成冲突识别",
        summary_text=conflict_summary["summary_text"],
        top_concerns=conflict_summary["top_concerns"],
    )

    alliance_map = sandbox._build_alliance_map(initial_vote)
    emit(
        "alliance_mapping",
        "已完成联盟识别",
        alliances=alliance_map["alliances"],
        splinters=alliance_map["splinters"],
    )

    bargaining_package = sandbox._build_bargaining_package(initial_vote, initial_attrs, conflict_summary, alliance_map)
    emit(
        "bargaining",
        "已完成条件交换分析",
        tradeoffs=bargaining_package["tradeoffs"],
        adjustments=bargaining_package["adjustments"],
        summary_text=bargaining_package["summary_text"],
    )

    revised_attrs = sandbox._apply_adjustments_copy(initial_attrs, bargaining_package["adjustments"])
    emit(
        "secretariat_revision",
        "已生成秘书处修订版本",
        policy_attributes=revised_attrs,
        feature_deltas=sandbox._build_feature_deltas(initial_attrs, revised_attrs),
        summary_text=f"修订方向：{sandbox._format_adjustments(bargaining_package['adjustments'])}",
    )

    final_vote = []
    for index, agent in enumerate(sandbox.agents, start=1):
        result = sandbox.evaluate_agent(agent, revised_attrs, policy_text=policy_text, stage_index=2)
        final_vote.append(result)
        emit(
            "final_vote",
            f"最终表决 {index}/{len(sandbox.agents)}：{agent.name}",
            agent_result=result,
            agent_results=list(final_vote),
        )

    final_summary = sandbox._observer_stage_summary(final_vote, revised_attrs, "最终表决")
    emit(
        "final_summary",
        "已完成最终汇总",
        summary_text=final_summary["summary_text"],
        status_counter=final_summary["status_counter"],
    )

    return sandbox._build_final_report(
        policy=policy,
        initial_attrs=initial_attrs,
        initial_vote=initial_vote,
        conflict_summary=conflict_summary,
        alliance_map=alliance_map,
        bargaining_package=bargaining_package,
        revised_attrs=revised_attrs,
        final_vote=final_vote,
        final_summary=final_summary,
    )


def run_single_with_progress(sandbox: ClimatePolicySandbox, policy: dict) -> dict:
    status_panel = st.status("正在运行单次推演...", expanded=True)
    progress_bar = st.progress(0.0, text="正在准备推演")
    stage_placeholder = st.empty()
    summary_placeholder = st.empty()
    table_placeholder = st.empty()
    statement_current_placeholder = st.empty()
    statement_history_placeholder = st.empty()
    log_placeholder = st.empty()
    log_lines: list[str] = []
    statement_history: list[str] = []
    total_steps = expected_single_trace_steps(len(sandbox.agents))
    completed_steps = 0

    def on_event(event: dict) -> None:
        nonlocal completed_steps
        completed_steps += 1
        stage_name = LIVE_STAGE_LABELS.get(event["stage_id"], event["stage_id"])
        progress_ratio = min(completed_steps / total_steps, 1.0)
        progress_bar.progress(progress_ratio, text=f"{stage_name}：{event['message']}")
        stage_placeholder.markdown(f"### 当前阶段：{stage_name}")

        if event.get("agent_result"):
            current = event["agent_result"]
            summary_placeholder.info(f"当前主体：{current['role']} | {get_display_status(current)} | 得分 {current['score']}")
            statement_entry = format_statement_entry(stage_name, current)
            statement_history.append(statement_entry)
            render_statement_panel(
                statement_current_placeholder,
                statement_history_placeholder,
                statement_entry,
                statement_history,
            )
        elif event.get("summary_text"):
            summary_placeholder.success(str(event["summary_text"]))
        else:
            summary_placeholder.caption(str(event["message"]))

        if event.get("agent_results"):
            table_placeholder.markdown(
                render_table_panel("当前立场概览", build_live_agent_rows(event["agent_results"]), height=250),
                unsafe_allow_html=True,
            )
        elif event.get("policy_attributes"):
            table_placeholder.markdown(
                render_table_panel("政策维度识别", build_live_feature_rows(event["policy_attributes"]), height=250),
                unsafe_allow_html=True,
            )
        elif event.get("alliances") is not None:
            alliance_rows = [
                {
                    "联盟": item["name"],
                    "成员": "、".join(item["members"]),
                    "基础": item["basis"],
                }
                for item in event["alliances"]
            ]
            if alliance_rows:
                table_placeholder.markdown(
                    render_table_panel("联盟识别", alliance_rows, height=250),
                    unsafe_allow_html=True,
                )
            else:
                table_placeholder.info("当前未识别到稳定联盟。")
        elif event.get("feature_deltas"):
            table_placeholder.markdown(
                render_table_panel("秘书处修订", event["feature_deltas"], height=250),
                unsafe_allow_html=True,
            )

        log_lines.append(f"{stage_name}：{event['message']}")
        log_placeholder.markdown(
            render_scroll_panel("实时日志", "\n".join(f"- {line}" for line in log_lines[-12:]), height=220),
            unsafe_allow_html=True,
        )
        status_panel.write(f"{stage_name}：{event['message']}")

    report = run_single_trace(sandbox, policy, on_event=on_event)
    progress_bar.progress(1.0, text="单次推演完成")
    status_panel.update(label="单次推演完成", state="complete", expanded=False)
    return report


def run_scenario_batch_with_progress(sandbox: ClimatePolicySandbox, policy_text: str) -> dict:
    scenario_defs = sandbox.get_default_scenarios()
    status_panel = st.status("正在运行情景实验...", expanded=True)
    progress_bar = st.progress(0.0, text="正在准备情景实验")
    scenario_placeholder = st.empty()
    comparison_placeholder = st.empty()
    statement_current_placeholder = st.empty()
    statement_history_placeholder = st.empty()
    log_placeholder = st.empty()
    log_lines: list[str] = []
    statement_history: list[str] = []

    reports = []
    comparison_rows = []
    constraint_counter: Counter[str] = Counter()
    actor_status_counter: dict[str, Counter[str]] = {}
    total_steps = max(1, len(scenario_defs) * expected_single_trace_steps(len(sandbox.agents)))
    completed_steps = 0

    for scenario_index, scenario in enumerate(scenario_defs, start=1):
        scenario_placeholder.markdown(
            f"### 当前情景：{scenario['label']}\n\n{scenario['description']}"
        )
        log_lines.append(f"开始运行情景 {scenario_index}/{len(scenario_defs)}：{scenario['label']}")
        status_panel.write(log_lines[-1])

        base_attrs = sandbox._normalize_attributes({}, policy_text)
        scenario_attrs = sandbox._merge_scenario_attrs(base_attrs, scenario.get("attribute_overrides", {}))

        def on_event(event: dict) -> None:
            nonlocal completed_steps
            completed_steps += 1
            progress_ratio = min(completed_steps / total_steps, 1.0)
            progress_bar.progress(progress_ratio, text=f"{scenario['label']}：{event['message']}")
            if event.get("agent_result"):
                current = event["agent_result"]
                scenario_placeholder.info(
                    f"当前情景：{scenario['label']} | 当前主体：{current['role']} | {get_display_status(current)} | 得分 {current['score']}"
                )
                stage_name = LIVE_STAGE_LABELS.get(event["stage_id"], event["stage_id"])
                statement_entry = format_statement_entry(stage_name, current, scenario["label"])
                statement_history.append(statement_entry)
                render_statement_panel(
                    statement_current_placeholder,
                    statement_history_placeholder,
                    statement_entry,
                    statement_history,
                )
            elif event.get("summary_text"):
                scenario_placeholder.success(f"{scenario['label']}：{event['summary_text']}")
            log_lines.append(f"{scenario['label']}：{event['message']}")
            log_placeholder.markdown(
                render_scroll_panel("实时日志", "\n".join(f"- {line}" for line in log_lines[-16:]), height=220),
                unsafe_allow_html=True,
            )

        report = run_single_trace(
            sandbox,
            {
                "title": str(scenario["label"]),
                "policy_text": policy_text,
                "attributes": scenario_attrs,
            },
            on_event=on_event,
        )

        support_count, conditional_support_count, oppose_count = sandbox._count_statuses(report["stage_results"][-1]["agent_results"])
        constraint_hits = sandbox._collect_constraint_hits(report["stage_results"][-1]["agent_results"])
        for hit in constraint_hits:
            constraint_counter[hit["feature"]] += 1
        for item in report["stage_results"][-1]["agent_results"]:
            actor_status_counter.setdefault(item["role"], Counter())[item["status_label"]] += 1

        comparison_rows.append(
            {
                "情景": scenario["label"],
                "说明": scenario["description"],
                "共识水平": report["consensus_label"],
                "可行性": report["final_scores"]["feasibility"],
                "公平性": report["final_scores"]["fairness"],
                "阻力强度": report["final_scores"]["resistance"],
                "支持数": support_count,
                "保留支持数": conditional_support_count,
                "反对数": oppose_count,
                "约束触发次数": len(constraint_hits),
            }
        )
        reports.append(
            {
                "scenario": scenario,
                "report": report,
                "constraint_hits": constraint_hits,
            }
        )
        comparison_placeholder.markdown(
            render_table_panel("情景对比进度", comparison_rows, height=260),
            unsafe_allow_html=True,
        )

    progress_bar.progress(1.0, text="情景实验完成")
    status_panel.update(label="情景实验完成", state="complete", expanded=False)

    return {
        "policy_text": policy_text,
        "agent_mode": sandbox._agent_mode_label(),
        "scenario_count": len(reports),
        "scenario_reports": reports,
        "comparison_table": comparison_rows,
        "research_findings": sandbox._build_scenario_findings(comparison_rows, constraint_counter, actor_status_counter),
        "method_notes": sandbox._build_method_limitations(),
    }


def render_batch_result(batch_result: dict) -> None:
    payload = build_experiment_payload(batch_result)
    tabs = st.tabs(["总览", "情景图表", "情景详情", "数据与方法"])

    with tabs[0]:
        render_stat_band(
            [
                {"label": "最佳可行性情景", "value": payload["best_feasibility"]["情景"], "sub": f'可行性 {payload["best_feasibility"]["可行性"]}'},
                {"label": "最佳公平性情景", "value": payload["best_fairness"]["情景"], "sub": f'公平性 {payload["best_fairness"]["公平性"]}'},
                {"label": "最低阻力情景", "value": payload["lowest_resistance"]["情景"], "sub": f'阻力 {payload["lowest_resistance"]["阻力强度"]}'},
            ]
        )
        render_note("关键观察", "以下结论由多情景对比自动生成，可直接作为展示摘要。")
        for item in batch_result["research_findings"]:
            st.write(f"- {item}")
        st.dataframe(batch_result["comparison_table"], use_container_width=True, hide_index=True)

    with tabs[1]:
        chart_col, heat_col = st.columns(2, gap="large")
        with chart_col:
            make_grouped_metric_chart(payload["grouped_rows"], "情景核心指标对比")
        with heat_col:
            make_heatmap(
                payload["feature_heat_rows"],
                "政策维度简称",
                "情景简称",
                "数值",
                "情景属性热力矩阵",
                color_scheme="goldgreen",
            )
        make_heatmap(
            payload["constraint_heat_rows"],
            "约束类型简称",
            "情景简称",
            "触发次数",
            "现实约束触发热力图",
            color_scheme="goldred",
        )

    with tabs[2]:
        for item in batch_result["scenario_reports"]:
            scenario = item["scenario"]
            scenario_report = item["report"]
            with st.expander(scenario["label"], expanded=scenario["id"] == "baseline_auto"):
                render_stat_band(
                    [
                        {"label": "共识水平", "value": scenario_report["consensus_label"], "sub": "最终表决"},
                        {"label": "可行性", "value": scenario_report["final_scores"]["feasibility"], "sub": "0-100"},
                        {"label": "公平性", "value": scenario_report["final_scores"]["fairness"], "sub": "0-100"},
                        {"label": "阻力强度", "value": scenario_report["final_scores"]["resistance"], "sub": "0-100"},
                    ]
                )
                render_note("情景说明", scenario["description"])
                detail_left, detail_right = st.columns([1.1, 0.9], gap="large")
                with detail_left:
                    st.markdown("**最终立场**")
                    st.dataframe(scenario_report["final_positions"], use_container_width=True, hide_index=True)
                with detail_right:
                    st.markdown("**最终政策属性**")
                    st.dataframe(
                        [{"维度": FEATURE_LABELS[key], "数值": scenario_report["stage_results"][-1]["policy_attributes"][key]} for key in FEATURE_ORDER],
                        use_container_width=True,
                        hide_index=True,
                    )
                if item["constraint_hits"]:
                    st.markdown("**本情景触发的现实约束**")
                    for hit in item["constraint_hits"]:
                        st.write(f"- {hit['role']}：{hit['message']}")

    with tabs[3]:
        method_col, source_col = st.columns(2, gap="large")
        with method_col:
            st.markdown("**方法**")
            for item in batch_result["method_notes"]["method"]:
                st.write(f"- {item}")
            st.markdown("**局限**")
            for item in batch_result["method_notes"]["limitations"]:
                st.write(f"- {item}")
        with source_col:
            st.markdown("**来源目录**")
            for source_item in source_catalog:
                with st.expander(f"{source_item['name']} | 可靠性 {source_item['reliability_level']}"):
                    st.write(f"机构：{source_item['organization']}")
                    st.write(f"类别：{source_item['category']}")
                    st.write(f"链接：{source_item['url']}")
                    st.write(f"为什么可靠：{source_item['why_reliable']}")
                    st.write("已知局限：")
                    for item in source_item["known_limitations"]:
                        st.write(f"- {item}")
            with st.expander("查看完整结果数据", expanded=False):
                st.json(batch_result)


def render_single_result(report: dict) -> None:
    payload = build_single_payload(report)
    tabs = st.tabs(["总览", "阶段流程", "主体与联盟", "数据与方法"])

    with tabs[0]:
        render_stat_band(
            [
                {"label": "推演主体", "value": report["agent_mode"]["label"], "sub": "当前运行模式"},
                {"label": "共识水平", "value": report["consensus_label"], "sub": "最终表决"},
                {"label": "可行性", "value": report["final_scores"]["feasibility"], "sub": "0-100"},
                {"label": "公平性", "value": report["final_scores"]["fairness"], "sub": "0-100"},
                {"label": "阻力强度", "value": report["final_scores"]["resistance"], "sub": "0-100"},
            ]
        )

        left, right = st.columns([1.2, 0.8], gap="large")
        with left:
            make_simple_bar_chart(payload["feature_rows"], "政策维度", "数值", "最终政策属性强度", "#1f7a6e", domain=[0, 3])
        with right:
            make_simple_bar_chart(payload["status_rows"], "立场", "数量", "最终立场分布", "#c6922d")

        if payload["stage_rows"]:
            st.vega_lite_chart(
                payload["stage_rows"],
                {
                    "mark": {"type": "line", "point": True, "strokeWidth": 3},
                    "encoding": {
                        "x": {"field": "阶段", "type": "ordinal", "title": None, "axis": {"labelAngle": -15}},
                        "y": {"field": "数量", "type": "quantitative", "title": None},
                        "color": {
                            "field": "立场",
                            "type": "nominal",
                            "scale": {"range": ["#1f7a6e", "#6f9d8f", "#d39b32", "#c86572"]},
                        },
                        "tooltip": [
                            {"field": "阶段", "type": "ordinal"},
                            {"field": "立场", "type": "nominal"},
                            {"field": "数量", "type": "quantitative"},
                        ],
                    },
                    "height": 320,
                    "title": "六阶段立场变化轨迹",
                    "config": {
                        "view": {"stroke": None},
                        "background": None,
                        "axis": {"labelColor": "#44545f", "titleColor": "#44545f", "gridColor": "#e7ece9"},
                        "title": {"color": "#16232c", "fontSize": 15, "anchor": "start"},
                    },
                },
                use_container_width=True,
            )

        summary_left, summary_right = st.columns(2, gap="large")
        with summary_left:
            render_note("主要阻力来源", "、".join(report["dominant_resistance_sources"]) if report["dominant_resistance_sources"] else "暂无明显集中阻力")
        with summary_right:
            render_note("妥协路径", report["compromise_path"])

        if payload["constraint_rows"]:
            make_simple_bar_chart(payload["constraint_rows"], "约束类型", "触发次数", "最终约束触发分布", "#c86572")

    with tabs[1]:
        for stage in report["stage_results"]:
            with st.expander(stage["label"], expanded=stage["stage_id"] in {"position_statement", "final_vote"}):
                st.write(stage["summary_text"])
                if stage.get("top_concerns"):
                    st.write("主要冲突：", "、".join(stage["top_concerns"]))
                if stage.get("alliances"):
                    st.write("潜在联盟：")
                    for alliance in stage["alliances"]:
                        st.write(f"- {alliance['name']}：{'、'.join(alliance['members'])}")
                if stage.get("tradeoffs"):
                    st.write("交换条件：")
                    for tradeoff in stage["tradeoffs"]:
                        st.write(f"- {tradeoff}")
                if stage.get("feature_deltas"):
                    st.dataframe(stage["feature_deltas"], use_container_width=True, hide_index=True)
                if stage.get("agent_results"):
                    for item in stage["agent_results"]:
                        with st.container():
                            st.markdown(f"**{item['role']} | {item['status_label']} | 得分 {item['score']}**")
                            st.caption(item["bloc"])
                            st.write(item["statement"])
                            st.write("支持点：", "；".join(item["positive_points"]) if item["positive_points"] else "暂无明显支持点")
                            st.write("担忧点：", "；".join(item["concern_points"]) if item["concern_points"] else "暂无明显担忧")
                            st.write("希望增加的条件：", "；".join(item["asks"]) if item["asks"] else "暂无")
                            if item.get("constraint_violations"):
                                st.write("现实约束触发：")
                                for violation in item["constraint_violations"]:
                                    st.write(f"- {violation['message']}（当前 {violation['actual']}）")
                            st.divider()

    with tabs[2]:
        alliance_col, role_col = st.columns([0.9, 1.1], gap="large")
        with alliance_col:
            st.markdown("**联盟版图**")
            if report["alliance_map"]["alliances"]:
                for alliance in report["alliance_map"]["alliances"]:
                    render_note(alliance["name"], f"{'、'.join(alliance['members'])}。{alliance['basis']}")
            else:
                render_note("联盟识别", "当前未识别到稳定联盟。")
            if report["alliance_map"]["splinters"]:
                st.markdown("**关键摇摆方**")
                for splinter in report["alliance_map"]["splinters"]:
                    st.write(f"- {splinter['role']}：{splinter['status']}，{splinter['note']}")
        with role_col:
            st.markdown("**主体画像与现实约束**")
            for item in report["agent_catalog"]:
                with st.expander(f"{item['role']} | {item['bloc']}"):
                    st.write(item["description"])
                    st.caption(f"设计依据：{item['design_rationale']}")
                    for basis in item["evidence_basis"]:
                        st.write(f"- {basis}")
                    if item.get("constraint_profile"):
                        mins = item["constraint_profile"].get("min_requirements", {})
                        maxs = item["constraint_profile"].get("max_tolerances", {})
                        if mins:
                            st.write("至少需要：")
                            for feature, value in mins.items():
                                st.write(f"- {FEATURE_LABELS[feature]} >= {value}")
                        if maxs:
                            st.write("最多容忍：")
                            for feature, value in maxs.items():
                                st.write(f"- {FEATURE_LABELS[feature]} <= {value}")
                        for note in item["constraint_profile"].get("rationale", []):
                            st.caption(f"约束依据：{note}")

    with tabs[3]:
        st.markdown("**来源目录**")
        for source_item in source_catalog:
            with st.expander(f"{source_item['name']} | 可靠性 {source_item['reliability_level']}"):
                st.write(f"机构：{source_item['organization']}")
                st.write(f"类别：{source_item['category']}")
                st.write(f"链接：{source_item['url']}")
                st.write(f"为什么可靠：{source_item['why_reliable']}")
                st.write("已知局限：")
                for item in source_item["known_limitations"]:
                    st.write(f"- {item}")
                st.write(f"推荐用途：{source_item['recommended_use']}")

        st.markdown("**真实国家样本**")
        for entity in real_world_entities:
            with st.expander(f"{entity['name']} | {entity['reference_role']}"):
                st.write(entity["simulation_use"])
                st.caption(f"可靠性总结：{entity['reliability_summary']['reason']}")
                rows = []
                for metric_name, metric in entity["objective_snapshot"].items():
                    rows.append(
                        {
                            "字段": metric_name,
                            "值": metric["value"],
                            "年份": metric["year"],
                            "来源": source_lookup[metric["source_id"]]["name"],
                        }
                    )
                st.dataframe(rows, use_container_width=True, hide_index=True)
                st.write("政策追溯：")
                st.write(f"- 官方主来源：{source_lookup[entity['policy_traceability']['primary_source_id']]['name']}")
                st.write(f"- 辅助结构化来源：{source_lookup[entity['policy_traceability']['secondary_source_id']]['name']}")
                st.write(f"- 说明：{entity['policy_traceability']['note']}")
                if entity["id"] in policy_lookup:
                    profile = policy_lookup[entity["id"]]
                    st.write(f"- 目标年份：{profile['policy_profile']['target_year']}")
                    st.write(f"- 目标类型：{profile['policy_profile']['target_type']}")
                    st.write(f"- 摘要：{profile['policy_profile']['mitigation_summary']}")

        with st.expander("查看完整结果数据", expanded=False):
            st.json(report)


mode_col, setup_col = st.columns([0.72, 1.28], gap="large")

with mode_col:
    st.subheader("运行设置")
    experiment_mode = st.radio("运行形态", ["单次推演", "情景实验"], horizontal=True)
    agent_mode_options = {
        "抽象角色模式": "abstract",
        "真实国家样本模式": "real_countries",
    }
    agent_mode_label = st.radio("推演主体模式", list(agent_mode_options.keys()), horizontal=True)
    selected_agent_mode = agent_mode_options[agent_mode_label]
    if selected_agent_mode == "real_countries":
        st.caption("当前接入 9 个真实国家样本，更适合展示真实性依据。")
    else:
        st.caption("当前使用抽象角色，更适合快速解释谈判结构。")

with setup_col:
    st.subheader("政策输入")
    policy_text = st.text_area(
        "输入政策提案",
        key="policy_text_input_final",
        height=150,
        label_visibility="collapsed",
    )

preview_sandbox = ClimatePolicySandbox(BASE_DIR, agent_mode=selected_agent_mode)
auto_detected_attrs = preview_sandbox._normalize_attributes({}, policy_text)

render_stat_band(
    [
        {"label": "运行形态", "value": experiment_mode, "sub": "单次推演 / 情景实验"},
        {"label": "推演主体", "value": agent_mode_label, "sub": "抽象角色 / 真实国家"},
        {"label": "真实国家样本", "value": "9", "sub": "当前接入样本数量"},
        {"label": "政策维度", "value": str(len(FEATURE_ORDER)), "sub": "含 LULUCF / 森林"},
    ]
)

attr_chart_col, attr_note_col = st.columns([1.2, 0.8], gap="large")
with attr_chart_col:
    make_horizontal_bar_chart(
        [{"强度": value, "属性": FEATURE_LABELS[key]} for key, value in auto_detected_attrs.items()],
        "强度",
        "属性",
        "政策维度识别结果",
        "#1f7a6e",
        domain=[0, 3],
    )
with attr_note_col:
    render_note("属性提取", "系统会根据政策文本自动识别各维度强度。")
    render_note("读图提示", "数值越高，表示该提案在对应议题上的表述越明确。")

with st.expander("模型设置（可选）", expanded=False):
    mode = st.radio("运行模式", ["模板模式", "真实模型模式"], index=default_mode_index, horizontal=True)
    api_key = st.session_state["api_key_input_final"]
    base_url = st.session_state["base_url_input_final"]
    api_path = st.session_state["api_path_input_final"]
    model_name = st.session_state["model_name_input_final"]
    if mode == "真实模型模式":
        if st.button("载入 OpenCode Go 预置", key="load_server_preset_final"):
            st.session_state["api_key_input_final"] = default_api_key
            st.session_state["base_url_input_final"] = OPENCODE_GO_BASE_URL
            st.session_state["api_path_input_final"] = OPENCODE_GO_API_PATH
            st.session_state["model_name_input_final"] = OPENCODE_GO_MODEL
        api_key = st.text_input("API Key", type="password", key="api_key_input_final")
        base_url = st.text_input("Base URL", key="base_url_input_final")
        api_path = st.text_input("API Path", key="api_path_input_final")
        model_name = st.text_input("Model", key="model_name_input_final")
        normalized_model_name = normalize_model_name(model_name)
        st.caption(f"当前生效配置：{base_url.rstrip('/')}/{api_path.lstrip('/')} | model={normalized_model_name}")
        if normalized_model_name != model_name.strip():
            st.caption(f"模型名已自动规范为：{normalized_model_name}")
    render_note("展示建议", "默认使用 OpenCode Go 预置；需要实时生成时可直接使用 DeepSeek V4 Pro。")

with st.expander("方法与数据来源", expanded=False):
    note_left, note_right = st.columns(2, gap="large")
    with note_left:
        render_note("建模思路", "系统将政策文本映射为 8 个谈判维度，再结合国家画像与现实约束进行推演。")
        render_note("结果边界", "结果用于比较不同方案的相对反应与冲突结构，不直接代表真实世界预测。")
    with note_right:
        render_note("主要来源", "UNFCCC NDC Registry、World Bank Open Data、ND-GAIN、Climate Watch。")
        render_note("可追溯性", "国家样本、指标年份、政策摘要与来源说明均可在界面内展开查看。")
    st.caption("详细说明文档：prototype_v1/demo_explainer_guide.md")


replay_path = st.session_state.get("replay_history_path")
if replay_path:
    replay_file = Path(replay_path)
    if replay_file.exists():
        replay_data = json.loads(replay_file.read_text(encoding="utf-8"))
        st.info(f"当前正在回放历史结果：{replay_file.name}")
        if st.button("退出历史回放", key="clear_history_replay"):
            st.session_state.pop("replay_history_path", None)
            st.rerun()
        if "comparison_table" in replay_data and "scenario_reports" in replay_data:
            render_batch_result(replay_data)
        else:
            render_single_result(replay_data)
        st.stop()
    else:
        st.warning("历史结果文件不存在，已自动退出回放模式。")
        st.session_state.pop("replay_history_path", None)


if st.button("运行推演", type="primary", use_container_width=True):
    for env_key in ["OPENAI_API_KEY", "OPENAI_BASE_URL", "OPENAI_API_PATH", "OPENAI_MODEL"]:
        os.environ.pop(env_key, None)

    if mode == "真实模型模式":
        if not api_key.strip():
            st.error("真实模型模式下请填写 API Key。")
            st.stop()
        os.environ["OPENAI_API_KEY"] = api_key.strip()
        os.environ["OPENAI_BASE_URL"] = base_url.strip()
        os.environ["OPENAI_API_PATH"] = api_path.strip()
        os.environ["OPENAI_MODEL"] = normalize_model_name(model_name)

    sandbox = ClimatePolicySandbox(BASE_DIR, agent_mode=selected_agent_mode)
    policy = {
        "title": "自定义政策",
        "policy_text": policy_text,
        "attributes": sandbox._normalize_attributes({}, policy_text),
    }

    try:
        if experiment_mode == "情景实验":
            batch_result = run_scenario_batch_with_progress(sandbox, policy_text)
        else:
            report = run_single_with_progress(sandbox, policy)
    except Exception as error:  # pragma: no cover
        st.error(f"运行失败：{error}")
        st.stop()

    narrator_mode = sandbox.narrator.describe()
    st.success(f"当前叙事模式：{narrator_mode}")

    if experiment_mode == "情景实验":
        payload = build_experiment_payload(batch_result)
        append_run_history(build_batch_history_entry(batch_result, payload, policy_text, narrator_mode))
        render_batch_result(batch_result)

    else:
        append_run_history(build_single_history_entry(report, policy_text, narrator_mode))
        render_single_result(report)
