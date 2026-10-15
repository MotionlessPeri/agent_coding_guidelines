---
id: 2026-10-compaction-hid-own-test-tool
date: 2026-10
kind: 命中
model: unknown
project: mobu-tool-plugin
caught_by: 用户
tags: [rule-3, 可达范围, 上下文压缩]
pages: [guidelines/code/reporting-limits-and-null-results.md]
---

**现象**：上下文压缩之后报「插件只有界面按钮，这个我测不了」，把测试交给用户。

**真因**：测试工具是本会话早些时候自己搭的，放在会话临时目录里；压缩后的摘要没带上它。我能看到的（摘要）不等于我做过的（磁盘上）。

**代价**：一次本可自动跑的回归被外包给用户。

**怎么被发现的**：用户指出。修法：说「做不到」之前，先列一下本会话的临时目录和产物目录。
