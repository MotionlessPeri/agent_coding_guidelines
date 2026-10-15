---
id: 2026-07-offscreen-gl-segfault-in-smoke
date: 2026-07
kind: 命中
model: unknown
project: retarget-study
caught_by: 实验
tags: [GUI验证, 离屏渲染]
pages: [guidelines/code/gui-visual-machine-gating.md]
---

**现象**：想用 `QT_QPA_PLATFORM=offscreen` 无头渲染截图做冒烟，`pyqtgraph.opengl` 的 `GLViewWidget` 一构建就段错误，exit 139；`renderToArray` 同样段错误；软件 GL 也救不了。

**真因**：offscreen 平台没有 GL context。逐步 spike 后发现，在有桌面会话的开发机上走默认平台、不 `show()`、直接 `grabFramebuffer()` 能拿到非空帧；真 headless 会失败。

**代价**：若把截图当硬 gate，CI 会神秘挂。修法：GL 冒烟走默认平台不设 offscreen，断言像素非空，当 best-effort；机器 gate 的牙留在纯函数。不同栈（EGL、OSMesa、headless Chromium、引擎 nullrhi）各有各的坑，先 spike 探测目标环境能不能渲、怎么截图。

**怎么被发现的**：spike 实验。
