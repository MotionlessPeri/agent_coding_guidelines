# Function Clarity

## 核心规则

两条函数级 clarity 规则，**始终在线的 baseline coding discipline**——每次写函数 / 加注释当下就该应用，不是 audit 时才应用：

1. **流程化结构**：函数实施应当**反映自身的流程**——超阈值的函数顶部有 leading 流程概览注释、每个步骤段加 numbered marker、单步骤超长就拆 sub-function
2. **注释 stability**：注释写 **"stable why"**（为什么这样设计），不写 **"transient when"**（什么时候加 / 哪个 commit 修 / 哪个 milestone 引入）

跟 `constraints.md` "Edit Scope Discipline" 关系：那条防 drive-by 改邻近代码；本条管**正在写**的代码本身的 readability。两条互补。

## Rule 1: 流程化结构

### 何时适用

| 信号 | 必做 |
|---|---|
| 函数 > **~50 行** | 函数顶部 doc comment 加 leading "流程：1./2./.../N." 概览 |
| 函数能识别出多步骤流程（不论行数） | 每步骤段加 `// 步骤 N: ...` 锚点 marker |
| 单步骤段 > **~80 行** | 拆 sub-function（按 `code-size-audit` skill Split Form 决策表选形态 a/b/c）|

阈值（50 / 80）是**软警觉线**——判断 readability，不机械化套数字。具体项目可调（在项目 AGENTS.md 或 dev-guide.md 写明）。本 guideline 提供 starting point。

### Leading 流程概览（必填）

让 6 个月后的 dev 读 30 秒就懂结构。

**正例**：
```cpp
/**
 * 处理 Report 的单个 Entry：刷 binding / 解析 DA / 跑 Pass / post-processing。
 *
 * 流程：
 *   1. NoChange 桶：只刷 binding，不进 DialogueIDsToReplace
 *   2. 按 bucket 解析 DA：New 走 CreateNewDialogueAsset；Modified TryLoad；
 *      Conflict 看 resolution mode（Skip / OpenDAToFix / UseNew）
 *   3. 跑 Pass A-D 或 RebuildDAFromScratch
 *   4. graph → runtime full-flush 编译
 *   5. post-processing：Beautify（仅 New/UseNew）/ bReviewed reset / WriteBound / MarkDirty
 *   6. 登记 DialogueID 到 InOutDialogueIDsToReplace
 *
 * 返回：true = continue 下一 Entry；false = fatal（OutError 非空）
 */
static bool ApplyEntryToDA(...);
```

**反例**（散落注释，无 leading）：
```cpp
static bool ApplyEntryToDA(...)
{
    // NoChange handling
    if (...) { ... return true; }
    // 跑 Pass A-D
    ...
    // 写 binding
    ...
}
```
读者每次重读都要从头 piece together，零复用价值。

### Numbered Step Marker

函数体每段加 `// 步骤 N: <概述>`（或项目约定的同等格式），对应 leading 概览的步骤号。grep `// 步骤 3:` 可直接跳转。

```cpp
static bool ApplyEntryToDA(...)
{
    // 步骤 1: NoChange 桶 —— 只刷 binding 不登记
    if (Entry.Bucket == NoChange) { ... return true; }

    // 步骤 2: 按 bucket 解析 DA
    UDialogueAsset* DA = nullptr;
    if (Entry.Bucket == New)           { ... }
    else if (Entry.Bucket == Modified) { ... }
    else if (Entry.Bucket == Conflict) { ... }

    // 步骤 3: 跑 Pass A-D 或 RebuildDAFromScratch
    ...
}
```

**关键 invariant**：leading 概览的步骤数 = 函数体 numbered marker 数。增删步骤**同步改两处**。docs 漂移比没 docs 更糟。

### 长步骤拆 sub-function

某 numbered step 段超 ~80 行 → 拆 sub-function，主函数收缩成调度。否则 leading 概览说"5 步"但实际单步骤几百行，概览失去意义。

拆函数选形态时按 `code-size-audit` skill 的 Split Form 决策表（a/b/c）；不在本 guideline 重复。

## Rule 2: 注释 Stability

### Stable Why vs Transient When

| 维度 | Stable why | Transient when |
|---|---|---|
| 写什么 | 为什么这样设计 / 这样防什么 | 什么时候加 / 哪个 commit / 哪个 milestone |
| 半年后 | 仍成立 | 失意义（M11 / I-034 没人记得）|
| 服务谁 | **每天读代码**的 common case | 少数 dev 想反查历史的 edge case |
| 反查途径 | 不需要 | `git blame` / `git log -L :func:file` 已经够 |

### 反 Pattern 对照表

| Transient when（反 pattern）| Stable why（正例）|
|---|---|
| `// M11 (2026-05-12): NormalizeXlsxPathForStorage 把绝对路径转相对项目根` | `// 跨机一致：存储相对项目根路径，不同 dev/CI workspace 也一致` |
| `// I-034 修复（2026-05-12）：Speakers.Num() > 0 也触发 DB 写` | `// Speakers-only xlsx 也走 DB 写：只 import speaker sheet 是合法场景` |
| `// 2026-05-12 fix: NoChange entries 仍要刷 BoundXlsxPaths` | `// NoChange 也刷 binding：内容没变 ≠ binding 元数据没变` |
| `// 加于 sprint 23 / commit abc1234` | （删，反查靠 git blame）|
| `// 之前是 X，现在改成 Y` | `// Y 而非 X：<具体设计理由>` 或只留 Y 的设计描述 |
| `// 任务 X 要求加这个分支` | `// <分支处理的具体业务场景>` |

### 反查 history 怎么办

需要"why + 改造历史"双信息时：
- **多数情况**：只留 stable why。改造历史靠 `git blame` / `git log -L :functionname:file`
- **极少情况**：反查特别频繁（架构核心 + 历史复杂），可以用结构化 pointer：`// Reason: <stable why>. History: see git blame for <commit-prefix>` —— **commit prefix 比 M11 / I-034 这种本地命名更稳定**

### 注释自包含：不引用 ephemeral 文档

transient when 不止「milestone 标签」一种形态——**引用实现期临时文档**是同源的另一种。注释解释设计意图
（stable why）必须 **inline、不依赖任何外部文档即可读懂**。判据是**引用目标 durable 还是 ephemeral**，
不是「内部 vs 外部」：

| 目标 | 例子 | 处理 |
|---|---|---|
| Ephemeral（会消失 / 失意义） | 实现期 plan / impl-plan 文档（写完即抛 / cleanup commit 删）、milestone/Task/Phase 标签、`见 design §2.1`、`旧 X 已废 / 改自 Y` | ❌ 剥——指向消失的文档 = 悬空引用，比没注释更糟 |
| Durable（长期在） | 论文 / 规范章节、**committed** 架构文档、框架源码 | 🟡 可留作**可选深入指针**，不作理解前提 |

清理旧引用时**先把它承载的 why 浓缩成一句 inline，再删引用**——最常见的错是把噪音和理由一起删了。

```cpp
// ❌ 依赖 ephemeral 文档：// 设计见 docs/plans/2026-06-05-foo-design.md §2.1
// ✅ why 内联自包含：    // 持久权威 = 节点标准 attr（透明/可序列化/可连接，不用自定义 data 类型）
```

### 例外（可容忍 transient when）

下列情况 stable why 难写，留 transient when 可接受：

| 场景 | 形式 |
|---|---|
| 临时 workaround 等 upstream fix | `// TODO: workaround for X bug, remove when fixed`（带 TODO 锚点便于 grep）|
| 引用稳定 issue tracker（半年后 URL 还在） | `// See https://issues.foo.com/PROJ-123`（**不是** `// PROJ-123` 这种本地缩写）|
| Engine bug / vendor bug 引用版本 | `// UE 5.5 bug: <symptom>`（指明影响版本，告知未来读者可能哪天能 simplify）|

## Anti-Patterns 汇总

| 反 pattern | Why 错 | 修法 |
|---|---|---|
| 函数 200 行无 leading 概览 | 读者重读都要 piece together | 加 leading 流程段 |
| 概览写了，体内无 numbered marker | grep 跳转失败 / 概览-体对不上 | 每段加 `// 步骤 N:` |
| Numbered marker 但缺概览 | 看 step 3 不知整体上下文 | 概览必填，跟 marker 配套 |
| 步骤 N 段超 80 行 | 概览失去意义，等于没流程 | 拆 sub-function（Split Form 决策表）|
| 概览跟实施漂移 | docs 漂移比没 docs 更糟 | 增删步骤**同步改两处**，否则不算 done |
| `// M11 fix` 不写 why | 半年后失意义 | 改成 stable why |
| `// 2026-05-12 加的` | 加日期没意义，git blame 已有 | 删 / 改 stable why |
| `// 原来是 X，改 Y` 不说为什么 | 等于没注释 | `// Y 而非 X：<理由>` |
| `// TODO` 不带 grep 锚点 | 找不回 | `// TODO(<grep-able-key>): ...` |

## 项目 Tuning

下列值**项目-specific**，本 guideline 给 starting point，具体值由项目 AGENTS.md / dev-guide 写明：

| 项 | Guideline starting point | 项目可调 |
|---|---|---|
| 函数 leading 概览触发线 | ~50 行 | 30 / 80 都合理 |
| 单步骤拆 sub-function 触发线 | ~80 行 | 跟 `code-size-audit` 的 helper 阈值对齐 |
| Step marker 格式 | `// 步骤 N: ...` | `// N) ...` / `// Step N: ...` 等 |
| 注释语言 | 跟项目文档语言一致 | 中文 / 英文 / 其他 |

## When This Applies

- **Coding time**：写新函数 / 加注释当下，自检本 guideline
- **Audit time**：项目可装 `code-clarity-audit` skill 跑 systematic 检查（见项目 skill）；autonomous-workflow Phase 3 末尾自动 compose

## 项目实例参考

DialogueSystem (UE 5.5 plugin) 项目 2026-05-13 把 `FDialogueImportPipeline::Apply` (245 行) 拆成 main Apply (47 行) + `ApplyEntryToDA` (163 行) + `ApplyDBWrites` (45 行) + `MaybeAutoDeriveStringTables` (15 行)。原 245 行版本里堆了大量 transient when 注释（"M11 (2026-05-12) ..." / "I-034 修复 ..."），缺 leading 流程概览。

后续按本 guideline 改造的样板：见 `Plugins/DialogueSystem/Source/DialogueSystemEditor/Private/Lines/DialogueImportPipeline.cpp` 改造 commit（待落地）。

## 相关 Guidelines

- `guidelines/code/constraints.md` "Edit Scope Discipline" —— 防 drive-by 改邻近代码；本条是正写代码本身的 readability
- `guidelines/code/reuse-before-implementing.md` —— 拆 sub-function 前先看是否复用其他地方；2 次以上才抽 helper
- `guidelines/code/clarify-before-implementing.md` —— 流程梳理本身是 prep work，应在 plan 阶段就想清楚
- 项目侧 `code-clarity-audit` skill —— audit procedure + 项目 tuning
- 项目侧 `code-size-audit` skill —— "拆 sub-function" 时用 Split Form 决策表选形态 a/b/c
