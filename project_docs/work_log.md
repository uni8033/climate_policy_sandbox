# 项目工作日志

## 2026-05-18

### Step 1. 项目重定位与目标确认

- 目标从“只做 PPT 方案”推进到“开始做真实项目原型”
- 确认本轮任务包括：
  - 写项目规划
  - 做 `1.0` 原型
  - 跑样例结果
  - 准备课堂简报材料

### Step 2. 复盘已有材料

- 复盘了 `idea.md`
- 复盘了现有 PPT、讲稿和项目记忆
- 确认已有的设计共识：
  - 使用云端模型 API 作为后续增强方向
  - 当前先做最小可运行闭环
  - 优先使用 Python + Streamlit 的开发路线

### Step 3. 工作区初始化

- 新建目录：
  - `project_docs/`
  - `prototype_v1/`
  - `prototype_v1/data/`
  - `prototype_v1/results/`
  - `prototype_v1/logs/`

### Step 4. 当前开发策略

- 先实现 `规则引擎 + Prompt 风格模板` 版本
- 不强依赖在线 API
- 保证原型在本地可运行、可复现、可讲清楚

### Step 5. 下一步计划

- 写完项目规划文件
- 搭建 `1.0` 代码
- 运行样例并生成结果文件
- 输出课堂汇报材料

### Step 6. 1.0 原型文件搭建

- 新建了：
  - `prototype_v1/README.md`
  - `prototype_v1/prompt_design.md`
  - `prototype_v1/llm_adapter.py`
  - `prototype_v1/climate_policy_engine.py`
  - `prototype_v1/run_demo.py`
  - `prototype_v1/streamlit_app.py`
  - `prototype_v1/data/agents.json`
  - `prototype_v1/data/demo_policy.json`
  - `project_docs/tomorrow_pipeline_ai_share.md`

### Step 7. Demo 跑通

- 在 `prototype_v1/` 下运行了：
  - `python3 run_demo.py`
- 已生成：
  - `prototype_v1/results/demo_run_output.json`
  - `prototype_v1/results/demo_run_report.md`
  - `prototype_v1/logs/run_history.log`

### Step 8. 初步结果判断

- 第一轮呈现明显两极分化
- 第二轮之后发展中国家代表明显松动
- 第三轮形成相对稳定的有限妥协
- 当前原型已经能展示：
  - 角色差异
  - 谈判条件调整
  - 结构化结果输出

### Step 9. 当前版本的主要局限

- 发言文本仍偏模板化
- 数据还没有真正接入
- 适应/损失补偿机制还不够强
- 前端展示还只是初步版本

### Step 10. 下一轮开发重点

- 优先把 `Streamlit` 页面补强
- 增加更真实的观察员总结逻辑
- 开始考虑接入真实数据子集

### Step 11. 运行环境核验

- Python 脚本已通过 `py_compile` 语法检查
- `streamlit` 可通过 `python3 -m streamlit run streamlit_app.py` 启动
- 发现当前环境下直接使用 `streamlit run ...` 入口会报错，因此在说明文档中已改为更稳妥的启动命令
