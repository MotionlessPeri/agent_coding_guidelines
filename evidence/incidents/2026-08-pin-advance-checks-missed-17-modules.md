---
id: 2026-08-pin-advance-checks-missed-17-modules
date: 2026-08
kind: 命中
model: unknown
project: mocap-pipeline
caught_by: 事后复盘
tags: [lane拓扑, 事件触发]
pages: [guidelines/collaboration/lane-topology-design.md]
---

**现象**：版本钉定前进、目录搬迁之后的连带检查靠人记得，层表的登记欠账攒到 17 个模块才被撞见。

**真因**：复核依赖「记得在 pin 前进后查一下」，会漏，且漏的读数是绿的。

**代价**：17 个模块的欠账一次性暴露。修法：事件触发表，挂 git 可观察事件（版本钉定前进、目录搬迁、合并上游），由协调 lane 执行对应复核。

**怎么被发现的**：撞见。
