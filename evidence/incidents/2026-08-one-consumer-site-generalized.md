---
id: 2026-08-one-consumer-site-generalized
date: 2026-08
kind: 命中
model: unknown
project: unknown
caught_by: 第三方复核
tags: [rule-4, 只取一个点]
pages: [guidelines/code/reporting-limits-and-null-results.md]
---

**现象**：从一处消费点推出「这个参数在别处不被消费」。

**真因**：只取了证据链上的一个点，然后把结论外推到整条链。它和「按名字查零命中」那例外推方向相反（一个从上游推下游，一个从一处推全体），说明问题不在方向，在「只取一个点」这个动作。

**代价**：对参数用途的错判。修法：读一个参数先 grep 它的名字拿到全部出现点，再决定读哪几处。

**怎么被发现的**：第三方复核。
