# Prototype V1 / V2 Beta

## 目标

这是 `全球气候政策多利益相关方博弈沙盘` 的原型目录。

当前目录里保留了 `1.0` 最小闭环思路，同时已经把核心流程推进到 `2.0 beta`：

```text
政策输入 -> 立场陈述 -> 冲突识别 -> 联盟映射 -> 条件交换 -> 秘书处修订 -> 最终表决
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
- 已扩展到 7 类角色，并在 `agents.json` 中写入设计依据
- 采用六阶段谈判流程，而不再只是固定三轮调参
- 有自动输出的政策可行性报告、联盟映射和立场变化
- 已新增带来源与可靠性标注的现实世界样本国家数据
- 已支持 `抽象角色模式 / 真实国家样本模式` 两种推演主体
- 便于后续接入真实数据与云端大模型

## 当前版本局限

- 发言文本仍以模板生成和规则引擎为主
- 还没有接入真实 `NDC / World Bank / ND-GAIN` 数据
- 目前的“科学性”仍以轻量映射和结构化依据为主，还不是真实国家级参数标定
- 可视化已从调试面板升级，但仍属于课程演示版而非正式产品
- 第三方模型网关是否可访问，仍受当前运行环境网络和访问策略影响

## 下一步建议

- 接入真实国家样本，把角色从“类型代理”升级为“国家/集团代理”
- 增加更多图表、联盟变化和情景对比
- 为秘书处修订阶段补充更细的文本修改逻辑

## 现实世界数据接地

- 来源目录：`data/source_catalog.json`
- 样本国家数据：`data/real_world_entities.json`
- 说明文档：`real_world_data_notes.md`

当前这一层的目标是先把“数据来源、年份、可靠性、局限”显式写进项目，而不是继续使用无法追溯的角色设定。

## 真实国家样本模式

- 当前样本：`德国`、`美国`、`中国`、`巴西`、`印度`、`印度尼西亚`、`沙特阿拉伯`、`斐济`、`孟加拉国`
- 生成逻辑：
  - 国家背景指标来自 `real_world_entities.json`
  - 政策承诺摘要来自 `real_policy_profiles.json`
  - 引擎依据收入水平、燃料出口依赖、可再生能源占比、ND-GAIN 脆弱性/准备度、NDC 目标类型和条件性说明，生成各国的偏好权重
  - 引擎还会把这些字段转成谈判硬约束，例如：
    - 最低需要的 `气候资金支持`
    - 最低需要的 `适应/损失补偿支持`
    - 最多容忍的 `化石能源退出强度`
    - 最多容忍的 `碳边境约束强度`
- 使用建议：
  - 如果你想展示“谈判结构”，优先用抽象角色模式
  - 如果你想展示“真实性和可追溯性”，优先用真实国家样本模式

## 当前真实性边界

- 真实国家模式已经引入：
  - 公开国家指标
  - 公开 NDC 摘要
  - 条件性承诺约束
- 但当前仍属于“有真实来源约束的规则推演”，还不是：
  - 计量经济学模型
  - 历史谈判语料训练模型
  - 部门级 IAM/能源系统模型

## 当前环境实测

- `python3 run_demo.py`：已成功运行
- `python3 -m streamlit run streamlit_app.py`：已成功启动
- 直接使用 `streamlit run ...` 在当前环境中可能失败，因此优先使用 `python3 -m streamlit`
- 已完成真实模型模式接入，但在当前托管环境测试外部网关时收到 `403 / error code 1010`，因此这里无法直接完成远端推理验证

## 高分版研究模式

- 新增 `情景实验` 运行形态
- 可对同一条政策文本批量运行多组预设情景
- 自动输出情景对比表、研究发现、方法与局限说明
- 相关说明见：`research_mode_notes.md`

## LULUCF 与可视化增强

- 新增 `森林/LULUCF 支持` 维度
- 该维度优先影响 `巴西 / 印度 / 印度尼西亚` 等森林与碳汇议题更重要的样本
- 情景实验页新增核心指标图、约束触发频率图和情景属性矩阵
