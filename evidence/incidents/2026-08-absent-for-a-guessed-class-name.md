---
id: 2026-08-absent-for-a-guessed-class-name
date: 2026-08
kind: 生效
model: unknown
project: ue-retarget
caught_by: 自查
tags: [rule-3, 猜的名字]
pages: [guidelines/code/reporting-limits-and-null-results.md]
---

**现象**：探测一个类名返回 `ABSENT`，差一步报「框架没有这个工厂」。

**真因**：探的是自己猜的名字。真名少一个 `-er`：`UIKRetargetFactory`，不是 `UIKRetargeterFactory`。探测器返回的是关于那个字符串的真相，不是关于世界的真相。

**代价**：差一步给出一个零征兆的错「不存在」。

**怎么被发现的**：当事 lane 自己在写回执的过程中抓住的，因为规则 3 那一问当时已经带在手上。错误状态留下了痕迹：那句差点发出的话写进了回执。这是规则当天就产生效用的直接证据。
