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

## 2026-05-26

### Step 12. 仓库独立化与 GitHub 同步

- 将 `/data/hanzhang/homework/AI4GC` 初始化为独立 git 仓库
- 新增 `.gitignore`，排除了缓存、日志、环境变量文件和浏览器临时目录
- 已推送到 GitHub：
  - `https://github.com/uni8033/climate_policy_sandbox.git`

### Step 13. 2.0 beta 角色系统升级

- 将 `prototype_v1/data/agents.json` 从 4 个角色扩展为 7 类角色
- 为每个角色新增：
  - `bloc`
  - `design_rationale`
  - `evidence_basis`
  - `priority_asks`
- 当前角色不再只是课堂直觉设定，而是显式对应：
  - NDC/净零承诺
  - World Bank 发展与融资约束
  - ND-GAIN 脆弱性与适应能力

### Step 14. 2.0 beta 谈判流程升级

- 将原来的“三轮固定推演”升级为六阶段流程：
  - 立场陈述
  - 冲突识别
  - 联盟与分裂
  - 条件交换
  - 秘书处修订
  - 最终表决
- 引擎现在会额外输出：
  - 潜在联盟
  - 摇摆方
  - 修订前后属性变化
  - 初始表态到最终表决的立场变化

### Step 15. Streamlit 页面升级

- 页面标题更新为 `v2.0 beta`
- 增加更接近产品 demo 的头图和结构
- 新增 4 个页面标签：
  - `总览`
  - `谈判流程`
  - `角色设计`
  - `结构化输出`
- 页面现在可以直接展示：
  - 最终立场表
  - 立场变化表
  - 政策修订前后对比
  - 联盟与关键摇摆方
  - 每个角色的设计依据

### Step 16. 本轮运行验证

- `python3 run_demo.py` 已成功运行
- 生成结果文件：
  - `prototype_v1/results/demo_run_output.json`
  - `prototype_v1/results/demo_run_report.md`
- 当前样例结果：
  - 共识水平：`有限妥协`
  - 落地可行性：`76.2`
  - 公平性：`25.0`
  - 阻力强度：`32.8`

### Step 17. 当前可直接访问的 demo

- 2.0 beta Streamlit 已启动
- 当前访问地址：
  - `http://10.103.69.253:8504`

### Step 18. 2.1 现实世界数据接地启动

- 新建来源目录文件：
  - `prototype_v1/data/source_catalog.json`
- 新建现实世界样本国家文件：
  - `prototype_v1/data/real_world_entities.json`
- 新建说明文档：
  - `prototype_v1/real_world_data_notes.md`

### Step 19. 当前已落地的真实来源

- `UNFCCC NDC Registry`
  - 用于官方 NDC 文本追溯
  - 可靠性标记：`A`
- `World Bank Open Data API`
  - 用于 GDP、人均收入、可再生能源占比、燃料出口占比等指标
  - 可靠性标记：`A-`
- `ND-GAIN Country Index`
  - 用于国家脆弱性与适应准备度
  - 可靠性标记：`B+`
- `Climate Watch`
  - 用于结构化查看国家 NDC 提交状态和辅助比较
  - 可靠性标记：`B`

### Step 20. 当前样本国家

- `德国`：发达经济体样本
- `中国`：大型新兴经济体样本
- `印度`：高脆弱发展中大国样本
- `沙特阿拉伯`：化石能源出口国样本
- `斐济`：小岛屿高脆弱国家样本

### Step 21. 页面同步更新

- `streamlit_app.py` 已新增现实世界数据展示区
- 页面中现在可以直接查看：
  - 数据来源目录
  - 可靠性等级
  - 每个样本国家的字段、年份和来源
  - 官方 NDC 主来源与辅助结构化来源

### Step 22. 当前仍未完成的现实化部分

- 还没有把官方 NDC PDF 逐条结构化解析为可直接推演的政策约束
- 角色系统目前仍然是抽象谈判角色为主，现实世界样本国家库为辅助证据层
- 下一步应把样本国家直接接入角色生成逻辑

### Step 23. 首批真实政策承诺结构化

- 新增：
  - `prototype_v1/data/real_policy_profiles.json`
- 当前已完成结构化摘要的样本：
  - `德国/欧盟共同 NDC 入口`
  - `中国`
  - `印度`
  - `沙特阿拉伯`
  - `斐济`

### Step 24. 当前结构化了哪些真实字段

- `submission_date`
- `target_year`
- `target_type`
- `baseline_year`
- `mitigation_summary`
- `adaptation_included`
- `sector_scope`
- `conditionality_note`
- `primary/secondary source`
- `reliability_summary`

### Step 25. 页面新增政策画像展示

- `streamlit_app.py` 现在不仅展示国家背景数据，还展示：
  - 真实承诺文档名称
  - 提交日期
  - 目标年份
  - 目标类型
  - 主要减排摘要
  - 条件性说明

### Step 26. 当前判断

- 项目已经从“抽象角色设定”进入“抽象角色 + 真实国家证据层”的过渡阶段
- 下一步的关键，不是再继续堆样本数量，而是：
  - 让样本国家直接生成谈判主体
  - 让真实承诺字段进入推演约束逻辑

### Step 27. 真实国家样本模式已接入引擎

- `ClimatePolicySandbox` 现已支持两种模式：
  - `abstract`
  - `real_countries`
- `real_countries` 模式下，当前 5 个样本国家直接参与推演：
  - `德国`
  - `中国`
  - `印度`
  - `沙特阿拉伯`
  - `斐济`

### Step 28. 当前国家模式的权重生成依据

- 背景指标：
  - 人均 GDP
  - 可再生能源占比
  - 燃料出口占比
  - ND-GAIN 脆弱性
  - ND-GAIN 准备度
- 政策约束：
  - NDC 目标类型
  - 目标年份
  - 条件性说明
  - 是否包含适应内容

### Step 29. 页面已可切换推演主体

- `streamlit_app.py` 已新增：
  - `抽象角色模式`
  - `真实国家样本模式`
- 用户现在可以直接对比：
  - 结构更清晰的抽象角色推演
  - 真实性更强的国家样本推演

### Step 30. 当前诚实边界

- 当前国家模式仍然属于“规则驱动的现实约束近似”
- 不是严格的计量模型，也不是基于大规模历史谈判数据训练得到
- 但它已经比纯人工角色设定更接近“可追溯、可解释、可继续改进”的现实化版本

### Step 31. 真实主体继续扩展

- 新增 4 个真实国家样本：
  - `美国`
  - `巴西`
  - `印度尼西亚`
  - `孟加拉国`
- 当前真实国家样本模式总计 9 个主体：
  - `德国`
  - `美国`
  - `中国`
  - `巴西`
  - `印度`
  - `印度尼西亚`
  - `沙特阿拉伯`
  - `斐济`
  - `孟加拉国`

### Step 32. 真实性增强的关键变化

- 不再只生成“偏好权重”
- 现在还会根据：
  - NDC 目标类型
  - 条件性承诺说明
  - 脆弱性与准备度
  - 收入水平
  - 燃料出口依赖
  生成“谈判硬约束”

### Step 33. 当前硬约束机制

- `min_requirements`
  - 用于表达某国至少需要的融资、适应或技术转移支持
- `max_tolerances`
  - 用于表达某国对化石退出、碳边境约束等议题的最大容忍度
- 当政策超出这些边界时：
  - 系统会增加现实约束触发记录
  - 并下调该国最终立场

### Step 34. 当前特别需要保留的真实性提醒

- `美国`
  - 最新已提交 NDC 可以追溯
  - 但 2025 年后不再具有活跃 NDC 状态
  - 因此在项目中只能作为“最新已提交承诺参考”，不能简单视作稳定有效的现行国际承诺

### Step 35. 页面同步更新

- 页面中的真实国家模式说明已从 5 个样本更新为 9 个样本
- `角色设计` 页现在会显示：
  - 最低需求
  - 最大容忍度
  - 约束依据
- 谈判流程页现在会显示：
  - 原始立场
  - 被现实约束下调后的立场
  - 触发了哪些约束

### Step 36. 高分版研究模式启动

- 新增 `情景实验` 运行形态
- 同一条政策文本现在可以在 5 组预设情景下批量运行
- 输出内容新增：
  - 情景对比表
  - 自动研究发现
  - 方法与局限页

### Step 37. 当前预设情景

- `基线情景`
- `高雄心低补偿`
- `高雄心配套补偿`
- `过渡优先`
- `公平融资优先`

### Step 38. 这一轮的意义

- 项目不再只是“单次推演 demo”
- 而是开始具备：
  - 可比较实验
  - 自动结果分析
  - 可直接用于课程汇报的研究发现输出

### Step 39. 新增 LULUCF 维度

- 在核心引擎中新增 `森林/LULUCF 支持` 维度
- 自动识别逻辑现在会识别：
  - `forest`
  - `forestry`
  - `LULUCF`
  - `碳汇`
  - `森林`
  - `土地利用`
- 该维度会影响国家权重、谈判硬约束、联盟识别和最终情景评分

### Step 40. 真实样本与 LULUCF 对齐

- 重新固化 9 国样本数据
- 为每个样本增加 `lulucf_relevance` 标注
- 对 `巴西 / 印度 / 印度尼西亚` 明确标为高相关样本

### Step 41. 情景实验可视化增强

- 新增核心指标对比图
- 新增现实约束触发频率图
- 新增情景属性矩阵
- 目标是让研究发现更适合课堂展示，而不仅是命令行输出
