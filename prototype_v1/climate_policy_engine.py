"""气候政策多利益相关方博弈沙盘 1.0 核心引擎。"""

from __future__ import annotations

import json
from dataclasses import dataclass
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
]

FEATURE_LABELS = {
    "fossil_phaseout": "化石能源退出强度",
    "carbon_tariff": "碳边境约束强度",
    "climate_finance": "气候资金支持",
    "tech_transfer": "技术转移支持",
    "transition_flexibility": "过渡期灵活性",
    "ccs_support": "CCS 过渡技术支持",
    "adaptation_fund": "适应/损失补偿支持",
}

FEATURE_TALKING_POINTS = {
    "fossil_phaseout": "更明确地限制高排放能源扩张",
    "carbon_tariff": "以更强的边境约束推动减排责任传导",
    "climate_finance": "增加气候资金与转型补偿安排",
    "tech_transfer": "提供更可落地的技术转移与能力建设",
    "transition_flexibility": "允许分阶段过渡并保留政策弹性",
    "ccs_support": "保留 CCS 等过渡技术选项",
    "adaptation_fund": "补充适应与损失补偿机制",
}

FEATURE_ASKS = {
    "fossil_phaseout": "细化退出路径，避免一刀切冲击",
    "carbon_tariff": "弱化单边碳边境约束或增加豁免机制",
    "climate_finance": "增加更明确的资金支持承诺",
    "tech_transfer": "增加技术转移和能力建设支持",
    "transition_flexibility": "加入更长的过渡期和分阶段安排",
    "ccs_support": "保留 CCS 等过渡技术路线",
    "adaptation_fund": "加入损失与损害或适应补偿安排",
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


@dataclass
class Agent:
    agent_id: str
    name: str
    description: str
    base_bias: float
    weights: Dict[str, float]


class ClimatePolicySandbox:
    def __init__(self, base_dir: Path) -> None:
        self.base_dir = Path(base_dir)
        self.narrator = build_narrator()
        self.agents = self._load_agents(self.base_dir / "data" / "agents.json")

    def _load_agents(self, path: Path) -> List[Agent]:
        raw = json.loads(path.read_text(encoding="utf-8"))
        return [
            Agent(
                agent_id=item["id"],
                name=item["name"],
                description=item["description"],
                base_bias=item["base_bias"],
                weights=item["weights"],
            )
            for item in raw
        ]

    def load_policy(self, path: Path) -> Dict[str, object]:
        policy = json.loads(Path(path).read_text(encoding="utf-8"))
        policy["attributes"] = self._normalize_attributes(policy.get("attributes", {}), policy.get("policy_text", ""))
        return policy

    def _normalize_attributes(self, attrs: Dict[str, int], policy_text: str) -> Dict[str, int]:
        merged = {key: int(attrs.get(key, 0)) for key in FEATURE_ORDER}
        inferred = self._infer_from_text(policy_text)
        for key, value in inferred.items():
            merged[key] = max(merged[key], value)
        return {key: max(0, min(3, merged[key])) for key in FEATURE_ORDER}

    def _infer_from_text(self, policy_text: str) -> Dict[str, int]:
        text = policy_text.lower()
        attrs = {key: 0 for key in FEATURE_ORDER}
        if "煤电" in policy_text or "fossil" in text or "淘汰" in policy_text or "停止新建" in policy_text:
            attrs["fossil_phaseout"] = 2
        if "碳边境" in policy_text or "碳关税" in policy_text or "tariff" in text:
            attrs["carbon_tariff"] = 2
        if "资金" in policy_text or "融资" in policy_text or "补偿" in policy_text:
            attrs["climate_finance"] = 1
            attrs["adaptation_fund"] = 1
        if "技术转移" in policy_text or "capacity" in text or "technology" in text:
            attrs["tech_transfer"] = 1
        if "过渡期" in policy_text or "分阶段" in policy_text:
            attrs["transition_flexibility"] = 1
        if "ccs" in text or "碳捕集" in policy_text:
            attrs["ccs_support"] = 1
        return attrs

    def evaluate_agent(self, agent: Agent, policy_attrs: Dict[str, int]) -> Dict[str, object]:
        contributions = {}
        score = agent.base_bias
        for key in FEATURE_ORDER:
            contribution = round(agent.weights[key] * policy_attrs[key], 2)
            contributions[key] = contribution
            score += contribution
        status = self._score_to_status(score)
        positives, concerns = self._extract_feature_views(contributions)
        asks = self._build_asks(concerns, policy_attrs, agent.agent_id)
        statement = self.narrator.render_statement(
            NarrationRequest(
                role_name=agent.name,
                role_description=agent.description,
                status_label=STATUS_LABELS[status],
                positive_points=positives,
                concern_points=concerns,
                asks=asks,
                policy_text="",
                round_index=1,
            )
        )
        return {
            "agent_id": agent.agent_id,
            "role": agent.name,
            "description": agent.description,
            "score": round(score, 2),
            "status": status,
            "status_label": STATUS_LABELS[status],
            "contributions": contributions,
            "positive_points": positives,
            "concern_points": concerns,
            "asks": asks,
            "statement": statement,
        }

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

    def _build_asks(self, concerns: List[str], policy_attrs: Dict[str, int], agent_id: str) -> List[str]:
        asks = []
        if agent_id == "developing_country":
            if policy_attrs["climate_finance"] < 2:
                asks.append(FEATURE_ASKS["climate_finance"])
            if policy_attrs["transition_flexibility"] < 2:
                asks.append(FEATURE_ASKS["transition_flexibility"])
            if policy_attrs["tech_transfer"] < 2:
                asks.append(FEATURE_ASKS["tech_transfer"])
        elif agent_id == "developed_alliance":
            if policy_attrs["fossil_phaseout"] < 3:
                asks.append("增加更清晰的减排时间表和执行约束")
            if policy_attrs["carbon_tariff"] < 2:
                asks.append("保留一定强度的国际规则约束")
        elif agent_id == "fossil_industry":
            if policy_attrs["transition_flexibility"] < 2:
                asks.append(FEATURE_ASKS["transition_flexibility"])
            if policy_attrs["ccs_support"] < 2:
                asks.append(FEATURE_ASKS["ccs_support"])
        elif agent_id == "island_ngo":
            if policy_attrs["adaptation_fund"] < 2:
                asks.append(FEATURE_ASKS["adaptation_fund"])
            if policy_attrs["climate_finance"] < 2:
                asks.append(FEATURE_ASKS["climate_finance"])
            if policy_attrs["fossil_phaseout"] < 3:
                asks.append("提高淘汰化石能源的雄心")
        if not asks and concerns:
            asks.append("对争议点给出更可执行的妥协版本")
        return asks[:3]

    def run(self, policy: Dict[str, object], rounds: int = 3) -> Dict[str, object]:
        policy_text = str(policy["policy_text"])
        policy_attrs = dict(policy["attributes"])
        round_results = []
        adjustment_history = []

        for round_index in range(1, rounds + 1):
            agent_results = []
            for agent in self.agents:
                result = self.evaluate_agent(agent, policy_attrs)
                result["statement"] = self.narrator.render_statement(
                    NarrationRequest(
                        role_name=agent.name,
                        role_description=agent.description,
                        status_label=result["status_label"],
                        positive_points=result["positive_points"],
                        concern_points=result["concern_points"],
                        asks=result["asks"],
                        policy_text=policy_text,
                        round_index=round_index,
                    )
                )
                agent_results.append(result)

            observer_summary, adjustments = self._observer_round_summary(agent_results, policy_attrs, round_index)
            round_results.append(
                {
                    "round": round_index,
                    "policy_attributes": dict(policy_attrs),
                    "agent_results": agent_results,
                    "observer_summary": observer_summary,
                }
            )
            adjustment_history.append({"round": round_index, "adjustments": adjustments})
            if round_index < rounds:
                self._apply_adjustments(policy_attrs, adjustments)

        final_positions = round_results[-1]["agent_results"]
        report = self._build_final_report(policy, round_results, adjustment_history, final_positions)
        return report

    def _observer_round_summary(self, agent_results: List[Dict[str, object]], policy_attrs: Dict[str, int], round_index: int) -> Tuple[Dict[str, object], Dict[str, int]]:
        status_counter = {key: 0 for key in STATUS_LABELS}
        concern_weight = {key: 0.0 for key in FEATURE_ORDER}
        for result in agent_results:
            status_counter[result["status"]] += 1
            for feature, contribution in result["contributions"].items():
                if contribution < 0:
                    concern_weight[feature] += abs(contribution)
        ranked_concerns = sorted(concern_weight.items(), key=lambda item: item[1], reverse=True)
        top_concerns = [FEATURE_LABELS[key] for key, value in ranked_concerns[:3] if value > 0]
        adjustments = self._recommend_adjustments(agent_results, policy_attrs)
        summary_text = (
            f"第 {round_index} 轮观察员判断：当前主要冲突集中在 {', '.join(top_concerns) if top_concerns else '立场分歧较小'}。"
            f" 建议下一轮优先调整：{self._format_adjustments(adjustments)}。"
        )
        return {
            "status_counter": status_counter,
            "top_concerns": top_concerns,
            "summary_text": summary_text,
        }, adjustments

    def _recommend_adjustments(self, agent_results: List[Dict[str, object]], policy_attrs: Dict[str, int]) -> Dict[str, int]:
        adjustments = {key: 0 for key in FEATURE_ORDER}
        lookup = {item["agent_id"]: item for item in agent_results}

        dev_status = lookup["developing_country"]["status"]
        ind_status = lookup["fossil_industry"]["status"]
        isl_status = lookup["island_ngo"]["status"]
        devd_status = lookup["developed_alliance"]["status"]

        if dev_status in {"oppose", "conditional_oppose"}:
            if policy_attrs["climate_finance"] < 2:
                adjustments["climate_finance"] += 1
            if policy_attrs["transition_flexibility"] < 2:
                adjustments["transition_flexibility"] += 1
            if policy_attrs["tech_transfer"] < 2:
                adjustments["tech_transfer"] += 1
            if policy_attrs["carbon_tariff"] > 1:
                adjustments["carbon_tariff"] -= 1

        if ind_status in {"oppose", "conditional_oppose"}:
            if policy_attrs["ccs_support"] < 2:
                adjustments["ccs_support"] += 1
            if policy_attrs["transition_flexibility"] < 2:
                adjustments["transition_flexibility"] += 1

        if isl_status in {"oppose", "conditional_oppose"}:
            if policy_attrs["adaptation_fund"] < 2:
                adjustments["adaptation_fund"] += 1
            if policy_attrs["climate_finance"] < 2:
                adjustments["climate_finance"] += 1
            if policy_attrs["fossil_phaseout"] < 3:
                adjustments["fossil_phaseout"] += 1

        if devd_status in {"conditional_oppose", "oppose"}:
            if policy_attrs["fossil_phaseout"] < 3:
                adjustments["fossil_phaseout"] += 1
            if policy_attrs["carbon_tariff"] < 2:
                adjustments["carbon_tariff"] += 1

        return adjustments

    def _apply_adjustments(self, policy_attrs: Dict[str, int], adjustments: Dict[str, int]) -> None:
        for key, delta in adjustments.items():
            policy_attrs[key] = max(0, min(3, policy_attrs[key] + delta))

    def _format_adjustments(self, adjustments: Dict[str, int]) -> str:
        parts = []
        for key in FEATURE_ORDER:
            delta = adjustments[key]
            if delta > 0:
                parts.append(f"提高{FEATURE_LABELS[key]}")
            elif delta < 0:
                parts.append(f"弱化{FEATURE_LABELS[key]}")
        return "、".join(parts) if parts else "保持现有政策框架"

    def _build_final_report(self, policy: Dict[str, object], round_results: List[Dict[str, object]], adjustment_history: List[Dict[str, object]], final_positions: List[Dict[str, object]]) -> Dict[str, object]:
        final_statuses = [item["status"] for item in final_positions]
        feasibility = round(sum(STATUS_SCORE[status] for status in final_statuses) / (len(final_statuses) * 3) * 100, 1)
        fairness = round(
            (
                round_results[-1]["policy_attributes"]["climate_finance"]
                + round_results[-1]["policy_attributes"]["tech_transfer"]
                + round_results[-1]["policy_attributes"]["adaptation_fund"]
                + round_results[-1]["policy_attributes"]["transition_flexibility"]
            )
            / 12
            * 100,
            1,
        )
        resistance = round(100 - feasibility + round_results[-1]["policy_attributes"]["carbon_tariff"] * 3, 1)
        consensus = self._consensus_label(final_statuses)
        dominant_resistance = round_results[0]["observer_summary"]["top_concerns"]
        compromise = self._summarize_compromise(round_results[-1]["policy_attributes"])
        return {
            "project": "气候政策多利益相关方博弈沙盘 Prototype 1.0",
            "input_policy": policy,
            "round_results": round_results,
            "adjustment_history": adjustment_history,
            "final_scores": {
                "feasibility": feasibility,
                "fairness": fairness,
                "resistance": resistance,
            },
            "consensus_label": consensus,
            "dominant_resistance_sources": dominant_resistance,
            "compromise_path": compromise,
            "final_positions": [
                {
                    "role": item["role"],
                    "status": item["status_label"],
                    "score": item["score"],
                    "asks": item["asks"],
                }
                for item in final_positions
            ],
        }

    def _consensus_label(self, statuses: List[str]) -> str:
        if statuses.count("support") >= 3 and "oppose" not in statuses:
            return "较强共识"
        if statuses.count("oppose") == 0:
            return "脆弱共识"
        if statuses.count("oppose") == 1:
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
        if attrs["carbon_tariff"] <= 1:
            parts.append("弱化单边碳边境约束")
        return "、".join(parts) if parts else "暂未形成明确妥协路径"


def render_markdown_report(report: Dict[str, object]) -> str:
    lines = []
    lines.append(f"# {report['project']}\n")
    lines.append("## 输入政策\n")
    lines.append(f"- 标题：{report['input_policy']['title']}")
    lines.append(f"- 文本：{report['input_policy']['policy_text']}")
    lines.append("- 初始属性：")
    for key in FEATURE_ORDER:
        lines.append(f"  - {FEATURE_LABELS[key]}：{report['input_policy']['attributes'][key]}")
    lines.append("\n## 三轮推演记录\n")
    for round_item in report["round_results"]:
        lines.append(f"### 第 {round_item['round']} 轮")
        lines.append("- 本轮政策属性：")
        for key in FEATURE_ORDER:
            lines.append(f"  - {FEATURE_LABELS[key]}：{round_item['policy_attributes'][key]}")
        lines.append("- 各角色表态：")
        for agent_result in round_item["agent_results"]:
            lines.append(f"  - {agent_result['role']}（{agent_result['status_label']}，得分 {agent_result['score']}）：{agent_result['statement']}")
        lines.append(f"- 观察员总结：{round_item['observer_summary']['summary_text']}")
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
        lines.append(f"  - {item['role']}：{item['status']}（得分 {item['score']}）")
    lines.append("\n## 1.0 版本观察\n")
    lines.append("- 当前版本已经能把‘政策输入 -> 多角色表态 -> 调整条件 -> 结构化报告’这个闭环跑通。")
    lines.append("- 规则层保证了角色差异和输出稳定性，适合第一阶段课堂演示。")
    lines.append("- 后续若接入云端大模型，可显著增强发言自然度、报告细节和引用能力。")
    return "\n".join(lines) + "\n"
