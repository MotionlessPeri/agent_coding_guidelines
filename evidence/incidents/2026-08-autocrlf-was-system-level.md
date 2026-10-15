---
id: 2026-08-autocrlf-was-system-level
date: 2026-08
kind: 命中
model: unknown
project: unknown
caught_by: 实验
tags: [前提, 机器, 内在前提]
pages: [guidelines/code/premises-not-in-the-text.md]
---

**现象**：写下「本仓的 `core.autocrlf=true`」。

**真因**：实测它来自 system 层配置，不随仓库走。换台机器，同一条命令不同口径。「本仓实测」和「本机实测」是两个不同的断言，「实测」这个标签也要写作用域。同一场里还分清了一个内在前提：「两份文件是不是同一份」这个问题离开行尾规范化约定就没有意义，filter 配置这个前提移不掉，只能写出来并连取值一起记；拿它当缺陷去「修」，得到的工具更严格且答错问题。

**代价**：判「同一份文件」的口径在另一台机器上会悄悄变化。

**怎么被发现的**：在另一个层级查配置来源。
