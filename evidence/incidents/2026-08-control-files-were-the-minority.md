---
id: 2026-08-control-files-were-the-minority
date: 2026-08
kind: 命中
model: unknown
project: unknown
caught_by: 实验
tags: [测量四问, 总体, 报分母]
pages: [techniques/measurement-four-questions.md]
---

**现象**：拿 3 个「没碰过的」文件当对照组判行尾口径，结论反了。

**真因**：全体 301 个文件里只有 25 个是那种行尾，3 个对照文件全落在这 25 个的少数派里。

**代价**：一个反向结论。修法：报分母，一条命令的事（`git ls-files --eol` 加计数）；判「代表不代表」贵，报「占多少」便宜，而后者足以让「不代表」当场可见。前提是总体有枚举器。

**怎么被发现的**：数分母。
