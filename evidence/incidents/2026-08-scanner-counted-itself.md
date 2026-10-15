---
id: 2026-08-scanner-counted-itself
date: 2026-08
kind: 命中
model: unknown
project: unknown
caught_by: 自查
tags: [测量四问, 总体, 量具在总体里]
pages: [techniques/measurement-four-questions.md]
---

**现象**：一个扫描器把自己的脚本算成了「写过那个文件」的进程。

**真因**：量具自己在总体里。报分母对这种失效无效，补完一条要问「我刚补的这条，对同一格的其他失效有效吗」。

**代价**：一条不存在的写入者。修法：把量具自己喂给它，它应当排除自己。

**怎么被发现的**：看原始记录。
