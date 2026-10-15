---
id: 2026-08-ordering-constraint-under-another-name
date: 2026-08
kind: 命中
model: unknown
project: unknown
caught_by: 第三方复核
tags: [rule-4, 按名字查]
pages: [guidelines/code/reporting-limits-and-null-results.md]
---

**现象**：某顺序约束的逐对声明接口在三个算子里 grep 零命中，报成「框架不拦顺序」。

**真因**：约束是用另一个机制、在另一个文件（处理器级遍历）表达的，那处源码还明写了为什么不用逐对声明。按名字查的零命中只证明「这个名字没有」，不证明「这件事没做」。这跟「探的名字是猜的」不同：这里名字对，而那件事换了机制。

**代价**：一条框架保证被报成不存在。

**怎么被发现的**：第三方复核。
