"""气候政策多利益相关方博弈沙盘 2.0 beta 核心引擎。"""

from __future__ import annotations

import json
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Tuple

from llm_adapter import NarrationRequest, build_narrator

FEATURE_ORDER = [
    "fossil_phaseout",
    "carbon_tariff",
    "climate_finance",
    "tech_transfer",
    "transition_flexibility",
    "ccs_support",
    "adaptation_fund",
    "lulucf_support",
]

FEATURE_LABELS = {
    "fossil_phaseout": "化石能源退出强度",
    "carbon_tariff": "碳边境约束强度",
    "climate_finance": "气候资金支持",
    "tech_transfer": "技术转移支持",
    "transition_flexibility": "过渡期灵活性",
    "ccs_support": "CCS 过渡技术支持",
    "adaptation_fund": "适应/损失补偿支持",
    "lulucf_support": "森林/LULUCF 支持",
}

FEATURE_TALKING_POINTS = {
    "fossil_phaseout": "更明确地限制高排放能源扩张",
    "carbon_tariff": "以更强的边境约束推动减排责任传导",
    "climate_finance": "增加气候资金与转型补偿安排",
    "tech_transfer": "提供更可落地的技术转移与能力建设",
    "transition_flexibility": "允许分阶段过渡并保留政策弹性",
    "ccs_support": "保留 CCS 等过渡技术选项",
    "adaptation_fund": "补充适应与损失补偿机制",
    "lulucf_support": "强化森林保护、碳汇和土地利用治理安排",
}

FEATURE_STRENGTHEN_ASKS = {
    "fossil_phaseout": "增加更清晰的化石能源退出时间表",
    "carbon_tariff": "保留一定强度的国际规则约束",
    "climate_finance": "增加更明确的资金支持承诺",
    "tech_transfer": "增加技术转移和能力建设支持",
    "transition_flexibility": "加入更长的过渡期和分阶段安排",
    "ccs_support": "保留 CCS 等过渡技术路线",
    "adaptation_fund": "加入损失与损害或适应补偿安排",
    "lulucf_support": "补充森林保护、碳汇与土地利用治理支持",
}

FEATURE_WEAKEN_ASKS = {
    "fossil_phaseout": "细化退出路径，避免一刀切冲击",
    "carbon_tariff": "弱化单边碳边境约束或增加豁免机制",
    "climate_finance": "避免超出当前可执行范围的资金承诺",
    "tech_transfer": "将技术合作设计为渐进推进机制",
    "transition_flexibility": "减少过长过渡安排带来的执行拖延",
    "ccs_support": "避免对 CCS 路线给予过高依赖",
    "adaptation_fund": "将补偿安排与现有融资机制衔接",
    "lulucf_support": "避免超出当前执行能力的土地利用约束",
}

STATUS_LABELS = {
    "support": "支持",
    "conditional_support": "有保留地支持",
    "conditional_oppose": "有保留地反对",
    "oppose": "强烈反对",
}

STATUS_SCORE = {
    "support": 3,
    "conditional_support": 2,
    "conditional_oppose": 1,
    "oppose": 0,
}

PIPELINE_STAGES = [
    ("position_statement", "立场陈述"),
    ("conflict_id", "冲突识别"),
    ("alliance_mapping", "联盟与分裂"),
    ("bargaining", "条件交换"),
    ("secretariat_revision", "秘书处修订"),
    ("final_vote", "最终表决"),
]

DEFAULT_SCENARIO_LIBRARY = [
    {
        "id": "baseline_auto",
        "label": "基线情景",
        "description": "直接采用文本自动识别结果，不额外增加补偿或过渡安排。",
        "attribute_overrides": {},
    },
    {
        "id": "high_ambition_no_support",
        "label": "高雄心低补偿",
        "description": "强化减排与边境约束，但不额外增加融资、适应和技术支持。",
        "attribute_overrides": {
            "fossil_phaseout": 3,
            "carbon_tariff": 2,
            "climate_finance": 0,
            "tech_transfer": 0,
            "adaptation_fund": 0,
        },
    },
    {
        "id": "high_ambition_with_support",
        "label": "高雄心配套补偿",
        "description": "强化减排，同时增加融资、技术转移和适应补偿。",
        "attribute_overrides": {
            "fossil_phaseout": 3,
            "carbon_tariff": 2,
            "climate_finance": 2,
            "tech_transfer": 2,
            "adaptation_fund": 2,
            "lulucf_support": 1,
        },
    },
    {
        "id": "transition_first",
        "label": "过渡优先",
        "description": "强调过渡期、CCS 和缓冲安排，降低快速退出冲击。",
        "attribute_overrides": {
            "fossil_phaseout": 1,
            "carbon_tariff": 0,
            "transition_flexibility": 3,
            "ccs_support": 2,
            "climate_finance": 1,
            "lulucf_support": 1,
        },
    },
    {
        "id": "finance_justice",
        "label": "公平融资优先",
        "description": "突出融资、公平和适应议题，弱化贸易型约束。",
        "attribute_overrides": {
            "carbon_tariff": 0,
            "climate_finance": 3,
            "tech_transfer": 2,
            "adaptation_fund": 3,
            "transition_flexibility": 2,
            "lulucf_support": 2,
        },
    },
    {
        "id": "forest_governance",
        "label": "森林治理优先",
        "description": "突出森林保护、碳汇与土地利用治理，同时给予一定融资和技术支持。",
        "attribute_overrides": {
            "climate_finance": 2,
            "tech_transfer": 2,
            "adaptation_fund": 1,
            "lulucf_support": 3,
        },
    },
]


@dataclass
class Agent:
    agent_id: str
    name: str
    bloc: str
    description: str
    design_rationale: str
    evidence_basis: List[str] = field(default_factory=list)
    priority_asks: List[str] = field(default_factory=list)
    base_bias: float = 0.0
    weights: Dict[str, float] = field(default_factory=dict)
    constraint_profile: Dict[str, object] = field(default_factory=dict)


class ClimatePolicySandbox:
    def __init__(self, base_dir: Path, agent_mode: str = "abstract") -> None:
        self.base_dir = Path(base_dir)
        self.agent_mode = agent_mode
        self.narrator = build_narrator()
        self.source_catalog = self._load_json(self.base_dir / "data" / "source_catalog.json")
        self.source_lookup = {item["id"]: item for item in self.source_catalog}
        self.real_world_entities = self._load_json(self.base_dir / "data" / "real_world_entities.json")
        self.real_policy_profiles = self._load_json(self.base_dir / "data" / "real_policy_profiles.json")
        self.policy_profile_lookup = {item["entity_id"]: item for item in self.real_policy_profiles}
        self.agents = self._build_agents()
        self.agent_lookup = {agent.agent_id: agent for agent in self.agents}

    def _load_json(self, path: Path) -> List[Dict[str, object]]:
        return json.loads(path.read_text(encoding="utf-8"))

    def _build_agents(self) -> List[Agent]:
        if self.agent_mode == "real_countries":
            return self._build_real_country_agents()
        return self._load_agents(self.base_dir / "data" / "agents.json")

    def _load_agents(self, path: Path) -> List[Agent]:
        raw = self._load_json(path)
        agents = []
        for item in raw:
            weights = {key: float(item["weights"].get(key, 0.0)) for key in FEATURE_ORDER}
            agents.append(
                Agent(
                    agent_id=item["id"],
                    name=item["name"],
                    bloc=item.get("bloc", "未分组"),
                    description=item["description"],
                    design_rationale=item.get("design_rationale", ""),
                    evidence_basis=item.get("evidence_basis", []),
                    priority_asks=item.get("priority_asks", []),
                    base_bias=float(item.get("base_bias", 0.0)),
                    weights=weights,
                )
            )
        return agents

    def _build_real_country_agents(self) -> List[Agent]:
        agents = []
        for entity in self.real_world_entities:
            profile = self.policy_profile_lookup.get(entity["id"])
            if not profile:
                continue
            weights = self._derive_country_weights(entity, profile)
            priority_asks = self._derive_country_priority_asks(entity, profile, weights)
            constraint_profile = self._build_country_constraint_profile(entity, profile)
            agents.append(
                Agent(
                    agent_id=str(entity["id"]),
                    name=str(entity["name"]),
                    bloc=str(entity["reference_role"]),
                    description=self._build_country_description(entity, profile),
                    design_rationale=self._build_country_design_rationale(entity, profile),
                    evidence_basis=self._build_country_evidence_basis(entity, profile),
                    priority_asks=priority_asks,
                    base_bias=self._derive_country_base_bias(entity, profile),
                    weights=weights,
                    constraint_profile=constraint_profile,
                )
            )
        return agents

    def _metric_value(self, entity: Dict[str, object], metric_name: str) -> float:
        snapshot = entity.get("objective_snapshot", {})
        metric = snapshot.get(metric_name, {})
        value = metric.get("value")
        return float(value) if value is not None else 0.0

    def _clamp_weight(self, value: float) -> float:
        return round(max(-1.8, min(1.8, value)), 2)

    def _has_conditional_support_signal(self, text: str) -> bool:
        support_keywords = ["finance", "financing", "融资", "support", "资金", "international climate financing"]
        negative_cues = ["未明确", "未像", "not explicit", "不等同", "no longer active"]
        return any(keyword in text for keyword in support_keywords) and not any(cue in text for cue in negative_cues)

    def _has_tech_support_signal(self, text: str) -> bool:
        tech_keywords = ["technology", "技术", "capacity"]
        negative_cues = ["不提供技术", "未明确", "not explicit"]
        return any(keyword in text for keyword in tech_keywords) and not any(cue in text for cue in negative_cues)

    def _has_lulucf_signal(self, profile: Dict[str, object]) -> bool:
        policy_profile = profile["policy_profile"]
        scope_items = [str(item).lower() for item in policy_profile.get("sector_scope", [])]
        text = f"{policy_profile.get('mitigation_summary', '')} {policy_profile.get('conditionality_note', '')}".lower()
        keywords = ["lulucf", "forest", "forestry", "tree cover", "碳汇", "森林", "土地利用"]
        return any(keyword in " ".join(scope_items) or keyword in text for keyword in keywords)

    def _derive_country_base_bias(self, entity: Dict[str, object], profile: Dict[str, object]) -> float:
        readiness = self._metric_value(entity, "nd_gain_readiness")
        vulnerability = self._metric_value(entity, "nd_gain_vulnerability")
        fuel_exports = self._metric_value(entity, "fuel_exports_share_merchandise_exports")
        gdp_per_capita = self._metric_value(entity, "gdp_per_capita_current_usd")
        target_type = self._normalize_target_type(str(profile["policy_profile"]["target_type"]))
        conditionality = str(profile["policy_profile"]["conditionality_note"])

        bias = 0.0
        if readiness >= 0.6:
            bias += 0.45
        if vulnerability >= 0.45:
            bias -= 0.2
        if fuel_exports >= 40:
            bias -= 0.55
        elif fuel_exports <= 5:
            bias += 0.15
        if gdp_per_capita < 7000:
            bias -= 0.15
        if target_type in {"base_year_target", "trajectory_target"}:
            bias += 0.2
        if "依赖" in conditionality or self._has_conditional_support_signal(conditionality.lower()):
            bias -= 0.15
        return round(bias, 2)

    def _derive_country_weights(self, entity: Dict[str, object], profile: Dict[str, object]) -> Dict[str, float]:
        readiness = self._metric_value(entity, "nd_gain_readiness")
        vulnerability = self._metric_value(entity, "nd_gain_vulnerability")
        fuel_exports = self._metric_value(entity, "fuel_exports_share_merchandise_exports")
        renewables = self._metric_value(entity, "renewable_energy_share_final_consumption")
        gdp_per_capita = self._metric_value(entity, "gdp_per_capita_current_usd")
        target_type = self._normalize_target_type(str(profile["policy_profile"]["target_type"]))
        conditionality = str(profile["policy_profile"]["conditionality_note"]).lower()
        adaptation_included = bool(profile["policy_profile"]["adaptation_included"])
        has_lulucf_signal = self._has_lulucf_signal(profile)

        weights = {}

        fossil_phaseout = 0.0
        if readiness >= 0.6:
            fossil_phaseout += 0.6
        if renewables >= 20:
            fossil_phaseout += 0.35
        if fuel_exports >= 15:
            fossil_phaseout -= 0.7
        if fuel_exports >= 50:
            fossil_phaseout -= 0.9
        if gdp_per_capita < 8000:
            fossil_phaseout -= 0.35
        if target_type in {"base_year_target", "trajectory_target"} and fuel_exports < 20:
            fossil_phaseout += 0.25
        if target_type in {"intensity_target", "baseline_scenario_target", "fixed_level_trajectory_target"}:
            fossil_phaseout -= 0.2
        weights["fossil_phaseout"] = self._clamp_weight(fossil_phaseout)

        carbon_tariff = 0.0
        if gdp_per_capita >= 25000 and readiness >= 0.6:
            carbon_tariff += 0.8
        if fuel_exports <= 5:
            carbon_tariff += 0.2
        if gdp_per_capita < 15000:
            carbon_tariff -= 0.55
        if fuel_exports >= 30:
            carbon_tariff -= 0.75
        weights["carbon_tariff"] = self._clamp_weight(carbon_tariff)

        climate_finance = 0.0
        if gdp_per_capita < 12000:
            climate_finance += 0.7
        if vulnerability >= 0.4:
            climate_finance += 0.65
        if self._has_conditional_support_signal(conditionality):
            climate_finance += 0.45
        if gdp_per_capita >= 30000 and readiness >= 0.6:
            climate_finance -= 0.45
        weights["climate_finance"] = self._clamp_weight(climate_finance)

        tech_transfer = 0.0
        if gdp_per_capita < 15000:
            tech_transfer += 0.75
        if readiness < 0.5:
            tech_transfer += 0.35
        if self._has_tech_support_signal(conditionality):
            tech_transfer += 0.45
        if gdp_per_capita >= 40000 and readiness >= 0.65:
            tech_transfer -= 0.2
        weights["tech_transfer"] = self._clamp_weight(tech_transfer)

        transition_flexibility = 0.0
        if target_type in {"intensity_target", "baseline_scenario_target", "fixed_level_trajectory_target"}:
            transition_flexibility += 0.9
        if fuel_exports >= 20:
            transition_flexibility += 0.75
        if gdp_per_capita < 10000:
            transition_flexibility += 0.45
        if readiness >= 0.65 and fuel_exports <= 5:
            transition_flexibility -= 0.35
        weights["transition_flexibility"] = self._clamp_weight(transition_flexibility)

        ccs_support = 0.0
        if fuel_exports >= 30:
            ccs_support += 1.0
        elif fuel_exports >= 10:
            ccs_support += 0.35
        if target_type == "base_year_target":
            ccs_support += 0.15
        if vulnerability >= 0.45 and gdp_per_capita < 10000:
            ccs_support -= 0.2
        weights["ccs_support"] = self._clamp_weight(ccs_support)

        adaptation_fund = 0.0
        if vulnerability >= 0.43:
            adaptation_fund += 1.0
        if adaptation_included:
            adaptation_fund += 0.3
        if gdp_per_capita < 10000:
            adaptation_fund += 0.35
        if readiness >= 0.65 and vulnerability < 0.35:
            adaptation_fund -= 0.25
        weights["adaptation_fund"] = self._clamp_weight(adaptation_fund)

        lulucf_support = 0.0
        if has_lulucf_signal:
            lulucf_support += 0.7
        if vulnerability >= 0.42:
            lulucf_support += 0.2
        if gdp_per_capita < 15000:
            lulucf_support += 0.25
        if fuel_exports >= 40 and not has_lulucf_signal:
            lulucf_support -= 0.25
        if readiness >= 0.6 and has_lulucf_signal:
            lulucf_support += 0.15
        weights["lulucf_support"] = self._clamp_weight(lulucf_support)

        return {key: weights.get(key, 0.0) for key in FEATURE_ORDER}

    def _derive_country_priority_asks(
        self,
        entity: Dict[str, object],
        profile: Dict[str, object],
        weights: Dict[str, float],
    ) -> List[str]:
        vulnerability = self._metric_value(entity, "nd_gain_vulnerability")
        gdp_per_capita = self._metric_value(entity, "gdp_per_capita_current_usd")
        fuel_exports = self._metric_value(entity, "fuel_exports_share_merchandise_exports")
        has_lulucf_signal = self._has_lulucf_signal(profile)

        asks = []
        if vulnerability >= 0.43:
            asks.append("adaptation_fund")
        if gdp_per_capita < 15000:
            asks.append("climate_finance")
            asks.append("tech_transfer")
        if fuel_exports >= 20:
            asks.append("transition_flexibility")
            asks.append("ccs_support")
        if weights["fossil_phaseout"] > 0.4:
            asks.append("fossil_phaseout")
        if weights["carbon_tariff"] > 0.4:
            asks.append("carbon_tariff")
        if has_lulucf_signal:
            asks.append("lulucf_support")

        deduped = []
        for item in asks:
            if item not in deduped:
                deduped.append(item)
        if not deduped:
            ranked = sorted(FEATURE_ORDER, key=lambda key: abs(weights[key]), reverse=True)
            deduped = ranked[:3]
        return deduped[:4]

    def _build_country_description(self, entity: Dict[str, object], profile: Dict[str, object]) -> str:
        return (
            f"{entity['name']}作为{entity['reference_role']}进入推演。"
            f" 当前承诺摘要：{profile['policy_profile']['mitigation_summary']}"
        )

    def _build_country_design_rationale(self, entity: Dict[str, object], profile: Dict[str, object]) -> str:
        return (
            f"以{entity['name']}的国家背景指标、脆弱性/准备度，以及已公开 NDC 承诺结构化摘要共同生成偏好权重；"
            f" 承诺入口为{profile['policy_profile']['document_name']}。"
        )

    def _normalize_target_type(self, target_type: str) -> str:
        return (
            target_type.lower()
            .replace(" ", "_")
            .replace(";", "_")
            .replace("__", "_")
            .strip("_")
        )

    def _build_country_constraint_profile(self, entity: Dict[str, object], profile: Dict[str, object]) -> Dict[str, object]:
        vulnerability = self._metric_value(entity, "nd_gain_vulnerability")
        readiness = self._metric_value(entity, "nd_gain_readiness")
        fuel_exports = self._metric_value(entity, "fuel_exports_share_merchandise_exports")
        gdp_per_capita = self._metric_value(entity, "gdp_per_capita_current_usd")
        target_type = self._normalize_target_type(str(profile["policy_profile"]["target_type"]))
        conditionality = str(profile["policy_profile"]["conditionality_note"]).lower()
        adaptation_included = bool(profile["policy_profile"]["adaptation_included"])
        has_lulucf_signal = self._has_lulucf_signal(profile)

        min_requirements: Dict[str, int] = {}
        max_tolerances: Dict[str, int] = {}
        rationale: List[str] = []

        if vulnerability >= 0.5:
            min_requirements["adaptation_fund"] = 2
            rationale.append("高脆弱国家需要更明确的适应与损失损害安排。")
        elif vulnerability >= 0.42 or adaptation_included:
            min_requirements["adaptation_fund"] = max(min_requirements.get("adaptation_fund", 0), 1)
            rationale.append("已公开承诺包含适应内容，因此不能完全忽略适应议题。")

        if gdp_per_capita < 6000:
            min_requirements["climate_finance"] = max(min_requirements.get("climate_finance", 0), 1)
            rationale.append("低收入或中低收入样本通常更依赖外部融资支持。")
        if self._has_conditional_support_signal(conditionality):
            min_requirements["climate_finance"] = max(min_requirements.get("climate_finance", 0), 2)
            rationale.append("NDC 摘要明确写出融资/支持条件，应视为谈判硬约束。")
        if self._has_tech_support_signal(conditionality):
            min_requirements["tech_transfer"] = max(min_requirements.get("tech_transfer", 0), 1)
            rationale.append("承诺文本涉及技术转移或能力建设需求。")

        if target_type in {"intensity_target", "baseline_scenario_target", "fixed_level_trajectory_target"}:
            min_requirements["transition_flexibility"] = max(min_requirements.get("transition_flexibility", 0), 1)
            rationale.append("目标类型依赖情景或强度路径，通常要求一定过渡弹性。")
        if has_lulucf_signal:
            min_requirements["lulucf_support"] = max(min_requirements.get("lulucf_support", 0), 1)
            rationale.append("其公开承诺涉及森林/土地利用治理，谈判中不能完全忽略 LULUCF 议题。")

        if fuel_exports >= 50:
            max_tolerances["fossil_phaseout"] = 1
            max_tolerances["carbon_tariff"] = 1
            min_requirements["ccs_support"] = max(min_requirements.get("ccs_support", 0), 1)
            rationale.append("高燃料出口依赖意味着难以接受过强的化石退出或碳边境约束。")
        elif fuel_exports >= 15:
            max_tolerances["fossil_phaseout"] = 2
            max_tolerances["carbon_tariff"] = 1
            rationale.append("资源与贸易暴露较高，会压低对快速退出和边境约束的容忍度。")

        if gdp_per_capita >= 25000 and readiness >= 0.6 and fuel_exports < 20:
            min_requirements["fossil_phaseout"] = max(min_requirements.get("fossil_phaseout", 0), 2)
            rationale.append("高收入且准备度较高的样本更可能坚持较明确的减排方向。")
        elif target_type == "base_year_target" and fuel_exports < 25:
            min_requirements["fossil_phaseout"] = max(min_requirements.get("fossil_phaseout", 0), 1)
            rationale.append("绝对量或基准年目标通常要求至少保留一定减排雄心。")

        if readiness >= 0.6 and fuel_exports <= 5:
            max_tolerances["transition_flexibility"] = min(max_tolerances.get("transition_flexibility", 3), 2)
            rationale.append("高准备度样本通常不希望过长过渡期弱化承诺可信度。")

        status_note = str(profile["policy_profile"].get("policy_status_note", ""))
        if "no_longer_active" in status_note or "no longer active" in status_note:
            rationale.append("该承诺为最新已提交版本，但当前不具备稳定活跃状态，解读时需保留政治不确定性。")

        return {
            "min_requirements": min_requirements,
            "max_tolerances": max_tolerances,
            "rationale": rationale,
        }

    def _build_country_evidence_basis(self, entity: Dict[str, object], profile: Dict[str, object]) -> List[str]:
        fuel_exports = entity["objective_snapshot"]["fuel_exports_share_merchandise_exports"]
        renewables = entity["objective_snapshot"]["renewable_energy_share_final_consumption"]
        readiness = entity["objective_snapshot"]["nd_gain_readiness"]
        vulnerability = entity["objective_snapshot"]["nd_gain_vulnerability"]
        primary = profile["sources"]["primary"]
        secondary = profile["sources"]["secondary"]
        primary_source = self.source_lookup[primary["source_id"]]["name"]
        secondary_source = self.source_lookup[secondary["source_id"]]["name"]

        evidence = [
            self._format_metric_evidence("燃料出口占比", fuel_exports),
            self._format_metric_evidence("可再生能源占最终能源消费", renewables),
            (
                f"ND-GAIN 脆弱性 {vulnerability['value']}、准备度 {readiness['value']}"
                f"（{readiness['year']}，{self.source_lookup[readiness['source_id']]['name']}）"
            ),
            (
                f"NDC 摘要：目标年份 {profile['policy_profile']['target_year']}，类型 {profile['policy_profile']['target_type']}"
                f"（主来源 {primary_source}，辅助来源 {secondary_source}）"
            ),
        ]
        if profile["policy_profile"]["conditionality_note"]:
            evidence.append(f"承诺解释提示：{profile['policy_profile']['conditionality_note']}")
        if self._has_lulucf_signal(profile):
            evidence.append("结构化提示：其公开承诺明确涉及森林、碳汇或土地利用治理议题。")
        for note in self._build_country_constraint_profile(entity, profile)["rationale"][:2]:
            evidence.append(f"约束依据：{note}")
        return evidence

    def _format_metric_evidence(self, label: str, metric: Dict[str, object]) -> str:
        source_name = self.source_lookup[metric["source_id"]]["name"]
        if metric["value"] is None:
            return f"{label}当前缺失可比值（来源 {source_name}）"
        suffix = metric["unit"] if metric["unit"] != "%" else "%"
        return f"{label} {metric['value']}{suffix}（{metric['year']}，{source_name}）"

    def load_policy(self, path: Path) -> Dict[str, object]:
        policy = json.loads(Path(path).read_text(encoding="utf-8"))
        policy["attributes"] = self._normalize_attributes(policy.get("attributes", {}), policy.get("policy_text", ""))
        return policy

    def get_default_scenarios(self) -> List[Dict[str, object]]:
        return [json.loads(json.dumps(item)) for item in DEFAULT_SCENARIO_LIBRARY]

    def _normalize_attributes(self, attrs: Dict[str, int], policy_text: str) -> Dict[str, int]:
        merged = {key: int(attrs.get(key, 0)) for key in FEATURE_ORDER}
        inferred = self._infer_from_text(policy_text)
        for key, value in inferred.items():
            merged[key] = max(merged[key], value)
        return {key: max(0, min(3, merged[key])) for key in FEATURE_ORDER}

    def _infer_from_text(self, policy_text: str) -> Dict[str, int]:
        text = policy_text.lower()
        attrs = {key: 0 for key in FEATURE_ORDER}

        def has_any(snippets: List[str]) -> bool:
            return any(snippet in policy_text or snippet in text for snippet in snippets)

        negative_markers = {
            "fossil_phaseout": ["不淘汰", "不退出化石能源", "继续新建煤电", "允许新建煤电"],
            "carbon_tariff": ["不实施碳边境", "不提高碳边境", "取消碳边境", "反对碳关税"],
            "climate_finance": ["不新增气候融资", "不增加气候融资", "不提供融资", "不新增融资", "不提供资金支持"],
            "tech_transfer": ["不提供技术转移", "不开展技术转移", "no technology transfer"],
            "transition_flexibility": ["不设过渡期", "不提供过渡期", "no flexibility"],
            "ccs_support": ["不支持ccs", "不支持碳捕集", "no ccs"],
            "adaptation_fund": ["不新增适应补偿", "不提供适应补偿", "不设损失与损害补偿", "不支持适应融资"],
            "lulucf_support": ["不涉及森林", "不保护森林", "不纳入土地利用", "不提供碳汇支持"],
        }

        if not has_any(negative_markers["fossil_phaseout"]) and (
            "煤电" in policy_text or "fossil" in text or "淘汰" in policy_text or "停止新建" in policy_text
        ):
            attrs["fossil_phaseout"] = 2
        if not has_any(negative_markers["carbon_tariff"]) and (
            "碳边境" in policy_text or "碳关税" in policy_text or "tariff" in text or "cbam" in text
        ):
            attrs["carbon_tariff"] = 2
        if not has_any(negative_markers["climate_finance"]) and (
            "资金" in policy_text or "融资" in policy_text or "补偿" in policy_text or "finance" in text
        ):
            attrs["climate_finance"] = 1
        if not has_any(negative_markers["adaptation_fund"]) and (
            "损失" in policy_text or "适应" in policy_text or "loss" in text or "adaptation" in text
        ):
            attrs["adaptation_fund"] = 1
        if not has_any(negative_markers["tech_transfer"]) and (
            "技术转移" in policy_text or "capacity" in text or "technology" in text
        ):
            attrs["tech_transfer"] = 1
        if not has_any(negative_markers["transition_flexibility"]) and (
            "过渡期" in policy_text or "分阶段" in policy_text or "flexibility" in text
        ):
            attrs["transition_flexibility"] = 1
        if not has_any(negative_markers["ccs_support"]) and ("ccs" in text or "碳捕集" in policy_text):
            attrs["ccs_support"] = 1
        if not has_any(negative_markers["lulucf_support"]) and (
            "lulucf" in text
            or "forest" in text
            or "forestry" in text
            or "森林" in policy_text
            or "碳汇" in policy_text
            or "土地利用" in policy_text
        ):
            attrs["lulucf_support"] = 1
        return attrs

    def evaluate_agent(
        self,
        agent: Agent,
        policy_attrs: Dict[str, int],
        policy_text: str = "",
        stage_index: int = 1,
    ) -> Dict[str, object]:
        contributions = {}
        score = agent.base_bias
        for key in FEATURE_ORDER:
            contribution = round(agent.weights[key] * policy_attrs[key], 2)
            contributions[key] = contribution
            score += contribution

        raw_score = round(score, 2)
        raw_status = self._score_to_status(raw_score)
        positives, concerns = self._extract_feature_views(contributions)
        asks = self._build_asks(agent, concerns, policy_attrs)
        adjusted_score, status, concerns, asks, violations = self._apply_constraint_profile(
            agent,
            policy_attrs,
            raw_score,
            raw_status,
            concerns,
            asks,
        )
        statement = self.narrator.render_statement(
            NarrationRequest(
                role_name=agent.name,
                role_description=self._agent_profile_text(agent),
                status_label=STATUS_LABELS[status],
                positive_points=positives,
                concern_points=concerns,
                asks=asks,
                policy_text=policy_text,
                round_index=stage_index,
            )
        )
        return {
            "agent_id": agent.agent_id,
            "role": agent.name,
            "bloc": agent.bloc,
            "description": agent.description,
            "design_rationale": agent.design_rationale,
            "evidence_basis": agent.evidence_basis,
            "raw_score": raw_score,
            "raw_status": raw_status,
            "raw_status_label": STATUS_LABELS[raw_status],
            "score": adjusted_score,
            "status": status,
            "status_label": STATUS_LABELS[status],
            "contributions": contributions,
            "positive_points": positives,
            "concern_points": concerns,
            "asks": asks,
            "constraint_profile": agent.constraint_profile,
            "constraint_violations": violations,
            "statement": statement,
        }

    def _agent_profile_text(self, agent: Agent) -> str:
        evidence = "；".join(agent.evidence_basis[:2]) if agent.evidence_basis else "暂无额外证据说明"
        return f"{agent.description} 设计依据：{agent.design_rationale} 证据基础：{evidence}"

    def _apply_constraint_profile(
        self,
        agent: Agent,
        policy_attrs: Dict[str, int],
        score: float,
        status: str,
        concerns: List[str],
        asks: List[str],
    ) -> Tuple[float, str, List[str], List[str], List[Dict[str, object]]]:
        if not agent.constraint_profile:
            return score, status, concerns, asks, []

        violations: List[Dict[str, object]] = []
        penalty = 0.0
        updated_concerns = list(concerns)
        updated_asks = list(asks)

        for feature, required in agent.constraint_profile.get("min_requirements", {}).items():
            actual = policy_attrs.get(feature, 0)
            if actual >= required:
                continue
            delta = required - actual
            penalty += 1.2 * delta
            message = f"根据其公开承诺与现实约束，{agent.name}至少需要“{FEATURE_LABELS[feature]}”达到 {required}"
            updated_concerns.append(message)
            updated_asks.append(FEATURE_STRENGTHEN_ASKS[feature])
            violations.append(
                {
                    "type": "min_requirement",
                    "feature": FEATURE_LABELS[feature],
                    "required": required,
                    "actual": actual,
                    "message": message,
                }
            )

        for feature, maximum in agent.constraint_profile.get("max_tolerances", {}).items():
            actual = policy_attrs.get(feature, 0)
            if actual <= maximum:
                continue
            delta = actual - maximum
            penalty += 1.2 * delta
            message = f"根据其公开承诺与现实约束，{agent.name}难以接受“{FEATURE_LABELS[feature]}”超过 {maximum}"
            updated_concerns.append(message)
            updated_asks.append(FEATURE_WEAKEN_ASKS[feature])
            violations.append(
                {
                    "type": "max_tolerance",
                    "feature": FEATURE_LABELS[feature],
                    "required": maximum,
                    "actual": actual,
                    "message": message,
                }
            )

        adjusted_score = round(score - penalty, 2)
        adjusted_status = self._score_to_status(adjusted_score)
        if violations and adjusted_status == "support":
            adjusted_status = "conditional_support"
        return adjusted_score, adjusted_status, self._dedupe_list(updated_concerns), self._dedupe_list(updated_asks), violations

    def _dedupe_list(self, items: List[str]) -> List[str]:
        deduped: List[str] = []
        for item in items:
            if item and item not in deduped:
                deduped.append(item)
        return deduped[:4]

    def _score_to_status(self, score: float) -> str:
        if score >= 4.0:
            return "support"
        if score >= 1.2:
            return "conditional_support"
        if score >= -1.5:
            return "conditional_oppose"
        return "oppose"

    def _extract_feature_views(self, contributions: Dict[str, float]) -> Tuple[List[str], List[str]]:
        positives = [item for item in contributions.items() if item[1] > 0.45]
        concerns = [item for item in contributions.items() if item[1] < -0.45]
        positives.sort(key=lambda item: item[1], reverse=True)
        concerns.sort(key=lambda item: item[1])
        positive_points = [FEATURE_TALKING_POINTS[key] for key, _ in positives[:2]]
        concern_points = [f"当前方案对“{FEATURE_LABELS[key]}”的处理让我们难以接受" for key, _ in concerns[:2]]
        return positive_points, concern_points

    def _build_asks(self, agent: Agent, concerns: List[str], policy_attrs: Dict[str, int]) -> List[str]:
        asks = []
        for feature in agent.priority_asks:
            current = policy_attrs[feature]
            weight = agent.weights[feature]
            if weight > 0 and current < 2:
                asks.append(FEATURE_STRENGTHEN_ASKS[feature])
            elif weight < 0 and current > 1:
                asks.append(FEATURE_WEAKEN_ASKS[feature])
            if len(asks) >= 3:
                break
        if not asks and concerns:
            asks.append("请针对争议点给出更可执行的妥协版本")
        return asks[:3]

    def _evaluate_all_agents(
        self,
        policy_attrs: Dict[str, int],
        policy_text: str,
        stage_index: int,
    ) -> List[Dict[str, object]]:
        return [self.evaluate_agent(agent, policy_attrs, policy_text=policy_text, stage_index=stage_index) for agent in self.agents]

    def run(self, policy: Dict[str, object], rounds: int = 3) -> Dict[str, object]:
        del rounds  # 2.0 beta 使用固定的六阶段谈判流程
        policy_text = str(policy["policy_text"])
        initial_attrs = self._normalize_attributes(dict(policy["attributes"]), policy_text)
        initial_vote = self._evaluate_all_agents(initial_attrs, policy_text, stage_index=1)

        conflict_summary = self._observer_stage_summary(initial_vote, initial_attrs, "初始表态")
        alliance_map = self._build_alliance_map(initial_vote)
        bargaining_package = self._build_bargaining_package(initial_vote, initial_attrs, conflict_summary, alliance_map)
        revised_attrs = self._apply_adjustments_copy(initial_attrs, bargaining_package["adjustments"])
        final_vote = self._evaluate_all_agents(revised_attrs, policy_text, stage_index=2)
        final_summary = self._observer_stage_summary(final_vote, revised_attrs, "最终表决")

        return self._build_final_report(
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

    def _observer_stage_summary(
        self,
        agent_results: List[Dict[str, object]],
        policy_attrs: Dict[str, int],
        stage_label: str,
    ) -> Dict[str, object]:
        status_counter = {key: 0 for key in STATUS_LABELS}
        concern_weight = {key: 0.0 for key in FEATURE_ORDER}
        for result in agent_results:
            status_counter[result["status"]] += 1
            for feature, contribution in result["contributions"].items():
                if contribution < 0:
                    concern_weight[feature] += abs(contribution)
        ranked_concerns = sorted(concern_weight.items(), key=lambda item: item[1], reverse=True)
        top_concerns = [FEATURE_LABELS[key] for key, value in ranked_concerns[:3] if value > 0]
        suggested_adjustments = self._recommend_adjustments(agent_results, policy_attrs)
        summary_text = (
            f"{stage_label}阶段判断：主要冲突集中在"
            f"{'、'.join(top_concerns) if top_concerns else '当前分歧相对可控'}；"
            f"建议优先处理：{self._format_adjustments(suggested_adjustments)}。"
        )
        return {
            "status_counter": status_counter,
            "top_concerns": top_concerns,
            "suggested_adjustments": suggested_adjustments,
            "summary_text": summary_text,
        }

    def _recommend_adjustments(
        self,
        agent_results: List[Dict[str, object]],
        policy_attrs: Dict[str, int],
    ) -> Dict[str, int]:
        pressure = {key: 0.0 for key in FEATURE_ORDER}
        for result in agent_results:
            if result["status"] not in {"conditional_oppose", "oppose"}:
                continue
            agent = self.agent_lookup[result["agent_id"]]
            intensity = 1.0 if result["status"] == "oppose" else 0.6
            for feature in agent.priority_asks[:3]:
                current = policy_attrs[feature]
                weight = agent.weights[feature]
                if weight > 0 and current < 3:
                    pressure[feature] += intensity
                elif weight < 0 and current > 0:
                    pressure[feature] -= intensity

        adjustments = {}
        for key, value in pressure.items():
            if value >= 0.9:
                adjustments[key] = 1
            elif value <= -0.9:
                adjustments[key] = -1
            else:
                adjustments[key] = 0
        return adjustments

    def _build_alliance_map(self, agent_results: List[Dict[str, object]]) -> Dict[str, object]:
        ambition_members = [
            item["role"]
            for item in agent_results
            if item["contributions"]["fossil_phaseout"] > 0.8 or item["contributions"]["adaptation_fund"] > 0.8
        ]
        finance_members = [
            item["role"]
            for item in agent_results
            if "气候资金支持" in " ".join(item["concern_points"]) or "适应/损失补偿支持" in " ".join(item["concern_points"])
        ]
        forest_members = [
            item["role"]
            for item in agent_results
            if item["contributions"].get("lulucf_support", 0.0) > 0.6
        ]
        transition_members = [
            item["role"]
            for item in agent_results
            if item["contributions"]["transition_flexibility"] > 0.8 or item["contributions"]["ccs_support"] > 0.8
        ]
        splinters = [
            {
                "role": item["role"],
                "status": item["status_label"],
                "note": "立场处在中间地带，可能成为交换条件中的关键摇摆方。",
            }
            for item in agent_results
            if item["status"] in {"conditional_support", "conditional_oppose"}
        ]
        alliances = []
        if ambition_members:
            alliances.append(
                {
                    "name": "高雄心联盟",
                    "members": ambition_members,
                    "basis": "共同支持更强减排或更明确的脆弱国家补偿安排。",
                }
            )
        if finance_members:
            alliances.append(
                {
                    "name": "公平融资联盟",
                    "members": finance_members,
                    "basis": "希望把资金、适应和能力建设写进最终方案。",
                }
            )
        if transition_members:
            alliances.append(
                {
                    "name": "过渡缓冲联盟",
                    "members": transition_members,
                    "basis": "强调更长过渡期、CCS 或避免过快退出造成的冲击。",
                }
            )
        if forest_members:
            alliances.append(
                {
                    "name": "森林与碳汇联盟",
                    "members": forest_members,
                    "basis": "强调森林保护、土地利用治理和碳汇贡献在整体减排中的作用。",
                }
            )
        return {
            "alliances": alliances,
            "splinters": splinters,
        }

    def _build_bargaining_package(
        self,
        agent_results: List[Dict[str, object]],
        policy_attrs: Dict[str, int],
        conflict_summary: Dict[str, object],
        alliance_map: Dict[str, object],
    ) -> Dict[str, object]:
        adjustments = self._recommend_adjustments(agent_results, policy_attrs)
        tradeoffs = []
        if adjustments["climate_finance"] > 0 or adjustments["adaptation_fund"] > 0:
            tradeoffs.append("用更明确的资金与适应安排交换更高减排接受度")
        if adjustments["transition_flexibility"] > 0 or adjustments["ccs_support"] > 0:
            tradeoffs.append("用过渡期和技术路线缓冲高冲击退出要求")
        if adjustments["lulucf_support"] > 0:
            tradeoffs.append("用森林保护、碳汇和土地利用治理安排增强新兴经济体与森林国家接受度")
        if adjustments["carbon_tariff"] < 0:
            tradeoffs.append("适度弱化单边边境约束以减少贸易型反弹")
        if adjustments["fossil_phaseout"] > 0:
            tradeoffs.append("保留高雄心目标，避免谈判完全滑向最低共识")

        alliance_names = [item["name"] for item in alliance_map["alliances"]]
        summary_text = (
            f"条件交换阶段围绕 {self._format_adjustments(adjustments)} 展开；"
            f"主要需要在 {'、'.join(alliance_names) if alliance_names else '零散立场方'} 之间达成最小可接受交换。"
        )
        return {
            "adjustments": adjustments,
            "tradeoffs": tradeoffs,
            "summary_text": summary_text,
            "trigger_conflicts": conflict_summary["top_concerns"],
        }

    def _apply_adjustments_copy(self, policy_attrs: Dict[str, int], adjustments: Dict[str, int]) -> Dict[str, int]:
        revised = dict(policy_attrs)
        for key, delta in adjustments.items():
            revised[key] = max(0, min(3, revised[key] + delta))
        return revised

    def _format_adjustments(self, adjustments: Dict[str, int]) -> str:
        parts = []
        for key in FEATURE_ORDER:
            delta = adjustments[key]
            if delta > 0:
                parts.append(f"提高{FEATURE_LABELS[key]}")
            elif delta < 0:
                parts.append(f"弱化{FEATURE_LABELS[key]}")
        return "、".join(parts) if parts else "保持现有政策框架"

    def _build_feature_deltas(self, before: Dict[str, int], after: Dict[str, int]) -> List[Dict[str, object]]:
        rows = []
        for key in FEATURE_ORDER:
            rows.append(
                {
                    "feature": FEATURE_LABELS[key],
                    "before": before[key],
                    "after": after[key],
                    "delta": after[key] - before[key],
                }
            )
        return rows

    def _build_vote_shift(
        self,
        initial_vote: List[Dict[str, object]],
        final_vote: List[Dict[str, object]],
    ) -> List[Dict[str, object]]:
        initial_lookup = {item["agent_id"]: item for item in initial_vote}
        rows = []
        for final_item in final_vote:
            initial_item = initial_lookup[final_item["agent_id"]]
            rows.append(
                {
                    "role": final_item["role"],
                    "bloc": final_item["bloc"],
                    "initial_status": initial_item["status_label"],
                    "final_status": final_item["status_label"],
                    "score_change": round(final_item["score"] - initial_item["score"], 2),
                }
            )
        return rows

    def _build_agent_catalog(self) -> List[Dict[str, object]]:
        return [
            {
                "role": agent.name,
                "bloc": agent.bloc,
                "description": agent.description,
                "design_rationale": agent.design_rationale,
                "evidence_basis": agent.evidence_basis,
                "constraint_profile": agent.constraint_profile,
            }
            for agent in self.agents
        ]

    def _agent_mode_label(self) -> str:
        return "真实国家样本模式" if self.agent_mode == "real_countries" else "抽象角色模式"

    def _build_final_report(
        self,
        policy: Dict[str, object],
        initial_attrs: Dict[str, int],
        initial_vote: List[Dict[str, object]],
        conflict_summary: Dict[str, object],
        alliance_map: Dict[str, object],
        bargaining_package: Dict[str, object],
        revised_attrs: Dict[str, int],
        final_vote: List[Dict[str, object]],
        final_summary: Dict[str, object],
    ) -> Dict[str, object]:
        final_statuses = [item["status"] for item in final_vote]
        feasibility = round(sum(STATUS_SCORE[status] for status in final_statuses) / (len(final_statuses) * 3) * 100, 1)
        fairness = round(
            (
                revised_attrs["climate_finance"]
                + revised_attrs["tech_transfer"]
                + revised_attrs["adaptation_fund"]
                + revised_attrs["transition_flexibility"]
                + revised_attrs["lulucf_support"]
            )
            / 15
            * 100,
            1,
        )
        resistance = round(100 - feasibility + revised_attrs["carbon_tariff"] * 3, 1)
        consensus = self._consensus_label(final_statuses)
        compromise = self._summarize_compromise(revised_attrs)
        feature_deltas = self._build_feature_deltas(initial_attrs, revised_attrs)
        vote_shift = self._build_vote_shift(initial_vote, final_vote)

        return {
            "project": "气候政策多利益相关方博弈沙盘 Prototype 2.0 beta",
            "agent_mode": {
                "id": self.agent_mode,
                "label": self._agent_mode_label(),
            },
            "input_policy": {
                "title": policy["title"],
                "policy_text": policy["policy_text"],
                "attributes": initial_attrs,
            },
            "pipeline_stages": [{"stage_id": key, "label": label} for key, label in PIPELINE_STAGES],
            "stage_results": [
                {
                    "stage_id": "position_statement",
                    "label": "立场陈述",
                    "policy_attributes": initial_attrs,
                    "agent_results": initial_vote,
                    "summary_text": "各角色先依据自身约束条件给出初始表态。",
                },
                {
                    "stage_id": "conflict_id",
                    "label": "冲突识别",
                    "summary_text": conflict_summary["summary_text"],
                    "top_concerns": conflict_summary["top_concerns"],
                    "status_counter": conflict_summary["status_counter"],
                },
                {
                    "stage_id": "alliance_mapping",
                    "label": "联盟与分裂",
                    "alliances": alliance_map["alliances"],
                    "splinters": alliance_map["splinters"],
                    "summary_text": "根据共同诉求识别潜在联盟与关键摇摆方。",
                },
                {
                    "stage_id": "bargaining",
                    "label": "条件交换",
                    "adjustments": bargaining_package["adjustments"],
                    "tradeoffs": bargaining_package["tradeoffs"],
                    "summary_text": bargaining_package["summary_text"],
                },
                {
                    "stage_id": "secretariat_revision",
                    "label": "秘书处修订",
                    "policy_attributes": revised_attrs,
                    "feature_deltas": feature_deltas,
                    "summary_text": f"秘书处据此形成修订文本：{self._format_adjustments(bargaining_package['adjustments'])}。",
                },
                {
                    "stage_id": "final_vote",
                    "label": "最终表决",
                    "policy_attributes": revised_attrs,
                    "agent_results": final_vote,
                    "summary_text": final_summary["summary_text"],
                    "status_counter": final_summary["status_counter"],
                },
            ],
            "alliance_map": alliance_map,
            "feature_deltas": feature_deltas,
            "vote_shift": vote_shift,
            "agent_catalog": self._build_agent_catalog(),
            "final_scores": {
                "feasibility": feasibility,
                "fairness": fairness,
                "resistance": resistance,
            },
            "consensus_label": consensus,
            "dominant_resistance_sources": conflict_summary["top_concerns"],
            "compromise_path": compromise,
            "final_positions": [
                {
                    "role": item["role"],
                    "bloc": item["bloc"],
                    "status": item["status_label"],
                    "score": item["score"],
                    "asks": item["asks"],
                }
                for item in final_vote
            ],
        }

    def run_scenario_batch(self, policy_text: str, scenarios: List[Dict[str, object]] | None = None) -> Dict[str, object]:
        scenario_defs = scenarios or self.get_default_scenarios()
        reports = []
        comparison_rows = []
        constraint_counter: Counter[str] = Counter()
        actor_status_counter: Dict[str, Counter[str]] = {}

        for scenario in scenario_defs:
            base_attrs = self._normalize_attributes({}, policy_text)
            scenario_attrs = self._merge_scenario_attrs(base_attrs, scenario.get("attribute_overrides", {}))
            report = self.run(
                {
                    "title": str(scenario["label"]),
                    "policy_text": policy_text,
                    "attributes": scenario_attrs,
                }
            )
            support_count, conditional_support_count, oppose_count = self._count_statuses(report["stage_results"][-1]["agent_results"])
            constraint_hits = self._collect_constraint_hits(report["stage_results"][-1]["agent_results"])
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

        findings = self._build_scenario_findings(comparison_rows, constraint_counter, actor_status_counter)
        methods = self._build_method_limitations()

        return {
            "policy_text": policy_text,
            "agent_mode": self._agent_mode_label(),
            "scenario_count": len(reports),
            "scenario_reports": reports,
            "comparison_table": comparison_rows,
            "research_findings": findings,
            "method_notes": methods,
        }

    def _merge_scenario_attrs(self, base_attrs: Dict[str, int], overrides: Dict[str, int]) -> Dict[str, int]:
        merged = dict(base_attrs)
        for key in FEATURE_ORDER:
            if key in overrides:
                merged[key] = max(0, min(3, int(overrides[key])))
        return merged

    def _count_statuses(self, agent_results: List[Dict[str, object]]) -> Tuple[int, int, int]:
        support_count = sum(1 for item in agent_results if item["status"] == "support")
        conditional_support_count = sum(1 for item in agent_results if item["status"] == "conditional_support")
        oppose_count = sum(1 for item in agent_results if item["status"] in {"conditional_oppose", "oppose"})
        return support_count, conditional_support_count, oppose_count

    def _collect_constraint_hits(self, agent_results: List[Dict[str, object]]) -> List[Dict[str, object]]:
        hits = []
        for item in agent_results:
            for violation in item.get("constraint_violations", []):
                hits.append(
                    {
                        "role": item["role"],
                        "feature": violation["feature"],
                        "message": violation["message"],
                    }
                )
        return hits

    def _build_scenario_findings(
        self,
        comparison_rows: List[Dict[str, object]],
        constraint_counter: Counter[str],
        actor_status_counter: Dict[str, Counter[str]],
    ) -> List[str]:
        findings: List[str] = []
        if comparison_rows:
            best_feasibility = max(comparison_rows, key=lambda row: row["可行性"])
            best_fairness = max(comparison_rows, key=lambda row: row["公平性"])
            lowest_resistance = min(comparison_rows, key=lambda row: row["阻力强度"])
            findings.append(f"可行性最高的情景是“{best_feasibility['情景']}”，可行性为 {best_feasibility['可行性']}。")
            findings.append(f"公平性最高的情景是“{best_fairness['情景']}”，公平性为 {best_fairness['公平性']}。")
            findings.append(f"阻力最小的情景是“{lowest_resistance['情景']}”，阻力强度为 {lowest_resistance['阻力强度']}。")
        if constraint_counter:
            top_feature, top_count = constraint_counter.most_common(1)[0]
            findings.append(f"最常触发的现实约束是“{top_feature}”，在批量情景中共触发 {top_count} 次。")
        if actor_status_counter:
            swing_actor = max(
                actor_status_counter.items(),
                key=lambda item: len([status for status, count in item[1].items() if count > 0]),
            )
            findings.append(f"最敏感的角色是“{swing_actor[0]}”，其立场在不同情景间出现了多种变化。")
        findings.append("当前批量情景的作用不在于给出唯一正确答案，而在于识别哪些政策维度最容易改变联盟结构与可接受边界。")
        return findings

    def _build_method_limitations(self) -> Dict[str, List[str]]:
        return {
            "method": [
                "先对政策文本做结构化属性识别，再叠加情景设定形成可比实验。",
                "真实国家样本模式下，国家权重与约束由 World Bank、ND-GAIN 和结构化 NDC 摘要共同生成。",
                "批量情景比较主要观察可行性、公平性、阻力强度、联盟变化与约束触发频率。",
            ],
            "limitations": [
                "当前仍属于规则驱动的现实约束近似，而非计量模型或 IAM。",
                "政策属性仍是研究建模框架，不等同于现实政策天然自带的数据字段。",
                "部分国家承诺存在政治状态变化或集团嵌套关系，解释时必须保留制度背景说明。",
            ],
        }

    def _consensus_label(self, statuses: List[str]) -> str:
        if statuses.count("support") >= 4 and "oppose" not in statuses:
            return "较强共识"
        if statuses.count("oppose") == 0:
            return "脆弱共识"
        if statuses.count("oppose") <= 2:
            return "有限妥协"
        return "分歧仍然明显"

    def _summarize_compromise(self, attrs: Dict[str, int]) -> str:
        parts = []
        if attrs["climate_finance"] >= 2:
            parts.append("增加气候资金支持")
        if attrs["tech_transfer"] >= 2:
            parts.append("增加技术转移安排")
        if attrs["transition_flexibility"] >= 2:
            parts.append("加入分阶段过渡期")
        if attrs["ccs_support"] >= 2:
            parts.append("保留 CCS 过渡路线")
        if attrs["adaptation_fund"] >= 2:
            parts.append("补充适应与损失补偿机制")
        if attrs["lulucf_support"] >= 2:
            parts.append("补充森林保护与碳汇治理安排")
        if attrs["carbon_tariff"] <= 1:
            parts.append("弱化单边碳边境约束")
        if attrs["fossil_phaseout"] >= 2:
            parts.append("维持较明确的减排方向")
        return "、".join(parts) if parts else "暂未形成明确妥协路径"


def render_markdown_report(report: Dict[str, object]) -> str:
    lines = []
    lines.append(f"# {report['project']}\n")
    lines.append("## 输入政策\n")
    lines.append(f"- 推演主体模式：{report['agent_mode']['label']}")
    lines.append(f"- 标题：{report['input_policy']['title']}")
    lines.append(f"- 文本：{report['input_policy']['policy_text']}")
    lines.append("- 初始属性：")
    for key in FEATURE_ORDER:
        lines.append(f"  - {FEATURE_LABELS[key]}：{report['input_policy']['attributes'][key]}")

    lines.append("\n## 六阶段谈判流程\n")
    for stage in report["stage_results"]:
        lines.append(f"### {stage['label']}")
        lines.append(f"- 阶段说明：{stage['summary_text']}")
        if "top_concerns" in stage:
            lines.append(f"- 主要冲突：{', '.join(stage['top_concerns']) if stage['top_concerns'] else '无明显集中冲突'}")
        if "policy_attributes" in stage:
            lines.append("- 当前政策属性：")
            for key in FEATURE_ORDER:
                lines.append(f"  - {FEATURE_LABELS[key]}：{stage['policy_attributes'][key]}")
        if "agent_results" in stage:
            lines.append("- 角色表态：")
            for agent_result in stage["agent_results"]:
                lines.append(
                    f"  - {agent_result['role']}（{agent_result['status_label']}，得分 {agent_result['score']}）："
                    f"{agent_result['statement']}"
                )
        if "alliances" in stage:
            lines.append("- 潜在联盟：")
            for alliance in stage["alliances"]:
                lines.append(f"  - {alliance['name']}：{', '.join(alliance['members'])}")
        if "splinters" in stage and stage["splinters"]:
            lines.append("- 关键摇摆方：")
            for splinter in stage["splinters"]:
                lines.append(f"  - {splinter['role']}：{splinter['status']}。{splinter['note']}")
        if "tradeoffs" in stage and stage["tradeoffs"]:
            lines.append("- 主要交换条件：")
            for tradeoff in stage["tradeoffs"]:
                lines.append(f"  - {tradeoff}")
        if "feature_deltas" in stage:
            lines.append("- 修订结果：")
            for item in stage["feature_deltas"]:
                lines.append(f"  - {item['feature']}：{item['before']} -> {item['after']}（变化 {item['delta']}）")
        lines.append("")

    lines.append("## 最终结果\n")
    lines.append(f"- 共识水平：{report['consensus_label']}")
    lines.append(f"- 落地可行性：{report['final_scores']['feasibility']}")
    lines.append(f"- 公平性：{report['final_scores']['fairness']}")
    lines.append(f"- 阻力强度：{report['final_scores']['resistance']}")
    lines.append(f"- 主要阻力来源：{', '.join(report['dominant_resistance_sources'])}")
    lines.append(f"- 妥协路径：{report['compromise_path']}")
    lines.append("- 最终角色立场：")
    for item in report["final_positions"]:
        lines.append(f"  - {item['role']}（{item['bloc']}）：{item['status']}（得分 {item['score']}）")

    lines.append("\n## 2.0 Beta 观察\n")
    lines.append("- 当前版本已从单纯三轮调参升级为六阶段谈判 pipeline。")
    lines.append("- 角色扩展到 7 类，并将设计依据和证据基础写入角色配置。")
    lines.append("- 规则层继续负责稳定性，LLM 主要负责把结构化立场转成更自然的谈判表述。")
    return "\n".join(lines) + "\n"
