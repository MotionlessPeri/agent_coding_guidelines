---
id: 2026-08-host-hang-blamed-on-user-file
date: 2026-08
kind: 命中
model: unknown
project: mobu-plugin
caught_by: 用户
tags: [rule-1, 用户产物, 加载器]
pages: [guidelines/code/reporting-limits-and-null-results.md, guidelines/code/diagnose-before-fixing.md]
---

**现象**：宿主打不开用户交来的场景文件，报出去的话是「这份 fbx 打不开，可能是它坏了」。

**真因**：自己这层刚引入的 bug。插件把启用状态序列化进了场景文件，宿主重开时恢复它，于是插件的启动逻辑（阻塞握手、建对象、起线程）在加载中途、宿主半初始化时跑起来，表现就是「打开到一半卡住」。修法是加载期守卫：监听宿主的加载开始 / 结束事件，加载期间强制停用。

**代价**：差一步把一份内含生产同事手调 17 项参数的交付文件判为损坏。「用户的产物坏了」的自然下一步是丢弃或重做，而且丢掉不报错。后来绕开宿主、用格式 SDK 直读抢救，17/17 参数命中，这次抢救本来根本不必发生。

**怎么被发现的**：用户点出。独立判据是 SDK 直读：读通了同时证明文件没坏、问题在插件。
