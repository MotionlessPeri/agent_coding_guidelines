---
id: 2026-08-seam-count-inflated-by-test-references
date: 2026-08
kind: 命中
model: unknown
project: mocap-pipeline
caught_by: 第三方复核
tags: [lane拓扑, 接缝计数]
pages: [guidelines/collaboration/lane-topology-design.md]
---

**现象**：接缝表给一条缝的 breaking change 预告等级定高了一档。

**真因**：非生产引用（mock、测试）和生产引用点并列计数，把引用数抬高了。接缝计数要分生产与非生产。

**代价**：一次被高估的预告等级。

**怎么被发现的**：第三方复核计数。
