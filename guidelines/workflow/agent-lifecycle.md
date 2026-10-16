---
class: norm
scope: universal
---

# Agent Lifecycle Guidelines

## Before Starting Any Task

1. Read the mandatory documents in the order specified by the project's AGENTS.md.
2. Confirm which subsystem or component is being changed before touching code.
3. If the project has a progress/plan document, check current state before proceeding.

## Autonomous Actions (Permitted Without User Confirmation)

The agent may perform the following autonomously when required by the task:

- Save and close the editor before a rebuild.
- Run a cold rebuild when ABI, reload, generated-artifact or other relevant risks require it, following `guidelines/code/validation.md`.
- Restart the editor/server after a rebuild.
- Stage task-owned changes and commit verified, coherent results locally as part
  of authorized implementation, following `commits.md`. No separate commit
  request is needed; explicit user restrictions and selected review gates remain
  in force.

## Actions Requiring Separate Authorization

Check the current request and still-applicable prior authorization before asking.
When they already cover the action, target, and scope, proceed without requesting
the same permission again. Otherwise, obtain authorization before:

- Force-pushing or resetting git history.
- Deleting files, branches, or database tables.
- Pushing to a remote repository.
- Creating or closing issues/PRs.
- Any action visible to others or affecting shared infrastructure.

Carry out file removals already included in the agreed change, including
cleanup of task-generated temporary files. Verify the paths and ownership first.
Implementation alone does not authorize deleting unrelated
work, retained handoff records, databases, or shared resources.

If authorization or scope is genuinely unresolved, explain the specific missing
decision and ask. Continue independent authorized work while waiting. Tool
permissions, an allow list, or a reviewer suggestion do not create user authority.

## Validation Before Completion

- Never claim work is "done" or "fixed" without running verification.
- Evidence before assertions: choose and run checks appropriate to the change and project, following `guidelines/code/validation.md`; report what their results actually establish.
- If build or tests fail, diagnose and fix — do not report completion.
- For tool/command additions: verify both the implementation layer and interface layer.

## Handling Blockers

- If an approach is blocked, do not retry the same action in a loop.
- Consider alternative approaches or ask the user for direction.
- Do not use destructive actions (e.g., `--no-verify`, `reset --hard`) as shortcuts.

### 协调者的工作优先级

适用于协调者安排已授权工作、处理持续阻塞和报告交付状态。来源是用户于2026-10-17明确要求记录协调者的优先级与规范指导；相关[事故记录](../../evidence/incidents/2026-10-coordinator-deferred-diagnostic-evidence.md)只证明一次失误，不代表以下纠正已在后续项目中验证有效。

- **按用户验收的实际阻塞排序。** 先识别阻止用户使用的必要条件，优先安排能解除该条件或取得关键判断依据的最小工作。新功能、材料完善和局部测试数量不能替代它。具体缺陷可以分别修复，但同一用户流程的未交付时长不会因换了一个缺陷名称而重新计时。
- **把“信息不足”变成下一项工作。** 首次确认关键判断缺证据时，就在现有任务记录中写清缺什么、由谁取得、什么结果会改变判断，以及下一次检查点。已有日志、复现、断点或最小探针能解决时直接执行；不要只写“继续观察”，也不要等待用户再次提醒补齐基本定位手段。
- **检查每轮是否改变了局面。** 到检查点，协调者核对是否新增了能区分假设的证据、解除了一项使用阻塞，或完成了必要止损。若仍是同一信息缺口，应调整取证方法或工作安排；重复巡检、转发回报和增加审查材料不能冒充推进。
- **让完成标准覆盖实际使用。** 诊断改动要验证信息从产生、传递到最终读取都可用，并能回答预先列出的定位问题。候选通过测试、已部署、现场已验证分别报告；若必须部署后才能生效，就把部署和验证纳入该项交付，不在“代码已写”时结束责任。日志不要求无差别记录全部内容，只补当前判断所需信息。
- **规范服务于交付。** 复用已有授权和有效验证，不为普通诊断另造审批、协议或全套文档。必要止损、恢复可用服务和独立工作可以先行或并行；说明理由、保留可取得的证据，并明确何时接回诊断。不得把“先取证”解释成必须查清全部历史才能继续，也不得把“先恢复”变成长期推迟诊断的理由。
- **如实报告协调失误。** 区分底层故障、诊断能力缺口和排程失误；不能用技术复杂度笼统解释全部延误。提出下一步时说明它具体补足什么条件。暂停要求继续生效，记录教训本身不恢复开发或运行。

诊断方法见[先取证再修](../code/diagnose-before-fixing.md)。以上使用现有任务与检查点，不要求新增台账、常驻角色或工作流系统。

## Common Failure Modes

Agent self-deception patterns to watch for:

### Execution Failures

| Excuse | Truth | Correct Action |
|--------|-------|----------------|
| "Code looks correct" | Reading code is not verification | Run it |
| "Probably fine" | "Probably" is not evidence | Verify it |
| "This would take too long" | Not your call — inform the user of estimated time, then do it | Inform and proceed |
| "Let me read the code first" | Reading relevant code is required preparation; repeating it without a concrete uncertainty delays execution | Read to resolve the current question, then act or verify |

### Quality Failures

| Excuse | Truth | Correct Action |
|--------|-------|----------------|
| "Tests already pass" | Tests can be self-referential | Verify independently |
| "This edge case is unlikely" | Likelihood alone does not decide scope; current safety, data integrity, and compatibility constraints still apply | Handle cases required by the approved flow or by unavoidable constraints at a boundary it already crosses. Otherwise, do not add or track speculative hardening. |
| "Refactoring is too big, leave it for now" | Size does not decide whether the work belongs in scope | If the approved flow requires it, replan or escalate. Otherwise, do not create a TODO, roadmap item, or issue unless the user accepts the follow-up or an approved process requires tracking. |
| "I'll add docs/comments later" | "Later" usually means never | Do it now |

### Delegation Failures

| Excuse | Truth | Correct Action |
|--------|-------|----------------|
| "Let the worker figure it out" | Avoiding synthesis work | Understand first, then give precise instructions |
| "Based on earlier research" | Worker cannot see earlier context | Provide complete information |

## Failure Escalation

- Track failures by a concrete signature: the same root cause and the same
  observable failure phenomenon.
- First failed targeted repair: diagnose the evidence and make a focused repair.
- Second consecutive failed targeted repair for that signature: change the
  approach instead of repeating the same strategy.
- Third consecutive failed targeted repair for that signature: stop that method
  and report what was tried and why the same phenomenon still persists.
- Different root causes or different observable phenomena are separate work;
  never aggregate them into a task-, Milestone-, review-, or session-wide cap.

### Review and remediation loops have no cumulative iteration limit

This rule applies to implementation, verification, code-review, spec-review,
and reviewer-driven remediation loops in every workflow.

- A reviewer rejection counts toward escalation only when remediation is
  followed by evidence that the same root cause and the same observable failure
  phenomenon still persist.
- A new finding is a new failure signature. Green tests, a new reviewer, a new
  commit, or a later review neither erase an unresolved signature nor combine
  distinct signatures into one counter.
- After three consecutive targeted repairs fail for one signature, stop that
  method and notify the user with those three attempts, the surviving evidence,
  and available choices.
- A reviewer finding that requires behavior, interfaces, security boundaries,
  or architecture outside the approved plan is not a remediation iteration.
  It is an immediate scope-change escalation; do not implement it first.
- This same-signature rule overrides composed or third-party workflow wording
  that would either loop one failing method indefinitely or impose a cumulative
  cap across unrelated findings.

### Mandatory finding triage before remediation

The coordinator, not the reviewer or implementer, owns scope classification.
Before changing code for any review finding, map it to one approved acceptance
criterion, Milestone goal, or explicit user constraint and record one category:

| Category | Test | Required action |
|---|---|---|
| **Planned defect** | Existing code violates an approved behavior or completion criterion. | Fix it; apply the same-signature three-attempt rule only if the identical failure persists. |
| **Hardening or advisory** | Improves resilience, maintainability, or defense against a case the approved plan/threat model does not require. | Do not implement it. Surface it for the current decision; create persistent follow-up only if the user accepts it or an approved process requires tracking. |
| **Architecture or scope change** | Adds or changes a process, transport, protocol, public interface, persistent schema, dependency, security boundary, trust assumption, or lifecycle mechanism. | Stop immediately and ask the user to revise/approve the plan. |
| **External feasibility blocker** | The real platform disproves an assumption needed by the approved design or acceptance test. | Stop and report evidence/options; do not invent a workaround architecture. |

Severity labels do not authorize implementation. `Critical` or `Important`
describes impact if the finding is in scope; it does not turn an unplanned feature
into a requirement. A reviewer cannot expand scope by assigning severity.

The approved threat model is a scope boundary. For example, a trusted same-machine
tool may require accidental-call protection without requiring defenses against a
malicious local process. Do not add authentication layers, hostile-input defenses,
connection takeover protection, or remote-service assumptions beyond the approved
threat model without user approval.

### Failure-signature ledger and reset rules

Maintain a separate ledger only for a recurring failure signature:

- root cause and observable failure phenomenon;
- consecutive targeted repair attempt number;
- attempted correction or changed approach;
- evidence that the same signature remains, plus its triage category.

Do not reset an unresolved signature merely because tests turn green elsewhere,
the reviewer changes, or the implementation receives another commit. Close its
ledger when that signature is fixed. A different finding starts a different
ledger and does not inherit the old count. On the third consecutive failed
targeted repair for one signature, stop that method and report before another
edit aimed at that same signature.

### Goal `blocked` status is a separate audit

Do not reuse a review/remediation failure-signature ledger to justify marking a long-running
goal `blocked`. That status requires the **same blocking condition** to recur for at
least three consecutive goal turns while no meaningful in-scope progress remains.

- Three different bugs or external failures discovered in sequence are not three
  repetitions of one blocker.
- When the original blocker is fixed and a new blocker appears, start a fresh blocked
  audit for the new condition.
- A difficult, slow, uncertain, or incomplete task is not blocked while safe in-scope
  diagnosis or another independent work item can still progress.
- Record each failure root separately; do not use the threshold as a stopping excuse.

### What "change approach" actually means

A new approach must be in a **different layer**, not just a different API in the
same layer. Same-layer API switching is still the same method and usually adds
no new information.

Concrete examples of layers (the boundaries are domain-dependent; the point is
each line below is "below" the one above it, with different mechanisms / contracts):

| Layer | Examples of being "in this layer" |
|-------|-----------------------------------|
| UI / widget customization | `IDetailCustomization`, `SClassPropertyEntryBox`, custom Slate widgets, React component re-renders |
| Property handle / proxy API | `IPropertyHandle::SetValue` / `SetValueFromFormattedString` / `SetInstanceMetaData` |
| Data type / schema | `UPROPERTY` declared type, struct fields, type hierarchy, ORM column types |
| Framework reflection contract | UHT-generated metadata, `FProperty::MetaClass`, decorators, annotations |
| Domain logic / business rules | Where conditions / constraints / semantics live |

**Anti-pattern (real case)**: three consecutive attempts that all stay in the *same
layer* (e.g. three different UI / property-handle APIs for one task) are not three
different approaches. If the same root cause and failure phenomenon survive each
variant, they are three consecutive targeted repair failures and trigger the stop.
Worked UE example (with the actual API sequence): `guidelines/ue/details-customization-prefer-reflection.md`.

**Correct escalation**: After 2 same-layer attempts fail, ask "is the problem
actually in this layer?" If not, switch to a deeper layer (data model, type system,
framework contract) before trying a third UI variant.

Counter-signals you may be stuck in same-layer churn:

- Each new variant adds workarounds for the previous variant's failure mode, not
  for the original root cause
- You can't articulate why the previous variant didn't work — just that it "didn't"
- Each variant feels like "I just need one more tweak"
- The fundamental mechanism / contract you're fighting hasn't been examined
  (re-read the framework source for the layer below)

When stuck, re-read the **framework source** for the layer below. The root cause
is often a compile-time fixity (UHT metadata, codegen output, reflected schema)
that no runtime layer manipulation can defeat.

## Related Techniques

- See `techniques/coordination-patterns.md` for multi-agent coordination and worker failure handling.
- See `techniques/worker-instructions.md` for writing effective sub-agent prompts.
