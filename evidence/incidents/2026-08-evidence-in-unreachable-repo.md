---
id: 2026-08-evidence-in-unreachable-repo
date: 2026-08
kind: 命中
model: unknown
project: unknown
caught_by: 第三方复核
tags: [rule-3, 可达范围]
pages: [guidelines/code/reporting-limits-and-null-results.md]
---

**现象**：审计一份文档，判某条断言「无刻画记录 / 无依据」。

**真因**：证据存在，住在一个从这份文档无法到达的仓里（被 gitignore 的独立仓）。任何只审这份文档的人都会得出同一个错结论。

**代价**：一条有依据的断言被判无依据。写者侧的修法：目标在读者拿不到的仓时，不能只给指针，要连关键证据一起摘。

**怎么被发现的**：第三方复核。
