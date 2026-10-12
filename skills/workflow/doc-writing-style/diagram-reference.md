# 图示选择与渲染参考

本页提供表达方法与渲染经验，只有决定使用图示或排查渲染问题时才需要。图示是否必要由读者任务和项目要求决定，不以步骤数量直接强制。

| 要表达什么 | 可选形式 |
|---|---|
| 参与者之间的时序与状态变化 | sequenceDiagram |
| 条件分支与回退路径 | flowchart |
| 简单操作顺序 | 编号列表 |
| 并列方案或字段映射 | 表格 |

## 渲染知识与验证

**核心教训**（踩过的坑）：渲染器版本会变——曾经把"目标卡在 mermaid 8.9.2、避开所有 9.x+ 语法"写死进文档，后来 GitLab 升到 11.x，整张白名单全部作废。所以：

1. **不在 skill / 文档里 hardcode "能用哪些语法"的白名单**（会过时）。具体版本约束留**项目侧**维护（项目 memory / AGENTS.md）。
2. **本地能渲染 ≠ 目标渲染器能渲染**。本地 IDE / VSCode preview 多是最新版，目标（GitLab / Confluence / mkdocs-mermaid …）可能落后。以**目标**为准。
3. **查目标渲染器版本**：浏览器 F12 → Network filter `mermaid` → 刷新 → 看加载的 chunk 文件名（如 `sandboxed_mermaid_v11.<hash>.chunk.js` 里的 `v11`），点开 chunk 搜 `version` 拿精确号。（注：GitLab 给 mermaid 套 sandbox iframe，console 里全局 `mermaid` 拿不到是正常的。）
4. **已有发布授权且确需目标实测时使用小探针**：建一个 `mermaid-probe.md`，每段用一个版本门控特性（`flowchart` 关键字 / `mindmap` / 命名 shape `@{ shape: stadium }` …），推到目标渲染器看哪段成、哪段报红字——直接得到能力边界，比知道精确版本号更有用。

## 可读性建议

- 节点 label 含特殊字符（`→` `<` `>` `:`）一律双引号包裹：`A["Tools > Setup"]`——防 parser 把 `→` 跟连接符混淆。
- 强调用 `classDef` 着色，少用 inline `<b>`/`<i>`（renderer securityLevel 可能 escape）；`<br/>` 的表现也以目标渲染器验证为准。
- **`classDef` 设了 `fill` 就必须同时设深色 `color:` 文字色**——别只给浅色 fill 靠 renderer 默认文字色。很多目标渲染器（GitLab / 某些主题）默认字是浅灰，**浅底 + 浅灰字读不清**。例：`classDef hi fill:#fff3e0,stroke:#e65100,color:#000`。`stroke` 也一并给，描边比纯底色更稳地标出关键路径。
