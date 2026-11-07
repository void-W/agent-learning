# Agent learning

这是围绕 Agent 与插件式 Harness 的个人学习知识库，采用 Karpathy 的 [LLM Wiki](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) 模式。目标是将阅读、源码分析、讨论与实验转化为可追溯、相互链接、持续修订的知识，而不是仅保存聊天或逐篇堆积摘要。

## 从这里开始

- [知识导航](wiki/知识导航.md)：按来源、概念、实现和探索查找页面。
- [维护规则](AGENTS.md)：Agent 摄入、查询、更新和检查知识库的约定。
- [演进日志](wiki/演进日志.md)：已经完成的知识库操作。
- [原始材料说明](raw/README.md)：已归档的原文与来源保留约定。
- [LLM Wiki 阅读笔记](wiki/sources/LLM-Wiki阅读笔记.md)：建设模式和本仓库的取舍。
- [下一步学习问题](wiki/explorations/Harness下一步学习问题.md)：当前尚未解决的问题。
- [思考强度缓存验证脚本](experiments/思考强度缓存验证/README.md)：固定输入、只切 effort，读取官方 API 的缓存命中。

## 三个层次

| 层次 | 位置 | 职责 |
| --- | --- | --- |
| 原始材料 | `raw/` | 保留文章快照、摘录和原始实验记录；摄入后不改写 |
| 知识 Wiki | `wiki/` | 整合来源，维护概念、实现分析、比较和未知问题 |
| 维护规则 | 本页链接的维护规则 | 规定页面组织、证据要求和摄入／查询／检查流程 |

原始代码保留在其独立 Git 仓库；知识页通过固定 commit 的 GitHub 链接引用，不复制整份源码，也不依赖机器上的绝对路径。

## 日常使用

1. **摄入**：提供一篇文章、一段源码或一次实验；先核对来源，再更新已有知识及索引、日志。
2. **查询**：先从知识导航找相关页面，区分已知与未知，必要时回到原始材料。值得保留的回答再沉淀为页面。
3. **检查**：按需检查断链、孤立页面、过时事实、矛盾和缺失证据；不自动启动定时任务。
4. **验证**：用 `experiments/` 下的脚本产生可重复读数，再把结果回填到对应 Wiki 页；脚本运行可能产生 API 费用，先干跑并确认。

可以这样发起任务：“摄入这篇文章”“追踪 DSH 的工具执行生命周期”“把这次讨论中已核实的结论写回 Wiki”“检查知识库是否有断链和过时结论”。

## 学习材料与实现目标

- [DeepSeek Harness](https://github.com/deepseek-ai/deepseek-harness)：当前已阅读的实现材料，具体分析限定到固定 commit。
- [claude-code-best/claude-code](https://github.com/claude-code-best/claude-code)：第三方项目，仅作为待核实学习材料；不将其视为已确认的 Anthropic 官方源码。
- [plugin-harness-go](https://github.com/void-W/plugin-harness-go)：自己的 Go 插件式 Harness 实现目标；知识库中的建议不代表代码已实现。

## 当前范围

首批页面覆盖工作区指令注入、Session 到模型消息的派生，以及 API adapter 对请求表达的影响。思考强度缓存验证已完成一次官方 API 实测（`high → low` 命中率 0.00%，同 effort 对照 90.10%）；尚未系统分析 Claude Code 项目。

以中文为主，保留必要的英文术语。Git 提供版本历史；Agent 默认只修改本地文件，commit、push 和认证变更需要用户明确授权。Markdown 可直接在 GitHub 或 Obsidian 阅读，当前无需安装额外依赖、搜索引擎或数据库。
