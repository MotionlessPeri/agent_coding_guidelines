---
id: 2026-07-ui-framework-chosen-by-viewport-texture-path
date: 2026-07
kind: 命中
model: unknown
project: renderer-test
caught_by: 事后复盘
tags: [GUI验证, 框架选型, 渲染器视口]
pages: [guidelines/code/gui-visual-machine-gating.md]
---

**现象**：给一个主输出是实时 GPU 画面的工具选 UI 框架时，按控件多不多、好不好看比较。

**真因**：决定性因素是视口怎么拿到渲染结果。能跟渲染器共享同一 GPU 设备的框架（如 Dear ImGui 的 `ImTextureID` 直接是渲染器的纹理句柄）免掉每帧把帧缓冲跨设备、跨上下文拷进控件；Qt 的 `QOpenGLWidget` 要跨上下文共享，复杂且有拷贝成本。集成接缝要用 RHI 中立类型（契约面写 `TextureHandle` 不写 `ImTextureID`），换框架时契约不必重谈。

**代价**：未记录。这条是从多 lane 项目收尾时 harvest 的选型约束。

**怎么被发现的**：收尾复盘。
