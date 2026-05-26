# [OPEN] Debug Session: streamlit-real-model-401

## 1. 问题摘要

- 目标：在网页端的“真实模型模式”下直接运行 `OpenCode Go + deepseek-v4-pro`
- 当前现象：报错 `LLM request failed: HTTP 401`，返回体提示 `Incorrect API key provided`，并指向 `platform.openai.com`
- 期望结果：网页端应使用 `OpenCode Go` 端点，而不是默认 `OpenAI` 端点

## 2. 当前状态

- 状态：`OPEN`
- 调试阶段：`假设与证据收集`
- 当前约束：在获得更多运行时证据前，不修改业务逻辑

## 3. 初始假设

1. 页面里的 `Base URL` 仍然是 `https://api.openai.com/v1`，导致把 `OpenCode` key 发给了 OpenAI。
2. `Streamlit` 小部件没有正确显示或保留服务器环境变量中的默认值。
3. 点击“运行推演”后，环境变量被清空，但表单值未正确写回，导致 `llm_adapter` 回退到默认 OpenAI 配置。
4. `API key` 被浏览器填写了，但 `Base URL` 或 `Model` 没同步，形成“key 正确、服务商错误”的 401。

## 4. 下一步计划

1. 阅读 `llm_adapter.py`，确认默认回退逻辑
2. 在不改业务逻辑的前提下读取当前页面配置来源
3. 做一次最小复现，分别验证“只填 key”和“完整填入 Go 配置”时的行为
4. 基于证据决定是否需要最小修复

## 5. 运行时证据

### 证据 A：适配层默认回退到 OpenAI

- `llm_adapter.py` 中：
  - `OPENAI_BASE_URL` 默认值为 `https://api.openai.com/v1`
  - `OPENAI_MODEL` 默认值为 `gpt-4.1-mini`

这意味着：

- 如果页面没有把 `OpenCode Go` 的 `Base URL / Model` 正确写回环境变量
- 即使 `API key` 是 `OpenCode` 的，也会被发往 OpenAI

### 证据 B：最小复现与用户报错完全一致

- 仅设置 `OPENAI_API_KEY=<opencode key>` 时：
  - 返回 `HTTP 401`
  - 返回体中包含 `Incorrect API key provided`
  - 文案明确指向 `platform.openai.com`

### 证据 C：完整 Go 配置时同一 key 成功

- 同时设置：
  - `OPENAI_BASE_URL=https://opencode.ai/zen/go/v1`
  - `OPENAI_API_PATH=chat/completions`
  - `OPENAI_MODEL=deepseek-v4-pro`
  - `OPENAI_USER_AGENT=climate-policy-sandbox/1.0`
- 同一 key 在同一服务器上成功运行，结果为：
  - `CASE2_SUCCESS openai-compatible:deepseek-v4-pro 分歧仍然明显`

## 6. 假设验证结果

1. 页面里的 `Base URL` 仍然是 OpenAI 地址
   - `当前最可能成立`
   - 证据：最小复现完全匹配用户错误

2. `Streamlit` 小部件没有正确显示或保留服务器环境变量默认值
   - `部分成立`
   - 证据：旧会话可能保留旧控件值；新增默认值后仍需显式确认当前生效配置

3. 点击“运行推演”后环境变量被清空但未正确写回
   - `缺少直接证据`
   - 当前不作为首要结论

4. 只有 key 被带入，`Base URL / Model` 没同步
   - `成立`
   - 证据：这正是最小复现中的失败条件

## 7. 最小修复

- 在 `streamlit_app.py` 中：
  - 使用新的 `session_state` 键初始化模型配置
  - 新增“载入服务器预置配置”按钮
  - 新增“当前生效配置”显示
  - 当 `deepseek-v4-pro` 配合非 `opencode.ai` 地址时给出警告

## 8. 当前状态

- 已在新端口 `8503` 启动修复后的页面
- 新入口：`http://10.103.69.253:8503`
