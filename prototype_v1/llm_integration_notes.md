# 真实大模型接入说明

## 当前已经支持什么

当前原型已经支持通过 `OpenAI-compatible` 方式调用外部模型。

可配置项包括：

- `OPENAI_API_KEY`
- `OPENAI_BASE_URL`
- `OPENAI_API_PATH`
- `OPENAI_MODEL`

其中：

- `OPENAI_BASE_URL` 例如：`https://opencode.ai/zen/v1`
- `OPENAI_API_PATH` 一般是：
  - `chat/completions`
  - 或 `responses`

## 当前代码支持的两种接口

### 1. Chat Completions

适合大多数 `OpenAI-compatible` 模型接口。

请求格式：

- `messages`
- `model`
- `temperature`

### 2. Responses

适合部分新版接口。

请求格式：

- `input`
- `model`
- `temperature`

## 如何快速试跑

### 方式一：直接打开 Streamlit

```bash
cd /data/hanzhang/homework/AI4GC/prototype_v1
python3 -m streamlit run streamlit_app.py
```

然后：

1. 切换到 `真实模型模式`
2. 输入 `API Key`
3. 输入 `Base URL`
4. 输入 `API Path`
5. 输入 `Model`
6. 点击 `运行推演`

### 方式二：命令行脚本

```bash
cd /data/hanzhang/homework/AI4GC/prototype_v1
export OPENAI_API_KEY="你的key"
export OPENAI_BASE_URL="https://opencode.ai/zen/v1"
export OPENAI_API_PATH="chat/completions"
export OPENAI_MODEL="qwen3.6-plus"
python3 run_llm_demo.py
```

## 当前测试情况

我已经完成了代码层面的接入改造，并尝试在当前运行环境直接测试外部接口。

测试现象：

- 访问 `chat/completions` 返回：`403`
- 访问 `responses` 返回：`403`
- 返回信息里出现：`error code: 1010`

这通常更像是：

- 当前托管环境被对方网关风控
- 当前 IP / 运行环境被访问策略拦截
- 或目标服务对该环境不允许直接访问

因此当前结论是：

- `代码接入已经完成`
- `当前环境下远端请求被拦截`
- `不代表你本机环境无法调用`

## 最建议的使用方式

如果你想继续推进实际可运行 demo，建议：

1. 在你自己的电脑上打开 `Streamlit`
2. 先测试 `chat/completions`
3. 如果不通，再改测 `responses`
4. 一旦某个组合能通，就把对应的 `base_url + api_path + model` 固定下来

## 当前相关文件

- `llm_adapter.py`
- `streamlit_app.py`
- `run_llm_demo.py`

这三份文件已经是当前真实模型接入的核心实现。
