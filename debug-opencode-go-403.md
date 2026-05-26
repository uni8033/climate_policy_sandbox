# [OPEN] Debug Session: opencode-go-403

## 1. 问题摘要

- 目标：在当前服务器上使用 `OpenCode Go` 模式的 API key 跑通真实模型 demo
- 当前现象：请求 `https://opencode.ai/zen/go/v1/chat/completions` 返回 `403 / error code: 1010`
- 目标模型：`deepseek-v4-pro`

## 2. 当前状态

- 状态：`OPEN`
- 调试阶段：`假设与证据收集`
- 当前约束：在获得更多运行时证据前，不修改业务逻辑

## 3. 初始假设

1. 当前服务器出口 IP 或运行环境被 `OpenCode` 网关风控，导致任何有效请求都被 `1010` 拦截。
2. `OpenCode Go` 模式除了 `Authorization` 外，还要求特定的请求头或来源标识，当前请求未满足。
3. 模型 ID 与接口路径虽然看起来正确，但该 key 实际没有对应模型或对应接口权限，网关直接拒绝。
4. 当前服务器到 `opencode.ai` 的网络路径经过了某种中间层，触发了 CDN / WAF 拦截。
5. 该 key 本身可用，但只能从特定客户端或特定工作流访问，直接用裸 HTTP 请求会被拒绝。

## 4. 已知事实

- 已测试 `https://opencode.ai/zen/go/v1/chat/completions`
- 已测试模型：
  - `deepseek-v4-pro`
  - `opencode-go/deepseek-v4-pro`
- 两次都返回 `403 / error code: 1010`

## 5. 下一步计划

1. 收集更完整的 HTTP 响应头与返回体
2. 探测是否存在额外必需请求头或 User-Agent 要求
3. 对比根路径、OPTIONS、HEAD、GET 等行为，判断是 API 层拒绝还是 CDN/WAF 层拒绝
4. 若证据指向环境限制，则给出当前服务器不可直连的结论和本机复现方案

## 6. 运行时证据

### 证据 A：补充请求头后单次 POST 调用成功

- `GET https://opencode.ai/zen/go/v1/` 返回 `404`
- `GET https://opencode.ai/zen/go/v1/chat/completions` 返回 `404`
- `POST https://opencode.ai/zen/go/v1/chat/completions` 在附带以下请求头后返回 `200`
  - `Authorization`
  - `Content-Type`
  - `Accept`
  - `User-Agent`

返回结果中包含：

- `model: deepseek-v4-pro`
- `choices[0].message.content: OK`

### 证据 B：真实原型代码一轮推演成功

- 使用配置：
  - `OPENAI_BASE_URL=https://opencode.ai/zen/go/v1`
  - `OPENAI_API_PATH=chat/completions`
  - `OPENAI_MODEL=deepseek-v4-pro`
  - `OPENAI_USER_AGENT=climate-policy-sandbox/1.0`
- 运行结果：
  - `NARRATOR openai-compatible:deepseek-v4-pro`
  - `CONSENSUS 分歧仍然明显`
  - `SCORES {'feasibility': 50.0, 'fairness': 0.0, 'resistance': 59.0}`

## 7. 假设验证结果

1. 当前服务器出口被风控，任何请求都会命中 `1010`
   - `部分否定`
   - 证据：补充请求头后的 POST 调用已返回 `200`

2. `OpenCode Go` 端点需要额外请求头或特定客户端指纹
   - `当前最可能成立`
   - 证据：原先请求返回 `403 / 1010`，补充 `Accept` 和 `User-Agent` 后同一端点同一模型成功返回

3. key 对该模型或接口没有权限
   - `否定`
   - 证据：`deepseek-v4-pro` 已成功返回有效结果

4. 当前网络链路异常导致所有请求不可用
   - `否定`
   - 证据：真实请求可达并返回有效 JSON

5. 该 key 只能在官方客户端使用，裸 HTTP 一定失败
   - `否定`
   - 证据：裸 HTTP 已在当前环境成功调用

## 8. 当前结论

- 根因更接近于：`请求头不完整导致网关/WAF 将请求识别为异常客户端`
- 最小修复已完成：
  - 在 `llm_adapter.py` 中补充 `Accept` 与 `User-Agent`
- 当前状态：
  - `一轮真实模型 demo 已在服务器上跑通`
  - `完整多轮 demo 仍可继续尝试，但耗时更长`
