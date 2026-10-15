---
id: 2026-08-lane-rejected-own-candidate
date: 2026-08
kind: 生效
model: unknown
project: unknown
caught_by: 事后复盘
tags: [rule-3, 规则生效统计]
pages: [guidelines/code/reporting-limits-and-null-results.md]
---

**现象**：同一天六条 lane 的收尾复盘里，统计「报结论」这组规则有没有当场拦住过误判。

**真因**：按「错误状态有没有留下第三方能看见的痕迹」这个判据，只有 1 条可出示：某 lane 用规则 3 否掉了自己一条候选，那条候选连同理由完整写在它的回报里。另有 4 条是「我本来会写 X、实际写了 Y」的自述，退回不可证伪一档。

**代价**：无。这条记的是统计口径：规则生效的次数结构性只报下界，规矩内化越好，错误状态越不成形、痕迹越少，所以这个数只能作存在性证明，不能跟命中数并列读。

**怎么被发现的**：收尾复盘。
