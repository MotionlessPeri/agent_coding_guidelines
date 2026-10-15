---
id: 2026-08-stream-died-after-unlogged-user-action
date: 2026-08
kind: 命中
model: unknown
project: mobu-plugin
caught_by: 用户
tags: [操作史, 日志]
pages: [guidelines/code/diagnose-before-fixing.md]
---

**现象**：一个下游订阅方的数据流永久失效，日志只有一条格式错误，没有任何操作痕迹。

**真因**：用户在流送过程中切换了一个流类型开关。这个信息不在任何日志里，是用户自己说的；拿到它之后才能去源码里确认机制（同名原地换定义、不注销旧的）并给出规避纪律。日志记结果，不记「这个人五分钟前在界面上点了什么」。

**代价**：只在日志里找会一直找不到复现条件。

**怎么被发现的**：问用户「你刚才做了什么操作」。
