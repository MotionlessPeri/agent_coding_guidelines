---
id: 2026-08-optional-dict-blamed-on-the-contract
date: 2026-08
kind: 命中
model: unknown
project: retarget-study
caught_by: 用户
tags: [rule-1, 归错层]
pages: [guidelines/code/reporting-limits-and-null-results.md]
---

**现象**：报「契约表达不了挂两份算子，已请上游裁决」。

**真因**：是自己写的接口把字段声明成 `Optional[dict]` 造成的；底层的 vector 加 binding 一直支持挂多份。限制在「我的接口」这一层。自己是那层作者，收窄在脑子里是「现状」，出口就成了「约束」。

**代价**：一次无谓的上游请求，外加被迫取折中配置，某个部位的功能整个做不了。

**怎么被发现的**：用户直接质疑「这不对吧」。
