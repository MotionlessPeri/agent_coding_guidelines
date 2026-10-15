---
id: 2026-08-p95-blind-to-threshold
date: 2026-08
kind: 命中
model: unknown
project: retarget-study
caught_by: 自查
tags: [rule-2, 数值聚合]
pages: [guidelines/code/reporting-limits-and-null-results.md]
---

**现象**：一个按速度阈值决定是否「锁住」的算子，阈值扫了 60 倍，p95 与最大值三档完全不动，初判「参数没接上，主导因素不是阈值」。

**真因**：阈值确实接上了。逐位复验：相邻阈值两两比最大差 4.27 cm，8417 帧里 8338 帧有差；中位偏差随阈值单调下降 2.71 → 0.21 cm。不动的是大偏差那一头，因为高速帧（26.4%）在每一档下都判「没锁住」，而大偏差全出在这些帧上。p95 和最大对这个参数天生不敏感。

**代价**：差一步误判接线。

**怎么被发现的**：逐位比原始输出。
