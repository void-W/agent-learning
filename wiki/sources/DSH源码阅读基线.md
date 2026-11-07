# DSH 源码阅读基线

- 类型：源码来源记录
- 创建／更新：2026-11-07（Asia/Shanghai）
- 证据范围：下列文件的局部阅读；非全仓审计、非运行验证

## 仓库与版本

- 仓库：[deepseek-ai/deepseek-harness](https://github.com/deepseek-ai/deepseek-harness)。
- 本次固定 commit：[`fcc0ad462172522aaf5c93a7b2e01f6b9f0b0159`](https://github.com/deepseek-ai/deepseek-harness/tree/fcc0ad462172522aaf5c93a7b2e01f6b9f0b0159)。
- 本地检出分支：`master`；分支会移动，知识页以 commit 为准。
- 获取方式：用户指定仓库的本地 Git clone，通过文本工具读取源码与包文档；没有安装依赖或运行测试。

## 已阅读的证据位置

以下链接均固定到上面的 commit。表内只列本批知识页依赖的阅读范围。

| 源文件 | 已核对范围 | 用途 |
| --- | --- | --- |
| [agent-instructions README.zh.md](https://github.com/deepseek-ai/deepseek-harness/blob/fcc0ad462172522aaf5c93a7b2e01f6b9f0b0159/packages/context/agent-instructions/README.zh.md#L10-L239) | 配置、流程、消息模板和限制 | 支持范围及追加式更新语义 |
| [agent-instructions index.ts](https://github.com/deepseek-ai/deepseek-harness/blob/fcc0ad462172522aaf5c93a7b2e01f6b9f0b0159/packages/context/agent-instructions/src/index.ts#L75-L375) | 文件工具识别、组合、投影、pre-step 和结果监听 | 文件 touch 到待处理消息的路径 |
| [agent-instructions state.ts](https://github.com/deepseek-ai/deepseek-harness/blob/fcc0ad462172522aaf5c93a7b2e01f6b9f0b0159/packages/context/agent-instructions/src/state.ts#L39-L101) | 来源类型与消息构造 | 指令消息的 role、content、source |
| [LLM message.ts](https://github.com/deepseek-ai/deepseek-harness/blob/fcc0ad462172522aaf5c93a7b2e01f6b9f0b0159/packages/llm/llm/src/message.ts#L224-L253) | 消息身份及用户消息构造 | `createUserMessage` 明确设置 user 角色 |
| [agent-loop agent.ts：步骤](https://github.com/deepseek-ai/deepseek-harness/blob/fcc0ad462172522aaf5c93a7b2e01f6b9f0b0159/packages/core/agent-loop/src/agent.ts#L283-L490) | pre-step、步骤结束和消息入历史 | 注入与工具结果的时序 |
| [agent-loop agent.ts：请求](https://github.com/deepseek-ai/deepseek-harness/blob/fcc0ad462172522aaf5c93a7b2e01f6b9f0b0159/packages/core/agent-loop/src/agent.ts#L655-L744) | 请求配置与派生消息 | 内部模型请求的构造 |
| [Session index.ts](https://github.com/deepseek-ai/deepseek-harness/blob/fcc0ad462172522aaf5c93a7b2e01f6b9f0b0159/packages/core/session/src/index.ts#L980-L1019) | `deriveMessages` | 当前有效历史的派生 |
| [Session surface.ts](https://github.com/deepseek-ai/deepseek-harness/blob/fcc0ad462172522aaf5c93a7b2e01f6b9f0b0159/packages/core/session/src/surface.ts#L120-L151) | 事件到消息的映射 | user 消息正文保持，非消息事件不入请求 |
| [DeepSeek serialize.ts](https://github.com/deepseek-ai/deepseek-harness/blob/fcc0ad462172522aaf5c93a7b2e01f6b9f0b0159/packages/llm/llm-deepseek/src/serialize.ts#L1-L169) | 请求序列化 | 工具结果转换、同角色合并和调用匹配校验 |

## 知识产出

- [DSH 从工作区指令到模型请求](../implementations/DSH工作区指令到模型请求.md)：实现事实的主要维护位置。
- [工作区指令与上下文注入](../concepts/工作区指令与上下文注入.md)：从实例抽取的问题与设计建议。
- [API adapter 与输入语义](../concepts/API适配器与模型输入语义.md)：区分结构性事实与待验证的效果差异。

## 阅读限制

没有检查全部 provider、端到端网络请求、服务端提示模板或模型输出；没有验证所有并发、恢复和压缩路径。当前本地仓库版本也不等于正在运行的桌面 DSH 版本。不可据此宣称实际 GUI 的每一个请求与此 commit 完全相同。

第三方 Claude Code 项目已在本地克隆，但尚未开展本批主题的源码阅读或来源身份核实；不作为上述结论的证据。

返回 [知识导航](../知识导航.md)。
