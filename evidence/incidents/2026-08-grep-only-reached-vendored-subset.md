---
id: 2026-08-grep-only-reached-vendored-subset
date: 2026-08
kind: 命中
model: unknown
project: unknown
caught_by: 事后复盘
tags: [rule-3, 可达范围]
pages: [guidelines/code/reporting-limits-and-null-results.md]
---

**现象**：消费方查「库里有没有 X」，grep 零命中，报「没有」。

**真因**：查的是 `external/<lib>/`，那是消费方能到达的全部，但不是库的全部。

**代价**：结论碰巧没错。报告者事后自评：「我当时没说这句边界，是运气好结论没错。」它这次没咬人，不代表下次不咬。

**怎么被发现的**：报告者自己复盘。
