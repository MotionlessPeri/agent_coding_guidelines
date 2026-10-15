---
class: experience
scope: multi-lane-projects
triggers: [lane, 拓扑, 切 lane, 重切, 开新 lane, 接缝, role description, 裁撤 lane, 并行派活, 多会话]
born: "2026-09，写下时的模型未记录"
retested: []
incidents:
  - 2026-08-lane-boundaries-crossed-repo-boundaries
  - 2026-08-four-cross-lane-errors-all-on-seams
  - 2026-08-review-lane-idle-between-campaigns
  - 2026-08-hotfix-lane-premise-silently-gone
  - 2026-08-shared-tree-write-conflicts
  - 2026-08-pin-advance-checks-missed-17-modules
  - 2026-08-seam-count-inflated-by-test-references
  - 2026-08-lane-ran-in-removed-worktree-dir
  - 2026-08-archived-address-semantics-changed-thrice
  - 2026-08-seam-numbers-in-brief-anchored-all-lanes
---

# Lane 拓扑设计：怎么切、什么时候重切

本文管拓扑怎么设计。lane 间的日常协调（唤醒、brief、收件箱、轮换）在 `skills/collaboration/role-lane-coordination`，同仓多会话的 hook 底层在 `multi-session-coordination`，两处不复述。

## 六条规则

1. **lane 边界跟仓库边界对齐，不跟技术子域对齐。** 每个独立仓（含 submodule 升独立仓的）一条 lane，拥有整仓加对外口。代码会搬家，域跟仓渐行渐远，每刀跨界；技术专长做「顾问」职能写进 role，不做边界。
2. **职能三权分立，每条 lane 写明「不做」清单。** 协调（派单、版本钉定、对外出口，不实现）；实现（一条 lane 吃下一个仓的全部代码）；裁决（设计加正确性审，零文件所有权）。实现集中一条之后，同仓并发写从常态变例外，写冲突纪律仍要，但从每天的事降为边缘情况。
3. **审查不常驻。** 正确性审并入裁决 lane；大型审计按 campaign 制临时开 lane，审完归档。审查是波动负载，常驻的成本换不来空转期的价值。
4. **接缝要有名有主，触发挂事件不挂人。** 两条 lane 边界相交的每个契约面登记成表：缝、owner、协调规则、两端同改时谁主导谁复核。连带复核挂 git 可观察事件（版本钉定前进、目录搬迁、合并上游），由协调 lane 执行。接缝计数要分生产与非生产引用。
5. **role description 只写归属与边界。** 会变的数字、命令、读数走 durable 文档指针；role 不会因过期变红，写进去的每个数都是给下一代埋的假话。同一事实只写一处，其余 lane 的 role 给指针。
6. **lane 数量即成本。** 每条 lane 是一个独立模型会话（multi-agent 约 15 倍单 chat，见 `techniques/coordination-patterns.md`）。加 lane 或并行派活前先给用户一行报价，强度档由用户选。

裁撤或保留一条职能 lane 时问「它的存在前提（隔离树、独立判官、专属域）还在吗」，别问「它最近忙不忙」；流量是结构性下界，忙闲读不出存在前提。

## 新拓扑的形状

```
<共享库A>/hub   库整仓 + 对外口（push 通知 → 主项目收 pin；breaking change 预告双下游）
<共享库B>/hub   同上（嵌套第三方依赖的版本钉定也归它）
<主项目>/hub    纯协调：需求池 / 派单验收 / 三层版本钉定 / 对外出口 / 事件触发表执行人
<主项目>/app    全部实现 + 生产值守（值守优先级高于开发线，用户可改）
<主项目>/design 设计裁决 + 正确性审，零文件所有权；领域中性门的判官
（退役）        arch 并入 hub；render、ui 按仓归位；review 并入 design；hotfix 并入 app
```

裁决权与文件所有权可以分离：跨仓 invariant 的门（测试）住被守的仓，判官（词表、豁免的裁决权）住仓外的裁决 lane，被审对象自己改判据的通道从结构上关闭。

## 重划本身怎么做

1. 先裁时序：业务收尾和拓扑重切谁先。把否掉的选项连同理由留档，否则轮换后它会被重提。
2. 多源 handoff：每条旧 lane 只写自己域的交接节；新 lane 读齐全部来源后做 smoke（回显读过的清单、cwd、自己理解的边界），裁决 lane 逐条收 smoke 后才宣告迁移完成。
3. 换角色不是退役：原地重 attach 带新 role，对话与历史保留；退役是终态，只给「这条 lane 不再需要了」用。归档地址能否复用是平台语义且随版本变，写进项目文档时带日期与出处。
4. 新 lane 的 cwd 显式指定并让它自证（`git worktree list` 看 cwd 在不在清单里）。
5. 想保留独立复核能力的数，别写进人人必读的表；进了 brief 的数会锚定所有 lane。
6. 每条新 role 过一遍「不做」清单，由裁决 lane 收 smoke；拓扑变更不夹带范围蠕变。

## 证据

事故记录见本页 frontmatter 的 `incidents`，统计由 `kb.py index` 生成。来源是一次真实的拓扑重划（一个 mocap 项目，8 条按技术子域加职能混切的 lane 改成 3 仓 6 lane 按仓加三权切）和重划后一周的运行实测。切法规则已被新拓扑的日常运行验证；重划本身的执行经验只跑过一遍，用户主导促升，apply-and-refine。

## 相关

- `skills/collaboration/role-lane-coordination`：lane 间日常协调方法，本文是它的上游一步。
- `skills/collaboration/multi-session-coordination`：同仓多会话的 lease / inbox hook 底层。
- [`../../techniques/coordination-patterns.md`](../../techniques/coordination-patterns.md)：multi-agent 成本账与「值不值得并行」。
- [`../../techniques/worker-instructions.md`](../../techniques/worker-instructions.md)：派单 brief 的自含性与锚定。
