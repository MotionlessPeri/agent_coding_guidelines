---
id: 2026-08-change-gate-blind-to-never-existed
date: 2026-08
kind: 命中
model: unknown
project: unknown
caught_by: 事后复盘
tags: [rule-3, 可达范围]
pages: [guidelines/code/reporting-limits-and-null-results.md]
---

**现象**：一个只在数值变化时报警的 gate 一直绿，被读成「这个量没问题」。

**真因**：它对「这个量从来就没有过」是盲的，只会报「变了」，不会报「一直没有」。缺席的两种成因（真的没有 / 我看不到）给出同一个观测。

**代价**：「一直没有」这件事在 gate 的覆盖范围之外，绿灯没有信息量。

**怎么被发现的**：复盘时对照规则 3 的那一问。
