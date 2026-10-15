---
id: 2026-08-recipe-pinned-to-head
date: 2026-08
kind: 命中
model: unknown
project: unknown
caught_by: 事后复盘
tags: [前提, 时刻, 移动引用]
pages: [guidelines/code/premises-not-in-the-text.md]
---

**现象**：一条复现配方写 `git show HEAD:<path>` 来取「坏版本」。

**真因**：`HEAD` 是移动引用。fix 一提交，它就指向好版本，而配方文字一个字没变。「什么时候跑」被写进了正确性前提，而它不在文字里。

**代价**：配方在写下之后不久就静默失效，照做的人拿到的是好版本，复现不出来。

**怎么被发现的**：复盘。修法是换不动引用 `<sha>^:<path>`，这是四次同族命中里唯一一次能真换掉实现的。
