# Claude Code Subagent 的 harness hidden contracts

用 Claude Code 的 subagent（`Agent` 工具 / 声明式 `.claude/agents/`）委派活时，一组官方 API doc 没强调、但实测/读官方 sub-agents 文档才明确的约定。属 Claude-Code harness hidden contract，跟 [`hook-conventions.md`](hook-conventions.md) 是兄弟篇。**Codex 的委派机制不同——本条只适用 Claude Code。**

> 来源：官方 [Create custom subagents](https://code.claude.com/docs/en/sub-agents)。核验于 2026-07。**注意本文分两部分：`核心规则` 是跨版本稳定的契约；`版本翻转的行为` 是在特定 Claude Code 版本翻转过的——记结论也记版本，且以官方 doc 现状为准（还会再变）。**

## 核心规则（稳定契约）

1. **省略 subagent 定义的 `tools` 字段 = 继承主对话的全部工具（含 MCP），不是零工具。** 想要一个"只读"研究 subagent，必须**显式** scope：`tools: Read, Grep, Glob`——否则它默认能改文件、能调 MCP。官方 frontmatter 表原文："Inherits all tools if omitted."
2. **subagent 的 context 隔离是不对称的。** 每个 subagent 起于一个**全新、隔离**的 context window：它**看不到**你的对话历史、你已调用的 skill、Claude 已读过的文件。它的初始 context 只有 = 它自己的 system prompt + 你派活那段 delegation message + CLAUDE.md 层级 + git-status 快照 + 预加载的 skills。反向：**只有 subagent 的 final message 回到 parent**，中间每一次 tool call / 文件读 / 测试输出都留在 subagent 自己的 context 里。
   - **例外**：设了 `CLAUDE_CODE_FORK_SUBAGENT=1` 的 fork subagent **会**继承 parent 对话（"memory"指 subagent 自己配置的 memory，不是 parent 的 auto-memory）。
   - **推论**：派活的 delegation prompt 必须**自包含**——把 subagent 需要的信息全塞进去（这正是 [`../../techniques/worker-instructions.md`](../../techniques/worker-instructions.md) 讲的，本条给了机制上的"为什么"）。
3. **Workflow 子 agent 的 model 继承父会话，不指定则自动继承。** 在 workflow 脚本里调用 `agent(prompt, {model: 'sonnet'})` 时，如果当前会话不是 sonnet（如 Kimi K3），所有子 agent 会 403 失败。**子 agent 的 model 字段只应在需要明确降级/升级模型时设置，且必须确认该模型在当前会话可用。** 安全做法：不填 model，让子 agent 继承父会话。
4. **Workflow `resumeFromRunId` 的 cache 陷阱。** `resumeFromRunId` 回放已完成 agent 的缓存结果。如果首次运行因模型权限 / API 错误等原因全部失败（返回空结果或 null），resume 会回放这些空结果，下游 agent 拿到 null 继续跑，全链仍然是废的。**修复：失败后先读 `journal.jsonl` 确认结果不为空。如果全是空结果，直接清 cache 目录重跑，不要 resume。** 清 cache 的方法：`rm -rf <transcript_dir>`（由 workflow 返回的 `Transcript dir` 路径给出），然后不带 `resumeFromRunId` 重新调用 Workflow。`

## 版本翻转的行为（记结论 + 记版本，别当 timeless）

下面三条在特定 Claude Code 版本**翻转过**。它们本身是个提醒：**Claude Code 的 subagent 行为跨版本会变**（同 [`make-format-args-lvalue.md`](../cpp/make-format-args-lvalue.md) / [`ue58-upgrade-gotchas.md`](../ue/ue58-upgrade-gotchas.md) 的"跨版本契约收紧/翻转"主题）。**依赖任一条前，先对当前版本的官方 sub-agents doc 复核。**

| 行为 | 翻转点 | 现状（截至核验） | 一直不变的碎片 |
|---|---|---|---|
| **嵌套 spawn** | v2.1.172 | subagent **可以** spawn 自己的 subagent（`Agent` 工具被继承，深度上限 5）。≤v2.1.171 时不能 | `AskUserQuestion` / `EnterPlanMode` / `ScheduleWakeup` / `WaitForMcpServers` **一直**对 subagent 不可用 |
| **后台 subagent 权限** | v2.1.186 | 后台 subagent 撞到需授权的 tool call 时，**权限请求会浮到主 session** 并点名是哪个 subagent 在问。<v2.1.186 时后台 subagent **自动拒绝**任何会弹权限的调用 → 后台写可能**静默失败却返回"成功形状"输出** | subagent **一直**不能问澄清问题（无 `AskUserQuestion`） |
| **定义热加载** | file-watcher 引入后 | 改 `~/.claude/agents/` 或 `.claude/agents/` 里**已有**定义，几秒内生效、**免重启**。早期需重启 session | 仍需重启的两个窄场景：新建 agents 目录的**第一个**文件；`--disable-slash-commands` 的 session |

**历史教训（即便 v2.1.186 已修）**：后台委派"静默失败返回成功形状输出"是 [`../code/validation.md`](../code/validation.md) / [`../../techniques/adversarial-verification.md`](../../techniques/adversarial-verification.md) 那条"tests passing ≠ 正确"的 subagent 版——委派回来的"做完了"要**独立验证**，别凭它的 final message 下结论。

## Anti-Patterns

| 反 pattern | 后果 | 修法 |
|---|---|---|
| 定义 subagent 时省 `tools` 以为=零权限 | 实际继承全部工具（含改文件/MCP） | read-only 用途显式 `tools: Read, Grep, Glob` |
| 派活 prompt 写"继续上面的工作" | subagent 看不到 parent 对话 | delegation prompt 自包含 |
| 凭 subagent 的 final message 认定"做完了" | 后台写在旧版会静默假成功；且中间过程你看不到 | 独立验证产物 |
| 把版本翻转的行为当 timeless 规则记 | 三条都在特定版本翻过，会过时 | 记版本锚 + 依赖前复核官方 doc |
| 指望 subagent 里 spawn 出能问用户 / 定时唤醒的下级 | AskUserQuestion/ScheduleWakeup 对 subagent 不可用 | 这类交互留在主 session |

## 相关 Guidelines / Techniques

- [`hook-conventions.md`](hook-conventions.md) —— 兄弟篇：同属 Claude-Code harness hidden contract。
- [`../../techniques/coordination-patterns.md`](../../techniques/coordination-patterns.md) + [`../../techniques/worker-instructions.md`](../../techniques/worker-instructions.md) —— 多 agent 编排的**概念工作流**；本条是它们缺的 **Claude-Code-specific harness 契约**面（tools 继承 / context 隔离 / 版本翻转）。
- [`../code/validation.md`](../code/validation.md) / [`../../techniques/adversarial-verification.md`](../../techniques/adversarial-verification.md) —— "委派回来的成功形状输出要独立验"。
- [`autonomous-loop-scheduling.md`](autonomous-loop-scheduling.md) —— `ScheduleWakeup` 对 subagent 不可用（本条版本翻转表里的一直不变碎片）。
