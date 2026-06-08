from __future__ import annotations

import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
import numpy as np

BASE = Path('/data/hanzhang/homework/AI4GC')
OUT = BASE / 'submission_original' / 'figures'
OUT.mkdir(parents=True, exist_ok=True)

plt.rcParams['font.sans-serif'] = ['Noto Sans CJK JP', 'Noto Sans CJK SC', 'SimHei', 'Microsoft YaHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False


def load_json(path: Path):
    return json.loads(path.read_text(encoding='utf-8'))


def savefig(fig, name: str):
    fig.savefig(OUT / name, dpi=220, bbox_inches='tight', facecolor='white')
    plt.close(fig)


def plot_pipeline():
    labels = ['政策输入', '立场陈述', '冲突识别', '联盟与分裂', '条件交换', '秘书处修订', '最终表决']
    fig, ax = plt.subplots(figsize=(12.8, 2.8))
    ax.set_xlim(0, len(labels) * 1.8)
    ax.set_ylim(0, 2)
    ax.axis('off')
    for i, label in enumerate(labels):
        x = i * 1.8 + 0.2
        y = 0.6
        box = FancyBboxPatch((x, y), 1.35, 0.7, boxstyle='round,pad=0.02,rounding_size=0.12',
                             linewidth=1.4, edgecolor='#1d5b56', facecolor='#eaf4f1')
        ax.add_patch(box)
        ax.text(x + 0.675, y + 0.35, label, ha='center', va='center', fontsize=11, color='#153237', fontweight='bold')
        if i < len(labels) - 1:
            ax.annotate('', xy=(x + 1.62, y + 0.35), xytext=(x + 1.38, y + 0.35),
                        arrowprops=dict(arrowstyle='->', lw=1.8, color='#c08b2f'))
    ax.text(0.2, 1.6, '原版系统六阶段推演流程（Prototype 2.0 beta）', fontsize=14, fontweight='bold', color='#132a33')
    savefig(fig, 'pipeline_overview.png')


def plot_metrics_compare():
    abstract = load_json(BASE / 'prototype_v1' / 'results' / 'demo_history' / '20260607_164129_single.json')
    real = load_json(BASE / 'prototype_v1' / 'results' / 'demo_history' / '20260602_030652_single.json')
    demo = load_json(BASE / 'prototype_v1' / 'results' / 'demo_run_output.json')
    labels = ['可行性', '公平性', '阻力强度']
    series = {
        '2.0 demo 样例': [demo['final_scores']['feasibility'], demo['final_scores']['fairness'], demo['final_scores']['resistance']],
        '抽象角色模式': [abstract['final_scores']['feasibility'], abstract['final_scores']['fairness'], abstract['final_scores']['resistance']],
        '真实国家样本模式': [real['final_scores']['feasibility'], real['final_scores']['fairness'], real['final_scores']['resistance']],
    }
    x = np.arange(len(labels))
    width = 0.24
    fig, ax = plt.subplots(figsize=(10.8, 5.2))
    colors = ['#2f7f6d', '#4d9e86', '#c58d2a']
    for idx, (name, values) in enumerate(series.items()):
        ax.bar(x + (idx - 1) * width, values, width, label=name, color=colors[idx])
        for j, v in enumerate(values):
            ax.text(x[j] + (idx - 1) * width, v + 1.2, f'{v:.1f}', ha='center', va='bottom', fontsize=9)
    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=11)
    ax.set_ylim(0, 100)
    ax.set_ylabel('分值 / 指标')
    ax.set_title('原版系统不同运行样本的核心指标对比', fontsize=14, fontweight='bold')
    ax.legend(frameon=False, ncol=3, loc='upper center', bbox_to_anchor=(0.5, 1.12))
    ax.grid(axis='y', alpha=0.2)
    savefig(fig, 'metrics_comparison.png')


def plot_agent_scores():
    demo = load_json(BASE / 'prototype_v1' / 'results' / 'demo_run_output.json')
    scores = []
    labels = []
    colors = []
    color_map = {
        '支持': '#1f7a6e',
        '有保留地支持': '#6aa68e',
        '有保留地反对': '#d59b37',
        '强烈反对': '#b64d5a',
    }
    for item in demo['stage_results'][-1]['agent_results']:
        labels.append(item['role'])
        scores.append(item['score'])
        colors.append(color_map.get(item['status_label'], '#60707b'))
    order = np.argsort(scores)
    labels = [labels[i] for i in order]
    scores = [scores[i] for i in order]
    colors = [colors[i] for i in order]
    fig, ax = plt.subplots(figsize=(10.6, 5.6))
    ax.barh(labels, scores, color=colors)
    ax.axvline(0, color='#222222', lw=1)
    for y, v in enumerate(scores):
        ax.text(v + (0.18 if v >= 0 else -0.18), y, f'{v:.1f}', va='center', ha='left' if v >= 0 else 'right', fontsize=9)
    ax.set_title('原版系统样例政策下的最终角色得分', fontsize=14, fontweight='bold')
    ax.set_xlabel('得分（越高表示越支持）')
    ax.grid(axis='x', alpha=0.2)
    savefig(fig, 'agent_scores_demo.png')


def plot_policy_adjustments():
    demo = load_json(BASE / 'prototype_v1' / 'results' / 'demo_run_output.json')
    before = demo['input_policy']['attributes']
    after = demo['stage_results'][-1]['policy_attributes']
    name_map = {
        'fossil_phaseout': '化石退出',
        'carbon_tariff': '碳边境约束',
        'climate_finance': '气候融资',
        'tech_transfer': '技术转移',
        'transition_flexibility': '过渡灵活性',
        'ccs_support': 'CCS 支持',
        'adaptation_fund': '适应补偿',
    }
    keys = list(before.keys())
    labels = [name_map[k] for k in keys]
    before_vals = [before[k] for k in keys]
    after_vals = [after[k] for k in keys]
    x = np.arange(len(keys))
    fig, ax = plt.subplots(figsize=(11.2, 4.8))
    ax.plot(x, before_vals, marker='o', lw=2.5, color='#b64d5a', label='初始政策')
    ax.plot(x, after_vals, marker='o', lw=2.5, color='#1f7a6e', label='修订后政策')
    for i, (b, a) in enumerate(zip(before_vals, after_vals)):
        ax.text(i, max(b, a) + 0.1, f'{b}->{a}', ha='center', fontsize=9, color='#37424a')
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=20)
    ax.set_ylim(-0.1, 3.4)
    ax.set_ylabel('维度强度')
    ax.set_title('秘书处修订前后政策属性变化', fontsize=14, fontweight='bold')
    ax.legend(frameon=False)
    ax.grid(axis='y', alpha=0.2)
    savefig(fig, 'policy_adjustments.png')


def plot_real_country_snapshot():
    real = load_json(BASE / 'prototype_v1' / 'results' / 'demo_history' / '20260602_030652_single.json')
    final_agents = real['stage_results'][-1]['agent_results']
    labels = [item['role'] for item in final_agents]
    scores = [item['score'] for item in final_agents]
    fig, ax = plt.subplots(figsize=(11, 5.4))
    colors = ['#1f7a6e' if s >= 2 else '#c58d2a' if s >= 0 else '#b64d5a' for s in scores]
    ax.bar(labels, scores, color=colors)
    for i, score in enumerate(scores):
        ax.text(i, score + 0.12, f'{score:.1f}', ha='center', fontsize=9)
    ax.axhline(0, color='#222222', lw=1)
    ax.set_title('真实国家样本模式下的最终国家立场得分', fontsize=14, fontweight='bold')
    ax.set_ylabel('得分')
    ax.tick_params(axis='x', rotation=25)
    ax.grid(axis='y', alpha=0.2)
    savefig(fig, 'real_country_scores.png')


if __name__ == '__main__':
    plot_pipeline()
    plot_metrics_compare()
    plot_agent_scores()
    plot_policy_adjustments()
    plot_real_country_snapshot()
    print('Figures generated:', sorted(p.name for p in OUT.glob('*.png')))
