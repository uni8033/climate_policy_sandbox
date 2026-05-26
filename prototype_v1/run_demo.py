from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from climate_policy_engine import ClimatePolicySandbox, render_markdown_report


BASE_DIR = Path(__file__).resolve().parent
RESULTS_DIR = BASE_DIR / "results"
LOG_DIR = BASE_DIR / "logs"


def main() -> None:
    sandbox = ClimatePolicySandbox(BASE_DIR)
    policy = sandbox.load_policy(BASE_DIR / "data" / "demo_policy.json")
    report = sandbox.run(policy, rounds=3)

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    json_path = RESULTS_DIR / "demo_run_output.json"
    md_path = RESULTS_DIR / "demo_run_report.md"
    log_path = LOG_DIR / "run_history.log"

    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    md_path.write_text(render_markdown_report(report), encoding="utf-8")

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with log_path.open("a", encoding="utf-8") as file:
        file.write(f"[{now}] 完成一次 demo 运行，输出：{json_path.name}, {md_path.name}\n")

    print("Demo run finished.")
    print(f"JSON result: {json_path}")
    print(f"Markdown report: {md_path}")
    print(f"Consensus: {report['consensus_label']}")
    print(f"Scores: {report['final_scores']}")


if __name__ == "__main__":
    main()
