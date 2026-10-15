---
id: 2026-08-commit-diff-rule-called-a-hole
date: 2026-08
kind: 命中
model: unknown
project: unknown
caught_by: 第三方复核
tags: [测量四问, 判据, 覆盖不了的两种意思]
pages: [techniques/measurement-four-questions.md]
---

**现象**：某类损坏没被「提交前读全 diff」拦住，被说成那条纪律有洞。

**真因**：那类损坏在提交发生之前就已完成，根本不经过「提交前读 diff」那道口。「A 覆盖不了 X」有两种意思：A 有洞该补 A，或 X 不属于 A 的问题该另立判据；两者在句子里长得一样，判法是问 X 会不会通过 A 所守的那道口。

**代价**：差一步给一个已完整的判据加一道无关的门。

**怎么被发现的**：第三方复核。
