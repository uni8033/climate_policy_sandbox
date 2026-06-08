from __future__ import annotations

import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import FancyBboxPatch

BASE = Path('/data/hanzhang/homework/AI4GC')
FIG = BASE / 'submission_original' / 'figures'
FIG.mkdir(parents=True, exist_ok=True)
EXP = BASE / 'submission_original' / 'experiments_api'

plt.rcParams['font.sans-serif'] = ['Noto Sans CJK JP', 'Noto Sans CJK SC', 'SimHei', 'Microsoft YaHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False


def load(path: Path):
    return json.loads(path.read_text(encoding='utf-8'))


def savefig(fig, name: str):
    fig.tight_layout()
    fig.savefig(FIG / name, dpi=240, bbox_inches='tight', facecolor='white')
    plt.close(fig)


def plot_pipeline():
    labels = ['政策输入', '结构化属性提取', '立场陈述', '冲突识别', '联盟映射', '秘书处修订', '最终表决']
    fig, ax = plt.subplots(figsize=(13.3, 2.9))
    ax.set_xlim(0, len(labels) * 1.82)
    ax.set_ylim(0, 2)
    ax.axis('off')
    for i, label in enumerate(labels):
        x = i * 1.82 + 0.2
        box = FancyBboxPatch((x, 0.62), 1.4, 0.68, boxstyle='round,pad=0.03,rounding_size=0.12',
                             linewidth=1.3, edgecolor='#1a5d54', facecolor='#eaf4f1')
        ax.add_patch(box)
        ax.text(x + 0.7, 0.96, label, ha='center', va='center', fontsize=10.8, color='#153237', fontweight='bold')
        if i < len(labels) - 1:
            ax.annotate('', xy=(x + 1.72, 0.96), xytext=(x + 1.44, 0.96),
                        arrowprops=dict(arrowstyle='->', lw=1.7, color='#c08b2f'))
    savefig(fig, 'api_pipeline_overview.png')


def plot_single_metrics():
    summary = load(EXP / 'api_core_experiment_summary.json')
    labels = ['可行性', '公平性', '阻力强度']
    series = {
        '抽象-高冲突': summary['single_scores']['abstract_stress'],
        '抽象-平衡型': summary['single_scores']['abstract_balanced'],
        '真实国家-平衡型': summary['single_scores']['real_balanced'],
        '真实国家-森林公平型': summary['single_scores']['real_forest'],
    }
    data = [[vals['feasibility'], vals['fairness'], vals['resistance']] for vals in series.values()]
    x = np.arange(len(labels))
    width = 0.18
    fig, ax = plt.subplots(figsize=(11.4, 5.4))
    colors = ['#b45863', '#2f7f6d', '#508f8f', '#c58d2a']
    for idx, (name, values) in enumerate(zip(series.keys(), data)):
        ax.bar(x + (idx - 1.5) * width, values, width, label=name, color=colors[idx])
        for j, v in enumerate(values):
            ax.text(x[j] + (idx - 1.5) * width, v + 1, f'{v:.1f}', ha='center', va='bottom', fontsize=8.5)
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.set_ylim(0, 100)
    ax.set_ylabel('分值')
    ax.legend(frameon=False, ncol=2, loc='upper center', bbox_to_anchor=(0.5, 1.07))
    ax.grid(axis='y', alpha=0.18)
    savefig(fig, 'api_single_metrics_comparison.png')


def _scenario_chart(table, out_name):
    scenarios = [row['情景'] for row in table]
    feasibility = [row['可行性'] for row in table]
    fairness = [row['公平性'] for row in table]
    resistance = [row['阻力强度'] for row in table]
    x = np.arange(len(scenarios))
    width = 0.24
    fig, ax = plt.subplots(figsize=(11.5, 5.2))
    ax.bar(x - width, feasibility, width, label='可行性', color='#2f7f6d')
    ax.bar(x, fairness, width, label='公平性', color='#c58d2a')
    ax.bar(x + width, resistance, width, label='阻力强度', color='#b45863')
    for arr, offset in [(feasibility, -width), (fairness, 0), (resistance, width)]:
        for i, v in enumerate(arr):
            ax.text(x[i] + offset, v + 0.8, f'{v:.1f}', ha='center', fontsize=8)
    ax.set_xticks(x)
    ax.set_xticklabels(scenarios)
    ax.set_ylim(0, 100)
    ax.legend(frameon=False, ncol=3, loc='upper center', bbox_to_anchor=(0.5, 1.07))
    ax.grid(axis='y', alpha=0.18)
    savefig(fig, out_name)


def plot_scenario_batches():
    summary = load(EXP / 'api_core_experiment_summary.json')
    _scenario_chart(summary['abstract_batch_table'], 'api_abstract_batch_compare.png')
    _scenario_chart(summary['real_batch_table'], 'api_real_batch_compare.png')


def plot_real_constraints():
    summary = load(EXP / 'api_core_experiment_summary.json')
    items = list(summary['real_batch_constraint_counts'].items())
    labels = [item[0] for item in items]
    values = [item[1] for item in items]
    fig, ax = plt.subplots(figsize=(10.8, 4.8))
    ax.bar(labels, values, color='#4c8b79')
    for i, v in enumerate(values):
        ax.text(i, v + 0.15, str(v), ha='center', fontsize=9)
    ax.set_ylabel('触发次数')
    ax.tick_params(axis='x', rotation=22)
    ax.grid(axis='y', alpha=0.18)
    savefig(fig, 'api_real_constraint_counts.png')


def plot_real_positions_compare():
    balanced = load(EXP / 'api_real_balanced_single.json')['report']['final_positions']
    forest = load(EXP / 'api_real_forest_single.json')['report']['final_positions']
    labels = [item['role'] for item in balanced]
    bvals = [item['score'] for item in balanced]
    fvals = [item['score'] for item in forest]
    x = np.arange(len(labels))
    width = 0.36
    fig, ax = plt.subplots(figsize=(12, 5.5))
    ax.bar(x - width / 2, bvals, width, label='平衡型综合政策', color='#4a8f88')
    ax.bar(x + width / 2, fvals, width, label='森林治理与公平融资政策', color='#c58d2a')
    ax.axhline(0, color='#222', lw=1)
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=22)
    ax.set_ylabel('最终得分')
    ax.legend(frameon=False)
    ax.grid(axis='y', alpha=0.18)
    savefig(fig, 'api_real_position_compare.png')


def plot_role_weight_heatmap():
    agents = load(BASE / 'prototype_v1' / 'data' / 'agents.json')
    features = ['fossil_phaseout','carbon_tariff','climate_finance','tech_transfer','transition_flexibility','ccs_support','adaptation_fund','lulucf_support']
    feature_labels = ['化石退出','碳边境','气候融资','技术转移','过渡灵活性','CCS','适应补偿','LULUCF']
    data = np.array([[item['weights'].get(f, 0) for f in features] for item in agents])
    roles = [item['name'] for item in agents]
    fig, ax = plt.subplots(figsize=(11.6, 5.8))
    im = ax.imshow(data, cmap='RdYlGn', aspect='auto', vmin=-2.2, vmax=2.2)
    ax.set_xticks(np.arange(len(feature_labels)))
    ax.set_xticklabels(feature_labels, rotation=20)
    ax.set_yticks(np.arange(len(roles)))
    ax.set_yticklabels(roles)
    for i in range(data.shape[0]):
        for j in range(data.shape[1]):
            ax.text(j, i, f'{data[i,j]:.1f}', ha='center', va='center', fontsize=8, color='#1d1d1d')
    fig.colorbar(im, ax=ax, fraction=0.025, pad=0.02)
    savefig(fig, 'api_role_weight_heatmap.png')


def plot_constraint_penalty():
    report = load(EXP / 'api_real_balanced_single.json')['report']['stage_results'][-1]['agent_results']
    labels = [item['role'] for item in report]
    raw = [item['raw_score'] for item in report]
    adjusted = [item['score'] for item in report]
    x = np.arange(len(labels))
    width = 0.36
    fig, ax = plt.subplots(figsize=(12, 5.4))
    ax.bar(x - width / 2, raw, width, label='约束调整前', color='#8aa6a3')
    ax.bar(x + width / 2, adjusted, width, label='约束调整后', color='#2f7f6d')
    ax.axhline(0, color='#222', lw=1)
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=22)
    ax.set_ylabel('得分')
    ax.legend(frameon=False, ncol=2, loc='upper center', bbox_to_anchor=(0.5, 1.06))
    ax.grid(axis='y', alpha=0.18)
    savefig(fig, 'api_real_constraint_penalty.png')


def plot_method_ablation():
    path = EXP / 'api_method_ablation_summary.json'
    if not path.exists():
        return
    summary = load(path)
    rows = summary['summary_table']
    labels = [row['实验'] for row in rows]
    feasibility = [row['可行性'] for row in rows]
    fairness = [row['公平性'] for row in rows]
    resistance = [row['阻力强度'] for row in rows]
    x = np.arange(len(labels))
    width = 0.24
    fig, ax = plt.subplots(figsize=(12.8, 5.6))
    ax.bar(x - width, feasibility, width, label='可行性', color='#2f7f6d')
    ax.bar(x, fairness, width, label='公平性', color='#c58d2a')
    ax.bar(x + width, resistance, width, label='阻力强度', color='#b45863')
    for arr, offset in [(feasibility, -width), (fairness, 0), (resistance, width)]:
        for i, v in enumerate(arr):
            ax.text(x[i] + offset, v + 0.8, f'{v:.1f}', ha='center', fontsize=7.8)
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=18)
    ax.set_ylim(0, 100)
    ax.legend(frameon=False, ncol=3, loc='upper center', bbox_to_anchor=(0.5, 1.08))
    ax.grid(axis='y', alpha=0.18)
    savefig(fig, 'api_method_ablation_compare.png')


if __name__ == '__main__':
    plot_pipeline()
    plot_single_metrics()
    plot_scenario_batches()
    plot_real_constraints()
    plot_real_positions_compare()
    plot_role_weight_heatmap()
    plot_constraint_penalty()
    plot_method_ablation()
    print(sorted(p.name for p in FIG.glob('api_*.png')))
