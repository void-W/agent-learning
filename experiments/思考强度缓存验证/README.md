# 思考强度缓存验证脚本

用官方 DeepSeek Messages API 做受控实验：**所有请求使用完全相同的 system prompt 和 user message，只改变 `thinking` 与 `output_config.effort`**，然后比较返回中的缓存命中 tokens。回答文本不是主要指标；`usage` 才是。

## 为什么不用聊天界面

聊天界面里很难保证“只改 effort、其他输入完全不变”。脚本固定了长前缀、模型、输出上限和请求顺序，并且每次请求的 system prompt 都相同（同一 run 内），因此可以把缓存变化归因于 effort。界面统计适合快速观察；脚本适合留下可重复的原始数据。

## 准备

在工作区根目录的 `.env` 中填写密钥；工作区根目录提供了 `.env.example` 模板：

```sh
# /Users/wujianchang/harness/.env
DEEPSEEK_API_KEY=<your-key>
DEEPSEEK_BASE_URL=https://api.deepseek.com/anthropic
```

脚本会从自身位置向上查找最近的 `.env`，默认就是工作区根目录；也可以用 `--env-file` 指定其他文件。**已存在的环境变量优先**，不会被 `.env` 覆盖。不要把 `.env` 提交到 Git，也不要在日志或结果中打印真实值。

脚本使用 Python 3.9+ 标准库，不需要安装依赖。默认端点是 `https://api.deepseek.com/anthropic/v1/messages`，模型是 `deepseek-flash`。

## 先干跑

```sh
python3 verify_effort_cache.py --dry-run
```

干跑只打印端点、模型、请求顺序和 prompt 长度，不发网络请求，也不需要密钥。

## 正式运行

```sh
python3 verify_effort_cache.py \
  --model deepseek-flash \
  --sequence high,high,low,low,high \
  --delay 5
```

默认 5 次请求：

1. `high`：暖场，建立缓存前缀；
2. `high`：同 effort 对照，应该命中；
3. `low`：只切 effort，观察是否接近冷启动；
4. `low`：确认切换后的稳定状态；
5. `high`：切回原 effort，观察是否恢复命中。

每次请求间隔 5 秒，给服务端留出缓存落盘时间。默认 system prompt 约 12,000 字符，输出上限 256 tokens；可以用 `--prompt-chars`、`--max-tokens`、`--sequence` 调整。

**费用提示**：每次请求都会计费；5 次请求的输入规模约 5 × 数千 tokens，输出很短。先用干跑确认，再决定是否增加重复次数或换成更长的序列。

## 输出

终端表格包含：

| 列 | 含义 |
| --- | --- |
| `input` | 未缓存输入 tokens（`usage.input_tokens`） |
| `cache_read` | 缓存命中 tokens（`usage.cache_read_input_tokens`） |
| `cache_create` | 缓存写入 tokens（当前文档称通常为 0） |
| `output` | 输出 tokens |
| `total_in` | 三项输入之和 |
| `hit_rate` | `cache_read / total_in` |

同时会在 `results/` 下写一份 JSON，包含配置、prompt 的 SHA-256、每次请求的 usage、响应 id、`stop_reason` 和文本预览。JSON 不包含 API key；仍建议提交前检查一遍。

## 怎么读结果

- **`high → high` 同 effort 对照命中很低**：先别下结论。可能是缓存尚未落盘、上下文太短、请求间隔太久或前缀被其他因素改变；增大 `--delay`／`--prompt-chars` 后重试。
- **`high → low` 命中接近 0，且输入规模相近**：支持“effort 被写进 prompt 开头、前缀失效”的模板结论。
- **`high → low` 仍保持高命中**：说明托管 API 没有把 effort 写进缓存前缀，或缓存键与服务端 prompt 构造和公开模板不同。
- **`high → low` 部分下降**：记录具体 tokens；不要把部分命中简化成“命中／不命中”。
- **切回 `high` 后恢复命中**：进一步支持前缀差异，而不是账号级缓存被整体清空。

单次 run 只能说明这个模型、这个端点、这个时间窗口的行为。缓存是 best-effort，还会受淘汰、请求间隔和服务端版本影响。

## 与 DSH 路径的关系

脚本直接请求官方 Messages API，验证的是**提供方模型行为**，不是 DSH 适配器内部的请求组装。若要与 DSH 的实际会话对照，可以同时读取 DSH“统计”页签中切换前后的每步缓存命中，两者应方向一致；不一致时优先检查 DSH 是否同时改变了 system prompt、工具或历史。

## 数据归档

一次 run 的 JSON 可以作为原始实验数据保存在 `results/`。如果要写进 Wiki，先保留文件并记录 run 时间、模型、序列和结论；不要把未执行的计划写成已完成。背景和判定标准见 [思考强度切换缓存实验](../../wiki/explorations/思考强度切换缓存实验.md)。

## 实测结果（2026-11-08）

`deepseek-flash`、官方 Messages 端点、12,000 字符前缀、序列 `high,high,low,low,high`：

| # | effort | input | cache_read | 命中率 |
| --- | --- | --- | --- | --- |
| 0 | high（暖场） | 1989 | 0 | 0.00% |
| 1 | high（对照） | 197 | 1792 | 90.10% |
| 2 | low（切换） | 1989 | 0 | 0.00% |
| 3 | low（稳定） | 197 | 1792 | 90.10% |
| 4 | high（回切） | 197 | 1792 | 90.10% |

结果支持“effort 进入缓存前缀”；不同 effort 的前缀缓存可以并存。原始记录见 [JSON](results/effort-cache-20261108-011514.json)。另有一次单请求冷启动记录 [single-warmup.json](results/effort-cache-20261108-011432-single-warmup.json)，不计入上述对照序列。

## 参考

- [DeepSeek：使用 Anthropic API](https://api-docs.deepseek.com/zh-cn/guides/anthropic_api)：端点、请求字段和 `usage` 字段。
- [DeepSeek：上下文硬盘缓存](https://api-docs.deepseek.com/zh-cn/guides/kv_cache/)：缓存前缀单元与命中规则。
