---
id: 2026-08-port-covered-half-the-operator
date: 2026-08
kind: 命中
model: unknown
project: retarget-study
caught_by: 第三方复核
tags: [rule-1, 归错层]
pages: [guidelines/code/reporting-limits-and-null-results.md]
---

**现象**：报出去的话是「这个算子从不解决 A-vs-B 那类穿插，这是它的能力边界」。协调者把这句原样转给了第三方 lane。

**真因**：移植只搬了原算子 930 行里的 125 行，少的那半正是解 A-vs-B 的，而且在原框架里默认开启。限制在「我的移植」这一层，不在算子。

**代价**：一个可用能力被判为不可用；错结论经转发污染了一圈。

**怎么被发现的**：别人复核源码。不是自查。
