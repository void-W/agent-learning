# DSH：从工作区指令到模型请求

- 类型：实现分析
- 创建／更新：2026-11-07（Asia/Shanghai）
- 证据范围：[DSH 源码阅读基线](../sources/DSH源码阅读基线.md)，commit `fcc0ad462172522aaf5c93a7b2e01f6b9f0b0159`
- 方法：源码与包文档阅读；未运行代码或抓取实际 API 请求

## 结论

**实现事实**：工作区规则由 `dsh-agent-instructions` 创建为 user 角色上下文，经步骤前处理进入持久 `user/message` 事件，再从有效历史派生到内部请求 `messages`。具体 provider 随后转换线上格式；内部独立消息不保证在线上仍是独立消息。

## 发现范围

**文档规定的行为**：`dsh-base` 默认包含指令插件，profile 可禁用。默认以 `.git` 识别项目根，加载根到会话工作目录的候选文件；支持 `AGENTS.md`、`CLAUDE.md` 及各自的 local overlay。用户全局链与项目链分别限制预算，base 为每条链配置 65,536 字节，而不是两条链共享 64 KiB。出处：[插件文档](https://github.com/deepseek-ai/deepseek-harness/blob/fcc0ad462172522aaf5c93a7b2e01f6b9f0b0159/packages/context/agent-instructions/README.zh.md#L10-L68)。

不是递归扫描整个工作区的所有规则。更深目录的发现跟随成功的结构化文件工具操作；不通过任意 bash 命令的目录变化发现规则。外部编辑不是由持续 watcher 监测，后续 touch／恢复等时机才会对账。出处：[范围与限制](https://github.com/deepseek-ai/deepseek-harness/blob/fcc0ad462172522aaf5c93a7b2e01f6b9f0b0159/packages/context/agent-instructions/README.zh.md#L219-L228)。

## 消息构造

[来源类型和构造函数](https://github.com/deepseek-ai/deepseek-harness/blob/fcc0ad462172522aaf5c93a7b2e01f6b9f0b0159/packages/context/agent-instructions/src/state.ts#L39-L101) 使用 `createUserMessage`；[该构造器](https://github.com/deepseek-ai/deepseek-harness/blob/fcc0ad462172522aaf5c93a7b2e01f6b9f0b0159/packages/llm/llm/src/message.ts#L241-L253) 明确设置 `role: 'user'`。以下为简化示意，不是抓取的请求或完整 schema：

```ts
{
  id: "message-id",
  role: "user",
  content: [{
    type: "text",
    text: "<system-reminder>\nAdditional instructions from: pkg/AGENTS.md\n…\n</system-reminder>"
  }],
  source: {
    kind: "agent-instructions",
    form: "instructions",
    changes: [/* 文件、scope、变更记录 */]
  }
}
```

`<system-reminder>` 是模型可见文本，不是 system 角色。基线来源还可有 `baseline` 与 `baselineIdentity`，用于识别完整基线和恢复对账。

## 工具结果到下一步

**实现事实**：插件识别 `read`、`write`、`edit` 的 `file_path`，只为成功且未取消的执行添加自身 touch。嵌套执行的 touch 先沿 parent token 上浮，待外层执行完成；如果会话步骤仍打开，则待 `step/end` 后排队投影。出处：[工具识别](https://github.com/deepseek-ai/deepseek-harness/blob/fcc0ad462172522aaf5c93a7b2e01f6b9f0b0159/packages/context/agent-instructions/src/index.ts#L75-L83)、[步骤边界与结果监听](https://github.com/deepseek-ai/deepseek-harness/blob/fcc0ad462172522aaf5c93a7b2e01f6b9f0b0159/packages/context/agent-instructions/src/index.ts#L304-L374)。

```text
read / write / edit 成功
  → 记录触及路径，等待外层执行和持久步骤结束
  → 对账规则内容与可见历史
  → next-step inbox 中排队或替换尚未提交的规则消息
  → 下一次 agent/pre-step 等待投影完成
  → 将规则折入本次进入步骤的消息批次
```

[pre-step 监听器](https://github.com/deepseek-ai/deepseek-harness/blob/fcc0ad462172522aaf5c93a7b2e01f6b9f0b0159/packages/context/agent-instructions/src/index.ts#L330-L355) 在调用 `next()` 后等待投影，对账待处理规则，将新增上下文插到已领取批次之后、driver 追加的运行时上下文之前。若步骤被拒绝或首次进入没有消息，则保持待处理上下文，不凭规则单独启动该首次请求。

## 先记录，再派生请求

[Agent loop](https://github.com/deepseek-ai/deepseek-harness/blob/fcc0ad462172522aaf5c93a7b2e01f6b9f0b0159/packages/core/agent-loop/src/agent.ts#L462-L479) 将批次中的规则以 `surfaceOp: 'append'` 写入 `user/message`。不是文件插件临时修改已经构造好的请求：

```ts
session.append("user/message", instructionMessage, { surfaceOp: "append" });
// 后续构造请求时：
const messages = session.deriveMessages();
```

[事件映射](https://github.com/deepseek-ai/deepseek-harness/blob/fcc0ad462172522aaf5c93a7b2e01f6b9f0b0159/packages/core/session/src/surface.ts#L120-L151) 为 user 事件保留消息数据，非消息事件不产生模型消息。[派生逻辑](https://github.com/deepseek-ai/deepseek-harness/blob/fcc0ad462172522aaf5c93a7b2e01f6b9f0b0159/packages/core/session/src/index.ts#L980-L1019) 遍历当前有效 surface，而不是无区别地把所有日志发送出去；[请求构造](https://github.com/deepseek-ai/deepseek-harness/blob/fcc0ad462172522aaf5c93a7b2e01f6b9f0b0159/packages/core/agent-loop/src/agent.ts#L724-L742) 将结果作为 `messages`。

## DeepSeek API 序列化

**实现事实**：[DeepSeek serializer](https://github.com/deepseek-ai/deepseek-harness/blob/fcc0ad462172522aaf5c93a7b2e01f6b9f0b0159/packages/llm/llm-deepseek/src/serialize.ts#L118-L144) 将内部 tool 消息转换为 `tool_result` 内容块，外层角色映射为 user；相邻同角色消息合并。内部 `id`、`source` 不作为这些 wire 消息的字段发送。它还检查工具调用与结果关联，并在合并后的 user 内容中将工具结果排在其他块之前。

简化后的线上片段可能是：

```ts
{
  role: "user",
  content: [
    { type: "tool_result", tool_use_id: "call-id", content: [/* 工具输出 */] },
    { type: "text", text: "<system-reminder>新增指令…</system-reminder>" }
  ]
}
```

该片段为代码推导示意，未通过网络抓取验证。它不等于所有 provider 的输出，也不是正在运行的桌面应用请求的完整描述。适配差异的分析见 [API adapter 与输入语义](../concepts/API适配器与模型输入语义.md)。

## 更新与移除

**文档规定的行为**：新发现产生 `Additional instructions from`；改变产生 `Updated instructions from` 及新正文；移除产生 `Instructions removed` 并说明旧规则不再适用。刷新以追加消息实现，未改变内容避免重复注入。[消息模板与历史影响](https://github.com/deepseek-ai/deepseek-harness/blob/fcc0ad462172522aaf5c93a7b2e01f6b9f0b0159/packages/context/agent-instructions/README.zh.md#L164-L212)。

需要区分：替换 inbox 中尚未进入历史的消息，与追加“旧规则被替代”的历史消息，不是同一个操作。旧事件仍可留在日志中；有效历史未来可能经过压缩，不代表原始指令文本永久进入每次请求。

## 未验证的部分

没有验证服务端模板、实际缓存命中、模型是否服从更新指令、所有并发／取消路径或所有 provider 的映射。本次只说明读到的实现与文档，不提供效果或安全保证。下一步见 [学习问题](../explorations/Harness下一步学习问题.md)。

返回 [知识导航](../知识导航.md)；概念层见 [工作区指令](../concepts/工作区指令与上下文注入.md)。
