---
id: 2026-08-uncertainty-moved-to-mesh-consumer
date: 2026-08
kind: 命中
model: unknown
project: unknown
caught_by: 外部追问
tags: [rule-4, 数字的机制]
pages: [guidelines/code/reporting-limits-and-null-results.md]
---

**现象**：「源侧推法的不确定度等于被消费量的 28% 到 67%」被外推到另一个消费方的对照上。

**真因**：那个数有完整机制支撑（两种推法给出不同的接触点），但另一个消费方走真实网格顶点，「靠推」这个误差源在那边根本不存在。机制都对，搬到了机制不成立的地方。

**代价**：一个有依据的数在错的场景里继续显得可信。

**怎么被发现的**：对方追问机制。这条和「alpha 性质」一例分属两个项目，双方各命中一种形态。
