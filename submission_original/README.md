# 原版项目提交材料

## 目录说明
- `report.tex`：正式 LaTeX 技术报告
- `figures/`：报告与汇报中用到的图表素材
- `slides/original_project_presentation.tex`：正式课堂汇报 Beamer 幻灯稿
- `slides/original_project_presentation.html`：可直接打开使用的 HTML 幻灯版
- `slides/speaker_notes.md`：逐页讲稿
- `scripts/generate_submission_figures.py`：图表生成脚本

## 建议使用方式
### 技术报告
- 若本机装有 XeLaTeX，可在本目录运行：
  - `xelatex report.tex`
  - 如需两遍交叉引用，可运行两次

### 课堂汇报
- 最稳妥的现场演示方式：直接用浏览器打开 `slides/original_project_presentation.html`
- 如果你更习惯 PDF/LaTeX 幻灯，可在 `slides/` 目录使用 XeLaTeX 编译：
  - `xelatex original_project_presentation.tex`

## 说明
- 当前运行环境中未检测到 `xelatex/pdflatex`，因此这里提供的是源文件和可直接打开的 HTML 幻灯版。
- 图表引用的数据来自：
  - `prototype_v1/results/demo_run_output.json`
  - `prototype_v1/results/demo_history/20260607_164129_single.json`
  - `prototype_v1/results/demo_history/20260602_030652_single.json`
