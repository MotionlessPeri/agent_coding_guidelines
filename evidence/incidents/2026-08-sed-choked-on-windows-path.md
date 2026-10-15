---
id: 2026-08-sed-choked-on-windows-path
date: 2026-08
kind: 命中
model: unknown
project: mobu-plugin
caught_by: 自查
tags: [shell生成代码, 转义, sed]
pages: [guidelines/code/generating-code-through-shell.md]
---

**现象**：用 `sed` 改一段含 Windows 路径的内容，报 `unterminated 's' command`。

**真因**：路径里的反斜杠和斜杠毁掉了 sed 表达式。同一次会话里和 heredoc 吃反斜杠是两次独立命中，用户自述「遇到很多次了」。

**代价**：一次失败的替换，加一轮排查表达式。

**怎么被发现的**：报错。修法：用写文件工具，或用 Python 做替换。
