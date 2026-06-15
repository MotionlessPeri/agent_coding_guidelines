---
name: conversation-walkthrough
description: 编码对话收尾时的标准 review 环节——对本对话改过的代码做一次结构化走查：(1) 结构 map（改了哪些文件、各自角色、怎么拼起来），(2) self-review 三档（🔴 重构/可读性：套 function-clarity 行数阈值，>~50 行函数加 leading 概览、单步骤 >~80 行拆 sub-function、≥2 次重复抽 helper；🟡 优化；🟢 对抗式正确性读查），(3) 注释体检（按「注释自包含」原则剥 transient、保留 stable why；关键函数用 Doxygen `/** @param @return */` 契约头，但每个 tag 必带真内容、禁空 tag/复述参数名）。配套：用一份 ephemeral tracking 文档锚定讨论主线防偏移；重构与注释清理分成不同主题各自 commit；改完 cold rebuild + 冒烟验证语义没变；跑通后可据此 promote 项目级 lesson。默认在编码对话收尾触发，除非用户明说「后面是迭代不用 review」。
when_to_use: Fires at the wrap-up of any coding conversation that produced non-trivial code changes (default-on standard closing step), UNLESS the user says upcoming work is iteration that doesn't need review. Also fires when the user asks to "review 一下这个对话改的代码 / walkthrough / 看看有没有重构点 / 整理注释". Covers: mapping what changed, self-reviewing for refactor/optimization/correctness, and humanizing comments (stripping iteration/agent-oriented noise). Pairs with guidelines/code/function-clarity.md (line thresholds + comment stability), guidelines/code/reuse-before-implementing.md (extract-on-2nd-occurrence), guidelines/workflow/commits.md (one commit = one theme). Skip for trivial/mechanical changes or when the user explicitly defers review to a later milestone.
---

# 对话代码 Walkthrough（编码收尾的标准 review 环节）

编码对话产出了**非平凡代码改动**后,收尾跑一次结构化走查。**默认开**——除非用户明说「后面是迭代,不用 review」。

> 单项目（curve_articulation_maya）验证一轮,apply-and-refine。

## 触发与范围

- **触发**:编码对话收尾;或用户说「walkthrough / review 这个对话改的代码 / 看有没有重构点 / 整理注释」。
- **范围**:**本对话改过的代码**。用 `git diff <对话起始 commit>~1 <最后 commit>` + 工作区改动圈定文件集,不漫游全仓。
- **跳过**:平凡/机械改动;或用户把 review 推迟到后面 milestone。

## 配套铁律:tracking 文档 + 分主题 commit

- **建一份 ephemeral tracking 文档**(放项目的 `docs/plans/<date>-*-walkthrough.md` 之类)当**讨论主线锚点**:范围、结构 map、发现、决策、进度 log 都进去。深入代码细节时随时拉回主线,防偏移。
  - ⚠️ 这份文档**本身 ephemeral**(review 完 cleanup),按「注释自包含」原则**不被任何代码注释引用**。
- **重构与注释清理分成不同主题、各自 commit**(`guidelines/workflow/commits.md` 一 commit 一主题):结构重构 = `refactor:`,注释清理 = `docs:`。**先提已验证的重构,再单独提注释**——结构改动和文字改动混一个 diff,review 时分不清「这行是搬过来的还是改了语义」。

## Phase 1 — 结构 map

一张表:**改了哪些文件 / 各自角色 / 本对话新增了什么**;再一两句「这些拼起来是一条什么数据流/调用链」。目标:让人(和半年后的自己)30 秒看懂这次改动的骨架。

## Phase 2 — self-review 三档

对着改动逐块过,分三档,**每条带 file:line + 决策列**(做/不做/可选),最后让用户拍重构范围:

| 档 | 找什么 | 判据(套 `guidelines/code/function-clarity.md` + `reuse-before-implementing.md`) |
|---|---|---|
| 🔴 重构/可读性 | 大函数、重复代码、缺概览 | 函数 >~50 行 → 加 leading 流程概览;单步骤 >~80 行 → 拆 sub-function;同一逻辑 **≥2 次重复** → 抽 helper(第 2 次就抽,不等第 3 次) |
| 🟡 优化 | 热路径冗余、重复昂贵调用、魔数 | 非阻塞,标出来让用户定;性能结论要 profiler/实测,不臆断 |
| 🟢 正确性 | 对抗式读查 | 主动找 bug 不是确认无 bug:边界/越界、约定(如行向量)、优先级覆盖、退化兜底 |

**拆函数的天然切法**:若一个函数按「输入→若干独立输出/分支」组织(典型:DG node 的 `compute` 按 plug 派发),**一个分支 = 一个 sub-function**,主函数收成派发 + 顶部一段「各分支算什么」概览。语义零改,只是把它本来就有的结构摊开。

## Phase 3 — 注释体检(注释自包含原则)

迭代积攒的注释常被 transient / 给-agent-看的标签污染。按下面这条清:

> **注释自包含原则**:注释解释设计意图(**stable why**)必须 **inline、不依赖任何外部文档即可读懂**。
> - **禁止引用实现期临时产物**——milestone/Task/Phase 标签、会被 cleanup 的 plan/impl-plan 文档、「旧 X 已废 / 改自 Y」历史(反查靠 `git blame`)。
> - **只允许引用 durable 目标**(论文/规范章节、committed 架构文档、框架源码),且仅作**可选深入指针**,不作理解前提。
> - **清理旧引用时**:先把它承载的 why **浓缩成一句 inline,再删引用**——别连理由一起删(最常见的错:把噪音和理由一起删了)。

判据 = **引用目标 durable 还是 ephemeral**,不是「内部 vs 外部」:

| 目标 | 例子 | 处理 |
|---|---|---|
| Ephemeral | 实现期 plan/impl-plan、Task/Phase/milestone 标签、「旧 X 已废」 | ❌ 剥(why 浓缩 inline 后删) |
| Durable | 论文 §、committed 架构文档、框架源码 | 🟡 可留作可选深入指针,不作前提 |

**保留**:解释「为什么这样设计 / 防什么」的 stable why(质量好的注释主体)。

### 关键函数用 Doxygen 风格契约头

**关键函数**(public API / 跨边界入口 / 非平凡契约——带参数、有返回语义、有前置条件的那些)的头注释用 Doxygen `/** @param @return */` 形式,把接口契约结构化:

```cpp
/**
 * <一句话职责> + <stable why / 不变式（可选）>。
 * @param splineIdx 要分裂的 spline 池索引
 * @param t         分裂参数 ∈ [0,1]
 * @return 新端点池索引；越界 → -1（no-op）
 */
int splitSpline(int splineIdx, double t);
```

铁律(防 Doxygen 最常见的噪音坑):

- **每个 tag 必须带真内容**——语义 / 空间(如「中性空间」) / 单位 / 所有权 / null/空 的含义 / 前置条件 / 取值范围。
- **空 tag 或只复述参数名**(`@param pos 位置`)= 噪音,**比不写更糟** → 没内容可写就**省掉那个 tag,或整块不套 Doxygen**。
- **不全量**:trivial getter / 签名自明的私有一行函数 / 框架样板(如 Maya `creator`/`initialize`)**不套**,否则满屏空 tag。
- **块写契约(what),stable-why 仍 inline**(块内首句或函数体),两者不重复。
- Doxygen 块放**声明处**(头文件,消费方读的地方);file-local/static helper 放定义处。

> 本 Phase 扩展 `guidelines/code/function-clarity.md` Rule 2:Rule 2 讲 milestone tag(transient when),本条加「不引用 ephemeral 文档 + 自包含」+「关键函数 Doxygen 契约头(tag 必带真内容)」两个维度。

## Phase 4 — 执行 + 验证

1. 用户拍定重构范围后动手:结构改动**保持注释原样搬**(注释清理留下一个 diff,结构/prose 分开 review)。
2. **验证语义没变**:cold rebuild(插件/native 必 cold,不 hot reload)+ 冒烟/headless 跑一遍既有 verify 脚本(`guidelines/code/validation.md` 对抗式)。重构尤其要「行为不变」实证,不能只「看代码对」。
3. 重构 commit(`refactor:`)→ 注释清理 commit(`docs:`),各自单一主题。
4. 更新 tracking 文档进度 log。
5. **promote 评估**:本轮发现的可复用 lesson 按 `guidelines/workflow/knowledge-promotion.md` 评估是否回灌 meta-corpus(两-strike / 框架 hidden contract)。

## Anti-Patterns

| 反 pattern | 后果 | 修法 |
|---|---|---|
| 不建 tracking 文档,边聊边深入 | 讨论偏移、丢主线、决策无记录 | 先建 ephemeral tracking 文档锚主线 |
| 重构 + 注释清理混一个 commit | review 分不清结构改动 vs 语义改动 | 分主题各自 commit,先重构后注释 |
| 注释清理时连 why 一起删 | 丢失设计理由 | 先浓缩 inline 再删 ephemeral 引用 |
| 重构后只「看代码对」不实测 | 隐性语义漂移 | cold rebuild + 冒烟/headless 验证 |
| self-review 只确认「没问题」 | 漏 bug | 对抗式:主动找边界/越界/退化失败 |
| tracking 文档被代码注释引用 | ephemeral 文档消失后悬空引用 | tracking 文档不进注释(自包含原则) |

## 项目实例参考

curve_articulation_maya(Maya C++ 插件)2026-06-15 对一轮「posed 编辑」实现(CurvenetNode 等 4 文件)跑本流程:
- Phase 1 结构 map:`compute()` 三分支(follow / 中性 deformer / posed 显示)。
- Phase 2:🔴 `compute()` ~140 行三分支无概览 → 按「一输出 plug 一 sub-function」拆(`computeDeformerPosed/DisplayKnots/OutPosedKnots`)+ 派发概览;🔴「GC-safe 读 pointArray」重复 4 次 → 抽 `readPointArray` helper。
- Phase 3 注释体检:剥 `Task 2.4`/`Phase 1`/`旧 editInput 已废删`/`见 design §2.1`(impl-plan 引用),把 why 浓缩 inline,保留「防 double-deform / 恒等不变式 / 行向量约定」等 stable why。
- Phase 4:cold rebuild + headless 回归(`_verify_walkthrough_refactor.py`:follow 跟姿势 101.29 / deformerPosed 反算回中性 0.0001=恒等)GREEN;`refactor:`(c64c439)+ `docs:`(bcc2570)两 commit。tracking 文档 `docs/plans/2026-06-15-posed-edit-walkthrough.md`。

## 相关 Guidelines / Skills

- `guidelines/code/function-clarity.md` — 行数阈值(Rule 1)+ 注释 stability(Rule 2);本 skill 是它的「系统化执行 + 注释自包含扩展」
- `guidelines/code/reuse-before-implementing.md` — ≥2 次重复抽 helper 的判据
- `guidelines/workflow/commits.md` — 一 commit 一主题(重构/注释分开)
- `guidelines/code/validation.md` + `techniques/adversarial-verification.md` — Phase 4 的对抗式验证
- `guidelines/workflow/knowledge-promotion.md` — Phase 4 末尾的 promote 评估
