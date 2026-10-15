---
id: 2026-08-log-file-as-observation-window
date: 2026-08
kind: 命中
model: unknown
project: unknown
caught_by: 事后复盘
tags: [rule-3, 观测窗口]
pages: [guidelines/code/reporting-limits-and-null-results.md]
---

**现象**：报「日志里零命中，所以修复后没有复发」。

**真因**：观测窗口被「哪个日志文件」隐式界定，而文件边界跟「修复之后」这个窗口边界不一致：可能更宽（跨了修复点，历史污染），也可能更窄（日志因重启翻篇，运气好）。

**代价**：「没有复发」这个结论的窗口没有被写出来。修法：窗口用时间戳显式界定，不用文件容器代替。

**怎么被发现的**：复盘。
