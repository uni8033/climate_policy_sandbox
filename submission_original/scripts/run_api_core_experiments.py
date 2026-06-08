from __future__ import annotations

import json
from pathlib import Path

from climate_policy_engine import ClimatePolicySandbox, render_markdown_report

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
SCENARIO_IDS = {'baseline_auto', 'high_ambition_with_support', 'finance_justice', 'forest_governance'}


def save_json(name: str, data: dict) -> None:
    (OUT / f'{name}.json').write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')


def save_md(name: str, report: dict) -> None:
    (OUT / f'{name}.md').write_text(render_markdown_report(report), encoding='utf-8')


def run_single(name: str, agent_mode: str, policy: dict) -> dict:
    sandbox = ClimatePolicySandbox(BASE_DIR, agent_mode=agent_mode)
    report = sandbox.run(policy)
    payload = {'run_name': name, 'agent_mode': agent_mode, 'narrator': sandbox.narrator.describe(), 'report': report}
    save_json(name, payload)
    save_md(name, report)
    return payload


def run_batch(name: str, agent_mode: str, policy_text: str) -> dict:
    sandbox = ClimatePolicySandbox(BASE_DIR, agent_mode=agent_mode)
    scenarios = [item for item in sandbox.get_default_scenarios() if item['id'] in SCENARIO_IDS]
    result = sandbox.run_scenario_batch(policy_text, scenarios=scenarios)
    payload = {'run_name': name, 'agent_mode': agent_mode, 'narrator': sandbox.narrator.describe(), 'result': result}
    save_json(name, payload)
    return payload


def extract_constraint_counts(batch_payload: dict) -> dict[str, int]:
    counts: dict[str, int] = {}
    for scenario in batch_payload['result']['scenario_reports']:
        for hit in scenario['constraint_hits']:
            counts[hit['feature']] = counts.get(hit['feature'], 0) + 1
    return counts


def main() -> None:
    demo_policy = ClimatePolicySandbox(BASE_DIR).load_policy(BASE_DIR / 'data' / 'demo_policy.json')
    abstract_stress = run_single('api_abstract_stress_single', 'abstract', demo_policy)
    abstract_balanced = run_single('api_abstract_balanced_single', 'abstract', BALANCED_POLICY)
    real_balanced = run_single('api_real_balanced_single', 'real_countries', BALANCED_POLICY)
    real_forest = run_single('api_real_forest_single', 'real_countries', FOREST_POLICY)
    abstract_batch = run_batch('api_abstract_scenario_batch', 'abstract', BALANCED_POLICY['policy_text'])
    real_batch = run_batch('api_real_scenario_batch', 'real_countries', BALANCED_POLICY['policy_text'])
    summary = {
        'narrators': {
            'abstract_stress': abstract_stress['narrator'],
            'abstract_balanced': abstract_balanced['narrator'],
            'real_balanced': real_balanced['narrator'],
            'real_forest': real_forest['narrator'],
            'abstract_batch': abstract_batch['narrator'],
            'real_batch': real_batch['narrator'],
        },
        'single_scores': {
            'abstract_stress': abstract_stress['report']['final_scores'],
            'abstract_balanced': abstract_balanced['report']['final_scores'],
            'real_balanced': real_balanced['report']['final_scores'],
            'real_forest': real_forest['report']['final_scores'],
        },
        'single_consensus': {
            'abstract_stress': abstract_stress['report']['consensus_label'],
            'abstract_balanced': abstract_balanced['report']['consensus_label'],
            'real_balanced': real_balanced['report']['consensus_label'],
            'real_forest': real_forest['report']['consensus_label'],
        },
        'abstract_batch_table': abstract_batch['result']['comparison_table'],
        'real_batch_table': real_batch['result']['comparison_table'],
        'abstract_batch_findings': abstract_batch['result']['research_findings'],
        'real_batch_findings': real_batch['result']['research_findings'],
        'real_batch_constraint_counts': extract_constraint_counts(real_batch),
        'llm_statement_samples': [
            {
                'role': item['role'],
                'status': item['status_label'],
                'statement': item['statement'],
            }
            for item in real_balanced['report']['stage_results'][-1]['agent_results'][:4]
        ],
    }
    save_json('api_core_experiment_summary', summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
