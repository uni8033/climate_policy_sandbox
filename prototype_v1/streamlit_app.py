from __future__ import annotations

import os
from pathlib import Path

try:
    import streamlit as st
except ImportError:  # pragma: no cover
    raise SystemExit("请先安装 streamlit，再运行 streamlit_app.py")

from climate_policy_engine import ClimatePolicySandbox, FEATURE_LABELS

BASE_DIR = Path(__file__).resolve().parent

st.set_page_config(page_title="气候政策博弈沙盘 v1.0", layout="wide")
st.title("气候政策多利益相关方博弈沙盘 v1.0")
st.caption("当前版本支持模板模式与真实大模型模式。建议先用模板模式验证流程，再切换到 OpenAI-compatible API 做真实调用。")

default_api_key = os.getenv("OPENAI_API_KEY", "")
default_base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
default_api_path = os.getenv("OPENAI_API_PATH", "chat/completions")
default_model_name = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")
default_mode_index = 1 if default_api_key else 0

if "api_key_input_v2" not in st.session_state:
    st.session_state["api_key_input_v2"] = default_api_key
if "base_url_input_v2" not in st.session_state:
    st.session_state["base_url_input_v2"] = default_base_url
if "api_path_input_v2" not in st.session_state:
    st.session_state["api_path_input_v2"] = default_api_path
if "model_name_input_v2" not in st.session_state:
    st.session_state["model_name_input_v2"] = default_model_name

with st.sidebar:
    st.subheader("模型配置")
    mode = st.radio("运行模式", ["模板模式", "真实模型模式"], index=default_mode_index)
    api_key = default_api_key
    base_url = default_base_url
    api_path = default_api_path
    model_name = default_model_name
    if mode == "真实模型模式":
        if st.button("载入服务器预置配置"):
            st.session_state["api_key_input_v2"] = default_api_key
            st.session_state["base_url_input_v2"] = default_base_url
            st.session_state["api_path_input_v2"] = default_api_path
            st.session_state["model_name_input_v2"] = default_model_name
        api_key = st.text_input("API Key", type="password", key="api_key_input_v2")
        base_url = st.text_input("Base URL", key="base_url_input_v2")
        api_path = st.text_input("API Path", key="api_path_input_v2")
        model_name = st.text_input("Model", key="model_name_input_v2")
        st.caption("如使用 OpenAI-compatible Chat 接口，通常填写 `chat/completions`；如使用 Responses 接口，可填写 `responses`。")
        st.caption(f"当前生效配置：{base_url.rstrip('/')}/{api_path.lstrip('/')} | model={model_name}")

policy_text = st.text_area(
    "输入政策提案",
    value="2030年前停止新建无减排措施煤电，并对高碳产品提高碳边境约束。",
    height=120,
)

st.subheader("调整政策属性")
cols = st.columns(4)
features = {}
for idx, key in enumerate(FEATURE_LABELS):
    with cols[idx % 4]:
        features[key] = st.slider(FEATURE_LABELS[key], min_value=0, max_value=3, value=0)

with st.expander("查看当前参数与角色设定说明"):
    st.markdown(
        """
        **参数分为 7 类**

        - `化石能源退出强度`：衡量政策对煤电等高排放能源的退出要求有多强。
        - `碳边境约束强度`：衡量是否通过碳关税或边境规则向外传导减排压力。
        - `气候资金支持`：衡量是否给发展中经济体提供明确的资金补偿或转型支持。
        - `技术转移支持`：衡量是否提供低碳技术、能力建设和知识转移。
        - `过渡期灵活性`：衡量政策是否允许分阶段过渡，避免短期剧烈冲击。
        - `CCS 过渡技术支持`：衡量是否保留碳捕集等过渡技术路线。
        - `适应/损失补偿支持`：衡量是否回应高脆弱地区的适应与损失补偿诉求。

        **角色设定**

        - `发展中国家代表`：更看重资金、技术、发展权和过渡安排。
        - `发达国家联盟代表`：更支持强减排、规则约束和执行时间表。
        - `传统能源/重工业代表`：更关注就业、成本、资产搁浅和过渡技术。
        - `小岛国/环保 NGO 代表`：更关注气候脆弱性、正义和损失补偿。

        **当前 1.0 版逻辑**

        - 每个角色都有一组参数权重，表示其对不同政策属性的敏感度。
        - 权重为正，说明该属性会提高支持度；权重为负，说明会加剧反对。
        - 当前权重依据主要来自课程讨论场景、现实气候谈判常见分歧和角色立场直觉，后续再逐步用真实数据校准。
        """
    )

if st.button("运行推演"):
    for env_key in ["OPENAI_API_KEY", "OPENAI_BASE_URL", "OPENAI_API_PATH", "OPENAI_MODEL"]:
        os.environ.pop(env_key, None)

    if mode == "真实模型模式":
        if not api_key.strip():
            st.error("真实模型模式下请填写 API Key。")
            st.stop()
        if "opencode.ai" not in base_url and "deepseek-v4-pro" in model_name:
            st.warning("当前看起来不像 OpenCode Go 配置；若你要用服务器预置的 deepseek-v4-pro，请点击“载入服务器预置配置”。")
        os.environ["OPENAI_API_KEY"] = api_key.strip()
        os.environ["OPENAI_BASE_URL"] = base_url.strip()
        os.environ["OPENAI_API_PATH"] = api_path.strip()
        os.environ["OPENAI_MODEL"] = model_name.strip()

    sandbox = ClimatePolicySandbox(BASE_DIR)
    policy = {
        "title": "自定义政策",
        "policy_text": policy_text,
        "attributes": features,
    }
    policy["attributes"] = sandbox._normalize_attributes(features, policy_text)
    try:
        report = sandbox.run(policy, rounds=3)
    except Exception as error:  # pragma: no cover
        st.error(f"运行失败：{error}")
        st.stop()

    st.success(f"当前叙事模式：{sandbox.narrator.describe()}")

    st.subheader("最终评分")
    metric_cols = st.columns(3)
    metric_cols[0].metric("落地可行性", report["final_scores"]["feasibility"])
    metric_cols[1].metric("公平性", report["final_scores"]["fairness"])
    metric_cols[2].metric("阻力强度", report["final_scores"]["resistance"])

    st.subheader("最终立场")
    for item in report["final_positions"]:
        st.write(f"- {item['role']}：{item['status']}（得分 {item['score']}）")

    st.subheader("分轮记录")
    for round_item in report["round_results"]:
        with st.expander(f"第 {round_item['round']} 轮"):
            st.write("本轮政策属性：")
            for key, value in round_item["policy_attributes"].items():
                st.write(f"- {FEATURE_LABELS[key]}：{value}")
            st.write("各角色发言：")
            for result in round_item["agent_results"]:
                st.write(f"- {result['role']}（{result['status_label']}）：{result['statement']}")
            st.info(round_item["observer_summary"]["summary_text"])
