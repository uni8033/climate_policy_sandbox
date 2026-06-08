from __future__ import annotations

import json
from pathlib import Path

from climate_policy_engine import ClimatePolicySandbox, render_markdown_report

ROOT = Path('/data/hanzhang/homework/AI4GC')
BASE_DIR = ROOT / 'prototype_v1'
OUT = ROOT / 'submission_original' / 'experiments'
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

FOREST_POLICY = {
    'title': '森林治理与公平融资样例',
    'policy_text': (
        '推动森林保护、碳汇和土地利用治理，并设立适应融资、损失损害支持和技术转移机制，'
        '同时对发展中经济体保留更长过渡期。'
    ),
    'attributes': {
        'fossil_phaseout': 1,
        'carbon_tariff': 0,
        'climate_finance': 3,
        'tech_transfer': 2,
        'transition_flexibility': 2,
        'ccs_support': 0,
        'adaptation_fund': 3,
        'lulucf_support': 3,
    },
}


def save_json(name: str, data: dict) -> None:
    (OUT / f'{name}.json').write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')


def save_md(name: str, report: dict) -> None:
    (OUT / f'{name}.md').write_text(render_markdown_report(report), encoding='utf-8')


def run_single(name: str, agent_mode: str, policy: dict) -> dict:
    sandbox = ClimatePolicySandbox(BASE_DIR, agent_mode=agent_mode)
    report = sandbox.run(policy)
    payload = {
        'run_name': name,
        'agent_mode': agent_mode,
        'narrator': sandbox.narrator.describe(),
        'report': report,
    }
    save_json(name, payload)
    save_md(name, report)
    return payload


def run_batch(name: str, agent_mode: str, policy_text: str) -> dict:
    sandbox = ClimatePolicySandbox(BASE_DIR, agent_mode=agent_mode)
    result = sandbox.run_scenario_batch(policy_text)
    payload = {
        'run_name': name,
        'agent_mode': agent_mode,
        'narrator': sandbox.narrator.describe(),
        'result': result,
    }
    save_json(name, payload)
    return payload


def extract_constraint_counts(batch_result: dict) -> dict[str, int]:
    counts: dict[str, int] = {}
    for scenario in batch_result['result']['scenario_reports']:
        for hit in scenario['constraint_hits']:
            counts[hit['feature']] = counts.get(hit['feature'], 0) + 1
    return counts


def main() -> None:
    demo_policy = ClimatePolicySandbox(BASE_DIR).load_policy(BASE_DIR / 'data' / 'demo_policy.json')

    abstract_stress = run_single('abstract_stress_single_fresh', 'abstract', demo_policy)
    abstract_balanced = run_single('abstract_balanced_single_fresh', 'abstract', BALANCED_POLICY)
    real_balanced = run_single('real_balanced_single_fresh', 'real_countries', BALANCED_POLICY)
    real_forest = run_single('real_forest_single_fresh', 'real_countries', FOREST_POLICY)

    abstract_batch = run_batch('abstract_scenario_batch_fresh', 'abstract', BALANCED_POLICY['policy_text'])
    real_batch = run_batch('real_scenario_batch_fresh', 'real_countries', BALANCED_POLICY['policy_text'])

    summary = {
        'abstract_stress_scores': abstract_stress['report']['final_scores'],
        'abstract_balanced_scores': abstract_balanced['report']['final_scores'],
        'real_balanced_scores': real_balanced['report']['final_scores'],
        'real_forest_scores': real_forest['report']['final_scores'],
        'abstract_batch_findings': abstract_batch['result']['research_findings'],
        'real_batch_findings': real_batch['result']['research_findings'],
        'real_batch_constraint_counts': extract_constraint_counts(real_batch),
        'real_final_positions_balanced': real_balanced['report']['final_positions'],
        'real_final_positions_forest': real_forest['report']['final_positions'],
    }
    save_json('fresh_experiment_summary', summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
