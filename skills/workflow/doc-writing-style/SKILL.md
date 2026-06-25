---
name: doc-writing-style
description: 起草「交付级」文档（设计稿 / 任务书 / handoff / 用户使用文档 / brainstorm 结论稿 / CHANGELOG）时的文体 + 图示 discipline。两块——(1) 文体：用项目工作语言写散文、技术标识符保留原文、不说黑话（能本地化的业务术语就本地化、工程界共识词不强译）、简洁⇔不丢信息的张力（砍冗余 callout / 压重复，但具体期望值 / 路径 / 验证示例 / 限制描述一字不少）；(2) 图示：满足「多阶段流程 / 多分支决策 / 易漏步骤的关键操作」任一就**必须画图**不能纯文字（给了选型决策表 sequenceDiagram / flowchart / 编号列表），且图要**可移植**——按目标渲染器（GitLab / Confluence / mkdocs 等）版本写，不 hardcode 语法白名单（会过时），本地能渲染 ≠ 目标能渲染，必要时推探针实测能力边界。是 guidelines/workflow/documentation.md 的「执行面」补充：那条管何时同步 / 怎么拆 / 怎么建索引，这条管散文本身怎么写好 + 图怎么画。
when_to_use: Fires when drafting any deliverable-grade document meant for humans to read and act on — design docs, task briefs / handoffs, user-facing usage docs, brainstorm conclusion writeups, CHANGELOG / release notes, roadmaps. Covers prose register (work-language prose +原文 identifiers, de-jargon, concise-vs-complete tension) and diagram discipline (when a diagram is mandatory + renderer-portable mermaid). Pairs with guidelines/workflow/documentation.md (declarative sync/split/index rules — this skill is the "how to write the prose + draw the diagram" execution face). Skip for: throwaway scratch notes, private memory / session logs, commit messages, and chat replies (those follow their own per-project language prefs).
---

# 交付文档的文体 + 图示 discipline

起草**给人读、要照着做**的文档时套用。防的是两个反方向的失败：一边是英文夹生 + 黑话 + 冗余把读者劝退，另一边是"简洁"过头把操作必需的信息删了。

> 单项目（DialogueSystemSample，中文协作团队）提炼，apply-and-refine。语言 / 术语替换表 / 目标渲染器都是**项目可调**项。

## 触发与范围

- **触发**：起草交付级文档——设计稿 / 同事任务书 / handoff brief / 用户使用文档 / brainstorm 结论稿 / CHANGELOG / roadmap。
- **跳过**：临时草稿 / 私人 memory / session log / commit message / 对话回复（这些走各自的 per-project 语言偏好，不强制本规范）。
- **跟 [`guidelines/workflow/documentation.md`](../../../guidelines/workflow/documentation.md) 的关系**：那条 declarative，管**何时**同步 / **怎么**拆分 / **怎么**建索引 / 「结论先于细节」；本 skill 管**散文本身怎么写好 + 图怎么画**。两条配套，关系同 `function-clarity.md` ↔ `conversation-walkthrough` skill。

## 一、文体四条

### 1. 用项目工作语言写散文，技术标识符保留原文

- **散文 / 解释 / 流程描述**：用项目工作语言（本项目=中文；按项目定，写进项目 AGENTS.md 的 "Documentation Language Policy" 段）。
- **保留原文不翻译**：框架类型名 / API 签名 / 字段名 / SQL 关键字 / shell 命令 / UI 按钮 label / 技术缩写（DB / UI / AR / UPROPERTY …）/ 业务专名（LineID / Choice …）/ code block 内注释。
- 判据：这个 token 对应代码里的某个标识符 → 保留原文（强译反增查找成本）；是说人话的散文 → 用工作语言。

### 2. 不说黑话

能本地化的**业务术语**就本地化；工程界共识技术词**不强译**。项目可调一张替换表，例：

| 黑话 | 本地化 | | 不强译（保留） |
|---|---|---|---|
| limitation | 限制 | | fixture |
| scope | 范围 | | smoke / dry-run |
| trigger | 触发 | | stale / orphan |
| expected / actual | 期望 / 实际 | | idempotent |

### 3. 简洁

砍冗余 callout、压重复句、合并相似段、删凑数的"（详见 §X.Y）"空引用。

### 4. 不丢信息（简洁的对立约束）

简洁 ≠ 删信息。**操作必需**的内容一字不少：具体期望值、验证示例（SQL / 命令 / 输出）、文件路径、限制描述、关键看点。砍的是冗余表达，不是信息密度。

> 3 和 4 是一对张力：每删一句先问"这是冗余表达，还是读者照做时需要的事实？"——前者删，后者留。

## 二、图示 discipline

### 何时必须画图（不能纯文字）

满足任一就画，别用大段文字描述流程：

| 场景 | 用什么 | 为什么 |
|---|---|---|
| 多阶段流程（≥3 步且阶段间有状态依赖） | `sequenceDiagram` | 把每阶段的状态变化画出来，文字描述读者要自己脑补状态机 |
| 多分支决策（按类型 / 条件分流） | `flowchart TD` + classDef 给关键路径上色 | 分支用文字容易漏掉某条 |
| 完整链路 + 有**容易跳过的关键步骤** | `flowchart TB` + 色块高亮（橘 `fill:#fff3e0` / 红 `stroke-width:2px`） | 高亮那一步防读者漏做 |
| 简单 2-3 步顺序、无状态依赖 | **不画图**，编号列表就够 | 画图反而是过度表达 |

### 图要可移植：按目标渲染器写，别 hardcode 语法白名单

**核心教训**（踩过的坑）：渲染器版本会变——曾经把"目标卡在 mermaid 8.9.2、避开所有 9.x+ 语法"写死进文档，后来 GitLab 升到 11.x，整张白名单全部作废。所以：

1. **不在 skill / 文档里 hardcode "能用哪些语法"的白名单**（会过时）。具体版本约束留**项目侧**维护（项目 memory / AGENTS.md）。
2. **本地能渲染 ≠ 目标渲染器能渲染**。本地 IDE / VSCode preview 多是最新版，目标（GitLab / Confluence / mkdocs-mermaid …）可能落后。以**目标**为准。
3. **查目标渲染器版本**：浏览器 F12 → Network filter `mermaid` → 刷新 → 看加载的 chunk 文件名（如 `sandboxed_mermaid_v11.<hash>.chunk.js` 里的 `v11`），点开 chunk 搜 `version` 拿精确号。（注：GitLab 给 mermaid 套 sandbox iframe，console 里全局 `mermaid` 拿不到是正常的。）
4. **拿不准就推探针实测**：建一个 `mermaid-probe.md`，每段用一个版本门控特性（`flowchart` 关键字 / `mindmap` / 命名 shape `@{ shape: stadium }` …），推到目标渲染器看哪段成、哪段报红字——直接得到能力边界，比知道精确版本号更有用。

### 不分版本的稳健习惯

- 节点 label 含特殊字符（`→` `<` `>` `:`）一律双引号包裹：`A["Tools > Setup"]`——防 parser 把 `→` 跟连接符混淆。
- 强调用 `classDef` 着色，少用 inline `<b>`/`<i>`（renderer securityLevel 可能 escape）；`<br/>` 是 mermaid 内置换行可放心用。

## Anti-Patterns

| 反 pattern | 为什么错 | 修法 |
|---|---|---|
| 散文里夹生英文（"已知 limitation" / "scope 边界"） | 增加阅读门槛 | 业务术语本地化，标识符才保留原文 |
| 强译工程共识词（fixture→夹具） | 反增查找成本 | 共识技术词保留原文 |
| 多阶段流程纯文字描述 | 读者漏关键步骤（尤其手动操作步） | 按选型表画图 + 高亮易漏步 |
| 简单 2 步也画 flowchart | 过度表达 | 编号列表就够 |
| 为"简洁"删掉验证示例 / 具体期望值 | 读者照做时缺信息 | 砍冗余表达，不砍操作事实 |
| 文档里 hardcode mermaid 语法白名单 | 渲染器升级后过时 | 项目侧维护版本约束 + 探针实测 |
| 只在本地 preview 验证就推上去 | 目标渲染器可能渲不出 | 以目标渲染器为准 |

## 项目 Tuning（项目可调项）

| 项 | 本 skill 给的默认 | 项目可调 |
|---|---|---|
| 散文语言 | 中文 | 任意工作语言；写进项目 AGENTS.md |
| 黑话替换表 | 上表示例 | 项目补自己的业务术语 |
| 目标渲染器 + 版本约束 | 不 hardcode | 项目 memory / AGENTS.md 维护当前版本 + 能力边界 |
| 高亮配色 | 橘 `#fff3e0` / 红描边 | 团队配色约定 |

## 相关 Guidelines / Skills

- [`guidelines/workflow/documentation.md`](../../../guidelines/workflow/documentation.md) —— declarative 同步 / 拆分 / 索引规则；本 skill 是其「散文 + 图示执行面」补充
- [`guidelines/code/function-clarity.md`](../../../guidelines/code/function-clarity.md) —— 同形态的「写好」discipline，但对象是代码注释 / 函数结构而非文档散文
- [`skills/workflow/conversation-walkthrough/SKILL.md`](../conversation-walkthrough/SKILL.md) —— 收尾的注释体检跟本 skill 的散文规范同源（注释自包含 / stable why）
