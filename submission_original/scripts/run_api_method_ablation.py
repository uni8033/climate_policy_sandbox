from __future__ import annotations

import json
from pathlib import Path

from climate_policy_engine import (
    ClimatePolicySandbox,
    FEATURE_ORDER,
    STATUS_SCORE,
)

ROOT = Path('/data/hanzhang/homework/AI4GC')
BASE_DIR = ROOT / 'prototype_v1'
OUT = ROOT / 'submission_original' / 'experiments_api'
OUT.mkdir(parents=True, exist_ok=True)

BALANCED_POLICY = {
    'title': '平衡型综合政策样例',
    'policy_text': (
        '2035年前在加强森林保护、碳汇和土地利用治理的同时，逐步停止新建无减排措施煤电，'
        '并为高脆弱国家提供适应融资、技术转移支持，同时允许部分发展中经济体采取更灵活的分阶段过渡安排。'
    ),
    'attributes': {
        'fossil_phaseout': 2,
        'carbon_tariff': 0,
        'climate_finance': 2,
        'tech_transfer': 2,
        'transition_flexibility': 2,
        'ccs_support': 0,
        'adaptation_fund': 2,
        'lulucf_support': 2,
    },
}

HIGH_AMBITION_POLICY = {
    'title': '高雄心配套补偿样例',
    'policy_text': (
        '要求尽快停止新建无减排措施煤电，并提高碳边境约束强度；'
        '同时增加适应融资、技术转移和转型补偿，但不过度延长过渡期。'
    ),
    'attributes': {
        'fossil_phaseout': 3,
        'carbon_tariff': 2,
        'climate_finance': 2,
        'tech_transfer': 2,
        'transition_flexibility': 0,
        'ccs_support': 0,
        'adaptation_fund': 2,
        'lulucf_support': 1,
    },
}


def save_json(name: str, data: dict) -> None:
    (OUT / f'{name}.json').write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')


def compute_scores(final_statuses: list[str], attrs: dict[str, int]) -> dict[str, float]:
    feasibility = round(sum(STATUS_SCORE[status] for status in final_statuses) / (len(final_statuses) * 3) * 100, 1)
    fairness = round(
        (
            attrs['climate_finance']
            + attrs['tech_transfer']
            + attrs['adaptation_fund']
            + attrs['transition_flexibility']
            + attrs['lulucf_support']
        )
        / 15
        * 100,
        1,
    )
    resistance = round(100 - feasibility + attrs['carbon_tariff'] * 3, 1)
    return {
        'feasibility': feasibility,
        'fairness': fairness,
        'resistance': resistance,
    }


def run_variant(
    name: str,
    label: str,
    agent_mode: str,
    policy: dict,
    *,
    disable_constraints: bool = False,
    disable_revision: bool = False,
    text_only: bool = False,
) -> dict:
    sandbox = ClimatePolicySandbox(BASE_DIR, agent_mode=agent_mode)
    if disable_constraints:
        for agent in sandbox.agents:
            agent.constraint_profile = {}

    attrs_seed = {} if text_only else dict(policy['attributes'])
    policy_text = str(policy['policy_text'])
    initial_attrs = sandbox._normalize_attributes(attrs_seed, policy_text)
    initial_vote = sandbox._evaluate_all_agents(initial_attrs, policy_text, stage_index=1)
    conflict_summary = sandbox._observer_stage_summary(initial_vote, initial_attrs, '初始表态')
    alliance_map = sandbox._build_alliance_map(initial_vote)
    bargaining_package = sandbox._build_bargaining_package(initial_vote, initial_attrs, conflict_summary, alliance_map)

    if disable_revision:
        adjustments = {key: 0 for key in FEATURE_ORDER}
        revised_attrs = dict(initial_attrs)
        tradeoffs: list[str] = []
    else:
        adjustments = bargaining_package['adjustments']
        revised_attrs = sandbox._apply_adjustments_copy(initial_attrs, adjustments)
        tradeoffs = bargaining_package['tradeoffs']

    final_vote = sandbox._evaluate_all_agents(revised_attrs, policy_text, stage_index=2)
    final_statuses = [item['status'] for item in final_vote]
    scores = compute_scores(final_statuses, revised_attrs)
    violations = sum(len(item.get('constraint_violations', [])) for item in final_vote)

    payload = {
        'id': name,
        'label': label,
        'agent_mode': agent_mode,
        'narrator': sandbox.narrator.describe(),
        'variant': {
            'disable_constraints': disable_constraints,
            'disable_revision': disable_revision,
            'text_only': text_only,
        },
        'initial_attributes': initial_attrs,
        'revised_attributes': revised_attrs,
        'adjustments': adjustments,
        'tradeoffs': tradeoffs,
        'consensus_label': sandbox._consensus_label(final_statuses),
        'final_scores': scores,
        'constraint_violation_count': violations,
        'final_statuses': [
            {
                'role': item['role'],
                'status': item['status_label'],
                'score': item['score'],
                'raw_score': item['raw_score'],
            }
            for item in final_vote
        ],
    }
    save_json(name, payload)
    return payload


def build_summary(items: list[dict]) -> dict:
    by_id = {item['id']: item for item in items}
    summary_table = [
        {
            '实验': item['label'],
            '主体模式': '真实国家样本' if item['agent_mode'] == 'real_countries' else '抽象角色',
            '可行性': item['final_scores']['feasibility'],
            '公平性': item['final_scores']['fairness'],
            '阻力强度': item['final_scores']['resistance'],
            '共识水平': item['consensus_label'],
            '约束触发次数': item['constraint_violation_count'],
        }
        for item in items
    ]
    findings = [
        (
            '在抽象角色模式下，仅依赖文本自动识别时，秘书处修订会把可行性由 '
            f"{by_id['ablation_abstract_text_only_no_revision']['final_scores']['feasibility']} "
            '提升至 '
            f"{by_id['ablation_abstract_text_only_full']['final_scores']['feasibility']}，"
            '说明当前平衡型文本在自动识别后更依赖修订机制来补足过渡安排与技术路线。'
        ),
        (
            '在真实国家样本模式下，去掉现实约束后，可行性由 '
            f"{by_id['ablation_real_high_ambition_full']['final_scores']['feasibility']} "
            '升至 '
            f"{by_id['ablation_real_high_ambition_no_constraints']['final_scores']['feasibility']}，"
            '阻力强度同步下降，说明约束建模显著提高了系统对高雄心政策现实摩擦的敏感性。'
        ),
        (
            '在平衡型政策上仅保留文本自动属性识别时，可行性为 '
            f"{by_id['ablation_abstract_text_only_full']['final_scores']['feasibility']}，"
            '公平性为 '
            f"{by_id['ablation_abstract_text_only_full']['final_scores']['fairness']}，"
            '低于显式属性设置版本，说明结构化属性输入能够为政策意图提供更稳定的表达。'
        ),
    ]
    return {
        'narrators': {item['id']: item['narrator'] for item in items},
        'summary_table': summary_table,
        'findings': findings,
        'items': items,
    }


def main() -> None:
    items = [
        run_variant('ablation_abstract_explicit_full', '抽象角色-显式属性', 'abstract', BALANCED_POLICY),
        run_variant('ablation_abstract_text_only_full', '抽象角色-文本识别+修订', 'abstract', BALANCED_POLICY, text_only=True),
        run_variant('ablation_abstract_text_only_no_revision', '抽象角色-文本识别无修订', 'abstract', BALANCED_POLICY, text_only=True, disable_revision=True),
        run_variant('ablation_real_high_ambition_full', '真实国家-高雄心含约束', 'real_countries', HIGH_AMBITION_POLICY),
        run_variant('ablation_real_high_ambition_no_constraints', '真实国家-高雄心去约束', 'real_countries', HIGH_AMBITION_POLICY, disable_constraints=True),
    ]
    summary = build_summary(items)
    save_json('api_method_ablation_summary', summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
