---
id: 2026-08-symptom-hung-on-wrong-cause
date: 2026-08
kind: 命中
model: unknown
project: unknown
caught_by: 事后复盘
tags: [rule-1, 文档写法]
pages: [guidelines/code/reporting-limits-and-null-results.md]
---

**现象**：一份接入文档写「视口不实现某方法 ⇒ 拖拽后没有撤销」。

**真因**：症状为真，成因挂错了对象。撤销缺失是因为读者自己那层没人替他 push 撤销记录，不是视口少实现一个方法。读者能自己复现症状却验不了成因，可验的那半替错的那半背了书。

**代价**：照做的读者白实现一个方法，回到同一个症状，此时更可能怀疑自己实现错了，而不是怀疑那句断言。

**怎么被发现的**：收尾复盘时发现。写法修正：症状一句、成因一句，拆开写。
