# Karpathy：LLM Wiki 阅读笔记

- 类型：来源总结
- 创建／更新：2026-11-07（Asia/Shanghai）
- 证据范围：文章完整正文；观点未通过本仓库的长期使用验证

## 来源记录

- 作者：Andrej Karpathy（Gist 账号 `karpathy`）。
- 原文：[LLM Wiki](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f)。
- 固定修订：`ac46de1ad27f92b28ac95459c782c07f6b8c964a`。
- 下载地址：[固定修订原文](https://gist.githubusercontent.com/karpathy/442a6bf555914893e9891c11519de94f/raw/ac46de1ad27f92b28ac95459c782c07f6b8c964a/llm-wiki.md)。
- 摄入日期：2026-11-07；[本地快照](../../raw/articles/karpathy-llm-wiki-ac46de1.md)，保留下载字节，未翻译或改写。
- 快照 SHA-256：`dc3efe98ae62f23dd08acad13aba2e95287beb20b6bec2f4af0423557fe37401`。

## 文章主张

**来源观点**：与每次查询时重新从原始文档拼接答案相比，LLM 可以增量维护持久 Wiki，将摘要、概念、实体关系、综合分析和冲突记录保留下来，使阅读与提问的成果持续积累。文章对 RAG 的对比是作者用来阐述模式的概括，不意味着所有 RAG 系统都没有积累机制。证据见 [核心思路](../../raw/articles/karpathy-llm-wiki-ac46de1.md#the-core-idea)。

**来源观点**：原始材料、生成 Wiki、维护 schema 构成三层；原始材料不变，Wiki 持续更新，schema（如 `AGENTS.md`）定义结构和操作约定。见 [架构](../../raw/articles/karpathy-llm-wiki-ac46de1.md#architecture)。

**来源观点**：摄入新材料不仅创建摘要，还更新已有知识和引用；查询产生的高价值回答可以写回 Wiki；lint 用于发现矛盾、过时结论、孤立页和知识缺口。见 [操作](../../raw/articles/karpathy-llm-wiki-ac46de1.md#operations)。

**来源观点**：内容导航与时间日志用途不同；小规模可以先用 Markdown 和索引，需要时再引入搜索、Obsidian 等工具。见 [索引与日志](../../raw/articles/karpathy-llm-wiki-ac46de1.md#indexing-and-logging) 及 [可选工具](../../raw/articles/karpathy-llm-wiki-ac46de1.md#optional-cli-tools)。

## 本仓库采用的取舍

**已采纳的建设方向**：由用户选材料、提问题和审核，Agent 帮助整理维护；先使用 Markdown、Git、导航和日志，不搭建向量数据库或自动摄入系统。具体规则见 [维护规则](../../AGENTS.md)。

**补充约束**：固定源码版本；区分事实、观点、假设和设计建议；不把第三方复原代码当作官方来源；不自动 commit 或 push。文章提供模式，不提供这些具体工程约束。

**限制与风险**：作者关于低维护成本和跨页维护能力的积极判断，不是准确性保证。Agent 可能遗漏交叉引用、把假设写成事实或引入矛盾，因此保留证据与人工审阅，并按需检查。

## 如何应用到 Harness 学习

一段 [DSH 源码分析](../implementations/DSH工作区指令到模型请求.md) 可同时支撑 [工作区指令概念](../concepts/工作区指令与上下文注入.md) 与 [adapter 输入语义](../concepts/API适配器与模型输入语义.md)。之后的阅读应修订这些页面、补充反例或版本差异，而不是反复创建同义摘要。

## 开放问题

- 哪些讨论值得写回，哪些只保留为临时问答？当前采用按任务和用户意图判断。
- 怎样识别上游更新使某项实现事实过时？先记录 commit，未来根据实际维护负担再考虑自动化。
- 何时需要搜索工具？当前页面数量不足以证明需要新基础设施。

返回 [知识导航](../知识导航.md)。
