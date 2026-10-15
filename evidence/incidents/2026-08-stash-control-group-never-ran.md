---
id: 2026-08-stash-control-group-never-ran
date: 2026-08
kind: 命中
model: unknown
project: unknown
caught_by: 自查
tags: [rule-3, 对照组]
pages: [guidelines/code/reporting-limits-and-null-results.md]
---

**现象**：用 `git stash` 前后各数一次测试数当对照组，两次数出同一个数，读成「改动没有影响」。

**真因**：`git stash push` 默认不带未跟踪文件，于是「改前」的树和「改后」一模一样，对照组根本没跑。「两边一样」在验证语境里长得像好消息，所以比「恰好为 0」更难自查。

**代价**：差一步把一个没生效的对照当成「无回归」的证据。

**怎么被发现的**：补做了那个「让它必定失败的操作」：stash 后确认那两个文件真的从树上消失了，一行 `ls` 的事。
