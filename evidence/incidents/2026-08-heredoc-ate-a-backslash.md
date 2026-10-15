---
id: 2026-08-heredoc-ate-a-backslash
date: 2026-08
kind: 命中
model: unknown
project: mobu-plugin
caught_by: 自查
tags: [shell生成代码, 转义, 静默失败]
pages: [guidelines/code/generating-code-through-shell.md]
---

**现象**：用「shell heredoc 到解释器再生成文件」这条链落盘一个 `.py`，源里写的 `"A\\nB"` 到了解释器变成 `A` 加真换行加 `B`，生成的文件第 66 行字符串未闭合，整份文件 SyntaxError；它被 `exec` 加载，于是什么都不跑、什么都不报。两轮各约 7 分钟的宿主启动等待，两次都先怀疑「环境慢、宿主卡了」。

**真因**：heredoc 吃掉一层反斜杠，`<<'EOF'` 挡不住，说明吃转义的那层在 shell 之上（工具把命令交给 shell 之前）。判定要用字节和长度，`repr()` 把真换行也印成 `\n`，两种情况长得一样。argv 单引号传参通道不吃。

**代价**：两次 7 分钟误判为环境问题；「没有输出」有两种成因，而两种观测一样。

**怎么被发现的**：看生成文件的字节。修法按优先级：用写文件工具；非要走 shell 用 argv；干脆不产生反斜杠；生成完先 `py_compile` 再交给宿主，这道门自己先注入语法错确认会红。
