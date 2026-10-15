---
class: norm
scope: universal
---

# Function Clarity

## 核心规则

写函数和注释时，关注两件事；表达形式按代码复杂度和项目约定选择：

1. **结构可读**：读者能看清函数的职责、主要分支和数据流。命名、控制流、拆分和概览注释都是可选手段，行数不单独决定采用哪一种。
2. **理由可用**：注释保留理解当前行为所需的设计理由、前提和契约；单纯的实施日期、提交或阶段编号通常留给版本历史。

跟 `constraints.md` "Edit Scope Discipline" 关系：那条防 drive-by 改邻近代码；本条管**正在写**的代码本身的 readability。两条互补。

## Rule 1: 流程化结构

### 何时适用

| 可读性信号 | 可选处理 |
|---|---|
| 函数较长，读者难以看清主要职责和分支 | 改善命名或控制流；概览能减少理解成本时再补概览 |
| 多阶段处理的边界不明显，步骤顺序对行为有意义 | 用有意义的函数名、分段说明或项目已有的步骤编号表达 |
| 一段处理混合独立职责、依赖过多或难以单独验证 | 评估按职责拆分，避免把连贯逻辑切成需要来回跳转的小函数 |

行数只能帮助定位值得查看的代码。此前使用过的 50 / 80 行不是必须加注释或拆函数的阈值；项目有明确约定时按其范围执行，不能把数字本身当作可读性缺陷。

### 流程概览（按需）

函数承担多个不易从签名和代码看出的阶段时，概览可以帮助读者先理解整体。简单函数无需复述实现。下面的块注释只是示例；Doxygen、普通注释或项目已有格式都可以，不要求统一换成某种格式。

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

**需要结合上下文判断的例子**：
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
如果这些分支之间还有隐藏的顺序或状态依赖，仅给局部动作起名不足以解释流程，可以补充整体理由或调整结构。若控制流本来清晰，没有顶部概览并不构成缺陷。

### Numbered Step Marker

长流程确实需要按步骤定位时，可以使用 `// 步骤 N: <概述>` 或项目已有格式。编号不是每段必填项；有意义的子函数名或简短分段说明也能表达阶段。

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

采用编号和概览时，让二者准确描述实际流程；增删步骤后检查相关说明。不要为了维持两份逐项对照的清单而增加重复注释；概览可以只说明关键阶段。

### 长步骤拆 sub-function

当一段处理有独立职责、稳定输入输出，且拆出后更容易理解或验证时，可以提取子函数。若拆分产生大量参数、隐藏共享状态或迫使读者频繁跳转，保留连续实现可能更清楚。

先查看已有实现能否复用，再判断局部函数、私有方法或独立模块哪种边界合适。相似代码出现两次只是调查线索；只有它们表达同一职责、预计需要一起变化时，提取公共 helper 才有意义。不为达到行数或重复次数指标引入抽象。

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

仅描述实施历史的注释不止「milestone 标签」一种形态，**依赖实现期临时文档**也会产生同样的问题。代码附近应写清理解当前行为所需的理由、前提和契约；长篇推导可以引用稳定来源，不必复制进每处注释。判断依据是引用目标是否长期可用，而不是「内部 vs 外部」：

| 目标 | 例子 | 处理 |
|---|---|---|
| 临时材料（会清理或失去含义） | 准备删除的实施计划、仅在某次任务内有意义的 milestone/Task/Phase 标签、只描述旧实现的说明 | 提取仍有效的理由，再删除或替换失效引用；不能仅凭文件名含 `plan` 就删除 |
| 稳定材料（长期维护） | 论文、规范章节、保留维护的架构文档、框架源码 | 可作为深入阅读来源；附近说明当前代码依赖的关键事实 |

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
| 只按行数要求概览、编号或拆分 | 形式增加了，实际理解成本可能更高 | 先指出职责、控制流或状态方面的具体问题 |
| 概览和逐段注释反复复述清晰代码 | 两份说明增加同步成本，却没有补充理由 | 保留有助于理解的部分，优先用清晰命名表达动作 |
| 仅因相似代码出现两次就抽 helper | 表面相似不等于需要共同变化 | 判断职责、依赖和未来修改边界 |
| 一段逻辑混合多个独立职责却只加编号 | 编号没有解决耦合和理解困难 | 评估按职责拆分及其参数、共享状态成本 |
| 概览跟实现漂移 | 读者据此形成错误理解 | 更新或删去过期说明，保留仍有效的理由 |
| `// M11 fix` 不写 why | 半年后失意义 | 改成 stable why |
| `// 2026-05-12 加的` | 加日期没意义，git blame 已有 | 删 / 改 stable why |
| `// 原来是 X，改 Y` 不说为什么 | 等于没注释 | `// Y 而非 X：<理由>` |
| `// TODO` 没有说明问题或移除条件 | 读者无法判断何时处理 | 补充具体问题和条件；关联编号沿用项目约定 |

## 项目 Tuning

项目已有明确约定时沿用。需要建立新约定时，以实际阅读和维护问题为依据，不为应用本文件额外建立配置：

| 项 | 默认判断 | 项目可选表达 |
|---|---|---|
| 流程概览 | 仅在签名和实现难以表达整体流程时补充 | 普通注释、项目既有文档格式或 Doxygen |
| 子函数拆分 | 看职责、依赖、控制流和验证边界 | 私有方法、局部函数或确有独立职责的模块 |
| 步骤定位 | 不要求编号 | `// 步骤 N: ...`、分段说明或有意义的函数名 |
| 注释语言 | 沿用项目工作语言和既有风格 | 中文、英文或其他 |

## When This Applies

- **编码时**：针对正在修改的函数和注释应用上述判断，不顺手清理无关代码。
- **审查时**：按用户要求或实际可读性问题检查相关范围。项目审查工具或技能只是可选辅助；本文件不要求安装、自动调用或串联其他技能。

## 项目实例参考

DialogueSystem (UE 5.5 plugin) 项目 2026-05-13 把 `FDialogueImportPipeline::Apply` (245 行) 拆成 main Apply (47 行) + `ApplyEntryToDA` (163 行) + `ApplyDBWrites` (45 行) + `MaybeAutoDeriveStringTables` (15 行)。原 245 行版本里堆了大量 transient when 注释（"M11 (2026-05-12) ..." / "I-034 修复 ..."），缺 leading 流程概览。

这个案例说明按入口处理、数据库写入和字符串表派生等职责拆分的做法；它不证明相同行数的函数都应该拆，也不要求其他项目复制其概览或注释格式。

## 相关 Guidelines

- [改动约束](constraints.md)的 "Edit Scope Discipline" —— 可读性建议不授权修改无关代码。
- [先查复用](reuse-before-implementing.md) —— 拆分或新增抽象前查看已有实现；复用判断看职责和修改边界，不靠重复次数决定。
- [澄清边界](clarify-before-implementing.md) —— 只有影响结果且现有授权无法解决的决定才需澄清；函数整理不自动启动规划审批。
- [行文规范](../writing/prose-and-register.md) —— 注释语言、术语和数量表达。
