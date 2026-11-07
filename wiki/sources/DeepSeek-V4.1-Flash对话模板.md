# DeepSeek-V4.1-Flash 对话模板

- 类型：源码模板来源
- 创建／更新：2026-11-08（Asia/Shanghai）
- 证据范围：固定 commit 的 `chat_template.jinja` 原文；2026-11-08 在 `deepseek-flash` 官方 Messages API 上完成一次相关实测，但模板仍不是托管 API 的逐字保证

## 来源记录

- 模型仓库：[deepseek-ai/DeepSeek-V4.1-Flash](https://huggingface.co/deepseek-ai/DeepSeek-V4.1-Flash)。
- 固定 commit：[`2cba9e42aa026125f3ed06c6d98c1db82f7ca027`](https://huggingface.co/deepseek-ai/DeepSeek-V4.1-Flash/commit/2cba9e42aa026125f3ed06c6d98c1db82f7ca027)（提交标题：Adding chat template）。
- 文件：[chat_template.jinja（固定修订原文）](https://huggingface.co/deepseek-ai/DeepSeek-V4.1-Flash/raw/2cba9e42aa026125f3ed06c6d98c1db82f7ca027/chat_template.jinja)。
- 本地快照：[DeepSeek-V4.1-Flash-chat_template-2cba9e4.jinja](../../raw/templates/DeepSeek-V4.1-Flash-chat_template-2cba9e4.jinja)。
- 快照 SHA-256：`d959d804d5101b79a49b6ff1bf3c54cd5affa9a5a78c503d925f3090040b31c3`。
- 获取日期：2026-11-08；保留下载字节，未翻译或改写。

## 已核实内容

**模板事实**：模板在消息序列的第一个元素处，先输出 `<｜begin▁of▁sentence｜>`；随后在 thinking 模式下输出 `<｜System｜>`，再输出一段普通文本形式的强度声明，然后才输出 system 正文：

```text
<｜begin▁of▁sentence｜><｜System｜>Reasoning Effort: 75 (range 1-100, the higher the value, the more thorough the reasoning)

<system 正文>
```

**模板事实**：字符串强度映射为 `low=50`、`medium=62`、`high=75`、`max=100`，也接受 1–100 的整数。对应模板片段：

```jinja
{%- if idx == 0 -%}
    {%- if thinking or m.role == "system" -%}{{- "<｜System｜>" -}}{%- endif -%}
    {%- if thinking -%}{{- "Reasoning Effort: " ~ budget ~ " (range 1-100, the higher the value, the more thorough the reasoning)\n\n" -}}{%- endif -%}
{%- endif -%}
```

**模板事实**：`thinking_mode == "chat"`（关闭思考）时不输出这行强度声明；生成提示的 `<think>`／`</think>` 也随模式变化。开启 thinking 时，历史 assistant 的 reasoning 内容按模板条件渲染。

## 对缓存的影响

**推断**：切换思考强度会改变模型输入开头的文本。按 DeepSeek [上下文硬盘缓存](https://api-docs.deepseek.com/zh-cn/guides/kv_cache/)的完整前缀单元匹配规则，第一个不同 token 之后的缓存单元不能完整匹配。`low`／`high`／`max` 之间切换时，历史 reasoning 仍然保留，但开头数字变化；切 `off` 时整行消失。缓存影响接近一次冷启动，而不是末尾少量未命中。

**实测支持（2026-11-08，`deepseek-flash` 官方 Messages API）**：固定 12,000 字符前缀，`high → high` 命中 90.10%，`high → low` 命中 0.00%，`low → low` 命中 90.10%，`low → high` 回切命中 90.10%。见 [实验记录](../explorations/思考强度切换缓存实验.md)。这支持模板推断，但仍只覆盖一个模型和端点。

**推断的边界**：模板层是普通文本，不是独立的 effort 特殊 token；实际分词由 tokenizer 决定。即使开头只差几个 token，只要缓存单元覆盖到该位置，该单元就不能完整匹配。

## 适用范围与限制

- 这是开放权重模型的公开模板，**不是托管 API 的逐字保证**。托管服务可能使用同一模板，也可能有自己的 prompt 构造。
- 已测量一次托管 API 的缓存命中，但仍未抓取最终请求 token 序列；“effort 在前缀中的具体位置”来自公开模板，托管服务可能不同。
- 模板可能随仓库更新；本页以固定 commit 为准，更新版本需另存快照。
- 不把该模板结论直接推广到其他模型、其他提供方或其他协议。

## 验证入口

2026-11-08 已完成一次受控运行：固定前缀、只切 effort，`high → low` 命中率从 90.10% 降到 0.00%，回切 `high` 恢复 90.10%。方法、原始 JSON 和复现命令见 [思考强度切换缓存实验](../explorations/思考强度切换缓存实验.md)。

返回 [知识导航](../知识导航.md)；相关概念见 [API 适配器与模型输入语义](../concepts/API适配器与模型输入语义.md)。
