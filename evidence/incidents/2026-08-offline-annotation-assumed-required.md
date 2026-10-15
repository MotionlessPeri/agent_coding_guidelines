---
id: 2026-08-offline-annotation-assumed-required
date: 2026-08
kind: 命中
model: unknown
project: retarget-study
caught_by: 用户
tags: [rule-1, 归错层]
pages: [guidelines/code/reporting-limits-and-null-results.md]
---

**现象**：报「依赖离线人工标注，不适用」，整个能力被搁置。

**真因**：那份输入烘的是可以自己算出来的几何，而且运行时根本不需要它。限制在「我对输入的理解」这一层，不在方法。

**代价**：整个能力被搁置数周，之后才被翻回来。

**怎么被发现的**：用户质疑。
