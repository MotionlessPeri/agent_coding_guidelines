# Fact-Forcing Gate

## 核心思路

让 agent 编辑代码 / 跑 destructive 命令前，**强制 surface 具体可验证的事实**——不是 self-evaluation（"are you sure?"），而是**动作前要求列出 concrete claims**：

| 即将做的动作 | 强制 surface 的事实 |
|---|---|
| 第一次 Edit / MultiEdit 某文件 | 1. grep 列所有 import / require 这文件的位置<br>2. 列受影响的 public function / class<br>3. 引用 user 当前指令原话 |
| 第一次 Write 新文件 | 1. 列哪些文件会 call 这个新文件<br>2. confirm 没有现有文件做同样事（用 Glob）<br>3. 引用 user 当前指令原话 |
| Destructive Bash（`rm -rf` / `git reset --hard` / `git push --force` / `drop table` / etc.） | 1. 列会影响的文件 / 数据<br>2. 写一行 rollback 步骤<br>3. 引用 user 指令原话 |
| 普通 Bash（每 session 第一次） | 1. 当前 user 请求一句话<br>2. 这条命令验证 / 产出什么 |

Self-evaluation 不 work——问 agent "你违反了 policy 吗"，答永远是 "没有"。但要求 "**列**每个 import 这文件的地方"——agent 必须真跑 Grep / Read，**动作本身**改变了输出质量。

## 跟现有 declarative guideline 的关系

本 repo 已经有两条 prep-work declarative rule：

- [`guidelines/code/clarify-before-implementing.md`](../guidelines/code/clarify-before-implementing.md) —— 开工前澄清需求
- [`guidelines/code/reuse-before-implementing.md`](../guidelines/code/reuse-before-implementing.md) —— 开工前 survey 现有实现

两条都是 **declarative**："开工前应当先 X"。Agent 读到 prompt 时通常会照做，但**当任务感觉 trivial / 时间压力大 / 上下文塞满**时，rule 容易被忽略。

Fact-forcing gate 是**同一思路的 enforcement 版本**——不靠 agent 自律，靠"动作前必须 surface 事实"的硬约束。两套互补：declarative 解释"为什么要做"，gate 强制"必须做"。

## 实施层级（按 enforcement 强度排）

### 层级 1: Prompt-level（最轻，立刻可用）

在 AGENTS.md / skill body 里直接写"动作前必须 surface 下列事实"清单。靠 agent 读 prompt 自律遵守。

**适合**：多数场景。Agent 读 prompt 一致性高时，prompt 级约定足够。本 repo 当前默认就走这条路径（clarify + reuse 两条 declarative rule）。

### 层级 2: Skill-level（中等）

写一个 `fact-forcing-gate` skill：

- description 里 trigger 在"about to do non-trivial Edit/Write/destructive-Bash"
- body 给出具体 fact 清单 + 强调 "skill 没跑完不要 Edit"
- skill 跑完后 agent 已 surface fact，再 proceed

**适合**：跨项目都希望保留这个 discipline，但不想到 hook 那么硬；尤其在 supervised-workflow 实施阶段自动 compose。

### 层级 3: Hook-level（最硬）

PreToolUse hook 拦截 Edit / Write / Bash：

- 检查"这是 first Edit 这文件吗"（per-session state 存 `~/.claude/<project-encoded>/fact-gate/edited-files.json`）
- 是 → 输出 deny 决定 + 把"该 surface 的 fact 清单"写进 `permissionDecisionReason`
- 否 → 放行

Agent 看到 deny + 提示后必须先跑 Grep / Read / etc.，再重试 Edit。

**适合**：跨项目自动保持 discipline，且承担 hook 维护成本。

⚠️ **装 hook 必读约束**（见 [`guidelines/claude-code/hook-conventions.md`](../guidelines/claude-code/hook-conventions.md)）：

- **Trap 1**：user-level skill 必须 install-time bake 绝对路径，不能依赖 `%USERPROFILE%` 字面字符串
- **Trap 2**：handler 必须 try-except + return 0 兜底；任何启动失败 / import error → exit 2 → PreToolUse 把自己锁死（Edit / Write / Bash 全 block，无法从 agent 内部修复，只能从 `~/.claude/settings.json.bak.*` 手动恢复）
- **Trap 3**：PreToolUse 用 `hookSpecificOutput.permissionDecision: "deny"`，不要用顶层 `decision: "block"`（后者只对 UserPromptSubmit / Stop 生效）

### 跨层级组合

最常见组合：

- **prompt 层** baseline——AGENTS.md / global skill 写 declarative 约定
- **skill 层** 兜底——非 trivial task 启动 supervised-workflow 自动 compose
- **hook 层 opt-in**——对特别讲究 quality 的项目装；普通项目不装

### advisory vs hard：三层都还是 advisory

用 MFIC 的 control 强度框架看，上面三层有个容易忽略的共性：**都是 advisory（agent 能绕过），没有一层是 hard（能力被真正拿走）**。

- 层级 1 / 2（prompt / skill）——靠 agent 读 prompt 自律，最弱。
- 层级 3（hook）——真拦得住"赶工者做显而易见的事"（这是现实威胁，价值很大），但控制方仍能绕过：换个工具、把 hook 关掉、改 settings.json。所以它是"合理保证"级的 advisory，不是 hard。

真正的 **hard control** 是把能力拿走：一个独立 approver 用 agent 没有的私钥签名精确 artifact（commit 的 tree-hash / 命令+参数+`approved_at` 时间戳），agent 改不了的 verifier（protected remote / 隔离 CI runner）只认匹配且未过期的签名——agent 伪造不出签名、不能把批准挪到别的 artifact、不能自批。这**超出 fact-forcing gate 的范畴**（gate 是"逼你 surface 事实"，不是"没签名不让落地"），但值得知道天花板在哪：fact-forcing gate 最多做到 advisory，够用即止；真要 hard 得上"独立签名 + agent 改不了的 verifier"这类方案（本 repo 目前没有现成实施，最接近的一层 engine-side 硬约束是 [`claude-code-autonomous-permissions.md`](claude-code-autonomous-permissions.md) 讲的 auto-mode 破坏性命令护栏）。

> advisory / hard 的框架来自 pmarreck 的 [MFIC — Mechanically-Falsifiable Independent Control](https://gist.github.com/pmarreck/b30aa3ca69cb70a5526f8a63ab8c8d7e)：advisory = 能绕过，hard = 能力被拿走。

## 何时 trigger gate

不是每个 Edit 都拦——差异化触发：

| 触发 | 是否拦 |
|---|---|
| 文件首次 Edit | ✅ 拦（拿一次事实清单） |
| 同一文件后续 Edit | ❌ 不拦（事实已 surface） |
| 文件首次 Write（新建） | ✅ 拦 |
| Destructive Bash | ✅ 每次都拦 |
| 普通 Bash | ✅ session 第一次拦，后续不拦 |
| Read / Glob / Grep | ❌ 不拦（read-only） |

Per-session state 在 user-level hook 自己存（不要塞进 `~/.claude/projects/<encoded>/`，那个目录的编码规则 Claude Code 可能改）。

## 证据 strength

ECC GateGuard skill 引用了两次 A/B 测试（同 agent 同任务，gated vs ungated）：

| 任务 | Gated | Ungated | Gap |
|---|---|---|---|
| Analytics module | 8.0 / 10 | 6.5 / 10 | +1.5 |
| Webhook validator | 10.0 / 10 | 7.0 / 10 | +3.0 |
| 平均 | 9.0 | 6.75 | **+2.25** |

两组 agent 都"代码跑得通 + 测试 pass"——差别在**设计深度**。Gated agent 因为 forced 看了 importer 上下文，做的决策更贴现有架构。

⚠️ ECC 单方面 A/B 数据 + 方法学未公开，**不当 ground truth**。但作为"为什么这个 pattern 有理论支撑"的 supporting evidence 可以参考。落地到自己项目时**自己测一次**——挑两个有重叠 importer 的真实任务，gated / ungated 各跑一次，对比设计深度。

## Anti-Patterns

| 反 pattern | 为什么错 |
|---|---|
| Self-evaluation："are you sure about this edit?" | LLM 永远 say "yes / no problem"，零信息量 |
| "你考虑了所有 caller 了吗？" 然后等 agent yes/no | Agent 答 yes 不代表真考虑了。要 force "**列出**所有 caller"，agent 才会真 grep |
| Gate 文本写"check before editing" 抽象命令 | 没有具体 fact 清单 = agent 没 forced action，等同于 self-evaluation |
| 每次 Edit 都拦（不区分 first vs repeat） | Noise > signal，agent 烦了开始走 around，用户也烦 |
| 把"fact 清单"放在 prompt 顶部期望 agent 一直记得 | 上下文长时容易漏；hook 在**动作发生那一刻**注入更稳 |
| 装 hook 但 handler 没 try-except → 一次 broken hook 把整个对话 Edit/Write/Bash 全锁死 | 见 hook-conventions.md trap 2 的 self-deadlock 真实案例 |

## 项目侧用法建议

**对本 repo（agent_coding_guidelines）**：

- prompt 层已经有 [`clarify-before-implementing`](../guidelines/code/clarify-before-implementing.md) + [`reuse-before-implementing`](../guidelines/code/reuse-before-implementing.md) declarative
- 不立刻装 hook 层。本 technique 主要作**未来可选 enforcement 路径的参考**
- 如果观察到 declarative guideline 被反复忽略 → 考虑 promote 到 skill 层
- skill 层不够再考虑 hook 层

**对新接入项目**：

1. 先走 prompt 层（让本 repo 的 AGENTS.md 通过 `@`-import 自然带入两条 declarative）
2. 观察 ~6 周。如果 agent 经常 skip survey 直接 Edit → 升级到 skill 层
3. 再观察。如果 skill 也被绕过 → 装 hook 层（接受维护成本 + 严格遵守 hook-conventions.md）

## 相关 Guidelines / Techniques

- [`guidelines/code/clarify-before-implementing.md`](../guidelines/code/clarify-before-implementing.md) —— Declarative 形态的"开工前澄清"
- [`guidelines/code/reuse-before-implementing.md`](../guidelines/code/reuse-before-implementing.md) —— Declarative 形态的"开工前 survey 现有实现"
- [`guidelines/claude-code/hook-conventions.md`](../guidelines/claude-code/hook-conventions.md) —— 装 hook 层 enforcement **必读**（self-deadlock / permissionDecision 字段 / path baking）
- [`techniques/adversarial-verification.md`](adversarial-verification.md) —— 完成后 adversarial 验证 + 开工前 fact-force = 双向 quality discipline
- ECC `gateguard` skill（[github](https://github.com/affaan-m/ECC/tree/master/skills/gateguard)）—— 本 technique 的灵感来源 + hook-level 实施参考
