---
id: 2026-08-directory-skeleton-mistaken-for-source
date: 2026-08
kind: 命中
model: unknown
project: ue
caught_by: 自查
tags: [rule-3, 镜像形态]
pages: [guidelines/code/reporting-limits-and-null-results.md]
---

**现象**：检查三个第三方依赖在不在，`ls -d` 三个目录全部存在，差一步报「依赖齐全，问题在别处」。

**真因**：发行版裁剪掉了源码，只留下目录骨架和许可证文件；许可要求文件必须留着，所以骨架一定在。「容器在」是系统性的假阳性，不是偶然。这是规则 3 的镜像：在场被误读成完整。

**代价**：差一步把问题推到别处。

**怎么被发现的**：往里再查一层具体的物。
