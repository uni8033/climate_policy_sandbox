# Prototype V1

## 目标

这是 `全球气候政策多利益相关方博弈沙盘` 的 `1.0` 最小原型。

当前版本重点不是做漂亮界面，而是先把下面这个闭环跑通：

```text
政策输入 -> 角色初始化 -> 三轮博弈 -> 自动调整政策 -> 观察员总结 -> 输出结构化报告
```

## 文件结构

- `climate_policy_engine.py`：核心规则引擎
- `llm_adapter.py`：可选的云端大模型接入层，默认使用本地模板模式
- `run_demo.py`：运行样例政策并输出结果
- `streamlit_app.py`：可选的 Web 原型页面
- `data/agents.json`：角色配置
- `data/demo_policy.json`：样例政策输入
- `results/`：样例运行结果
- `logs/`：开发日志
- `prompt_design.md`：当前 Prompt 与 AI 使用思路说明

## 如何运行

### 1. 运行命令行样例

```bash
cd /data/hanzhang/homework/AI4GC/prototype_v1
python3 run_demo.py
```

运行后会生成：

- `results/demo_run_output.json`
- `results/demo_run_report.md`

### 2. 运行 Streamlit 页面

如果本地装有 `streamlit`，推荐使用下面这条更稳妥的命令：

```bash
cd /data/hanzhang/homework/AI4GC/prototype_v1
python3 -m streamlit run streamlit_app.py
```

### 3. 使用真实大模型模式

当前原型已经支持 `OpenAI-compatible` 接口调用。

你可以：

- 在 `Streamlit` 页面里切换到 `真实模型模式`
- 或直接通过环境变量运行 `run_llm_demo.py`

命令行示例：

```bash
cd /data/hanzhang/homework/AI4GC/prototype_v1
export OPENAI_API_KEY="你的key"
export OPENAI_BASE_URL="https://opencode.ai/zen/v1"
export OPENAI_API_PATH="chat/completions"
export OPENAI_MODEL="qwen3.6-plus"
python3 run_llm_demo.py
```

更详细的接入说明见：

- `llm_integration_notes.md`

## 当前版本特点

- 不依赖在线 API 也能运行
- 有明确角色、政策属性和状态更新逻辑
- 有自动输出的政策可行性报告
- 便于后续接入真实数据与云端大模型

## 当前版本局限

- 发言文本仍以模板生成和规则引擎为主
- 还没有接入真实 `NDC / World Bank / ND-GAIN` 数据
- 还没有做完整前端可视化和引用标注
- 第三方模型网关是否可访问，仍受当前运行环境网络和访问策略影响

## 下一步建议

- 接入云端模型 API，提升角色发言自然度
- 增加真实国家数据映射
- 增加图表、联盟变化和情景对比

## 当前环境实测

- `python3 run_demo.py`：已成功运行
- `python3 -m streamlit run streamlit_app.py`：已成功启动
- 直接使用 `streamlit run ...` 在当前环境中可能失败，因此优先使用 `python3 -m streamlit`
- 已完成真实模型模式接入，但在当前托管环境测试外部网关时收到 `403 / error code 1010`，因此这里无法直接完成远端推理验证
