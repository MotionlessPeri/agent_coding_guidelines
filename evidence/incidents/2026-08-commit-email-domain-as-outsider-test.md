---
id: 2026-08-commit-email-domain-as-outsider-test
date: 2026-08
kind: 命中
model: unknown
project: unknown
caught_by: 实验
tags: [前提, 人员构成, 谁的仓]
pages: [guidelines/code/premises-not-in-the-text.md]
---

**现象**：用「commit email 不是我们的域 ⇒ 这是外部的改动」做判据。

**真因**：人员构成变化最慢，所以最不像会过期的东西，过期时没有任何近因提示回头看。而且它还叠加「在哪个仓问」：同一段代码在两个仓里 email 不同，跨仓搬运的 commit 顶替了原作者。

**代价**：归属判断在换仓或人员变动后静默失真。

**怎么被发现的**：对同一段代码在两个仓里核对。
