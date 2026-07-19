---
name: doc-writing-style
description: 起草「交付级」文档（设计稿 / 任务书 / handoff / 用户使用文档 / brainstorm 结论稿 / CHANGELOG）时用——两块 discipline：(1) 文体，应用 prose-and-register（工作语言写散文 / 标识符保留原文 / 不说黑话 / 简洁不丢信息 / 不翻译腔 / 自造词首次 grounding）；(2) 图示，「多阶段流程 / 多分支决策 / 易漏关键步」任一就必须画图，且图要可移植（按目标渲染器版本写、不 hardcode 语法、必要时探针实测）。对话回复 / commit message / 私人草稿不适用（各走自己规则）。是 guidelines/writing/prose-and-register.md（文体 SoT）+ guidelines/workflow/documentation.md（文档结构）的文档场景执行面。
---

# 交付文档的文体 + 图示 discipline

起草**给人读、要照着做**的文档时套用。防的是两个反方向的失败：一边是英文夹生 + 黑话 + 冗余把读者劝退，另一边是"简洁"过头把操作必需的信息删了。

> 单项目（DialogueSystemSample，中文协作团队）提炼，apply-and-refine。语言 / 术语替换表 / 目标渲染器都是**项目可调**项。

## 触发与范围

- **触发**：起草交付级文档——设计稿 / 同事任务书 / handoff brief / 用户使用文档 / brainstorm 结论稿 / CHANGELOG / roadmap。
- **跳过**：临时草稿 / 私人 memory / session log / commit message / 对话回复（这些走各自的 per-project 语言偏好，不强制本规范）。
- **跟 declarative guideline 的关系**：文体规则本身在 [`guidelines/writing/prose-and-register.md`](../../../guidelines/writing/prose-and-register.md)（跨「文档 + 代码注释」共享的 SoT）；[`guidelines/workflow/documentation.md`](../../../guidelines/workflow/documentation.md) 管**何时**同步 / **怎么**拆分 / **怎么**建索引 / 「结论先于细节」。本 skill = 前者在文档场景的应用 + 图示 discipline。关系同 `function-clarity.md` ↔ `conversation-walkthrough` skill。

## 一、文体：遵循 prose-and-register，文档场景加两点

**文体规则本身在 [`guidelines/writing/prose-and-register.md`](../../../guidelines/writing/prose-and-register.md)**——工作语言写散文 + 标识符保留原文 / 不说黑话（业务术语本地化、工程共识词不强译、半通用 CS 词也算黑话）/ 简洁 ⇔ 不丢信息的张力 / 别要翻译腔·别压箭头公式 / 项目自造词首次出现先 grounding。那条是跨「文档 + 代码注释」共享的 SoT，起草文档前先过一遍。本 skill 不复制这些规则，只在其上加两点文档场景的应用：

1. **项目自造词开篇术语表 grounding**：文档比注释更依赖统一上下文——读者需要一次性看懂术语。guideline 要求首次出现的自造词（carrier / 中性 / curvenet 这类）grounding，文档场景把它落成**开篇一个「术语表」小节**（词 → 一句话释义，通常一张两列小表），别散落到正文各处才解释。**标题就用「术语表」（或「术语说明」），不要用「先认几个词」这类口语化标题——交付文档要读着正式。**
2. **黑话替换表落到项目**：guideline 给了示例表，具体表由项目补自己的业务术语（写进项目 AGENTS.md / memory）。

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
- **`classDef` 设了 `fill` 就必须同时设深色 `color:` 文字色**——别只给浅色 fill 靠 renderer 默认文字色。很多目标渲染器（GitLab / 某些主题）默认字是浅灰，**浅底 + 浅灰字读不清**。例：`classDef hi fill:#fff3e0,stroke:#e65100,color:#000`。`stroke` 也一并给，描边比纯底色更稳地标出关键路径。

## Anti-Patterns

> 文体反 pattern（夹生英文 / 强译共识词 / 翻译腔 / 箭头公式 / 为简洁删信息）见 [`guidelines/writing/prose-and-register.md`](../../../guidelines/writing/prose-and-register.md)。下面是文档 / 图示专属的：

| 反 pattern | 为什么错 | 修法 |
|---|---|---|
| 项目自造词首次出现不在开篇术语表交代 | 读者无从理解、正文各处才解释 | 开篇「术语表」小节一句话 grounding |
| 术语表用「先认几个词」这类口语化标题 | 交付文档读着不正式、不像正常文档 | 标题用「术语表」（或「术语说明」）|
| 多阶段流程纯文字描述 | 读者漏关键步骤（尤其手动操作步） | 按选型表画图 + 高亮易漏步 |
| 简单 2 步也画 flowchart | 过度表达 | 编号列表就够 |
| 文档里 hardcode mermaid 语法白名单 | 渲染器升级后过时 | 项目侧维护版本约束 + 探针实测 |
| 只在本地 preview 验证就推上去 | 目标渲染器可能渲不出 | 以目标渲染器为准 |
| `classDef` 只设 `fill` 不设 `color` | 浅底 + renderer 默认浅灰字 → 读不清 | fill 必配深色 `color:` + `stroke` |

## 项目 Tuning（项目可调项）

| 项 | 本 skill 给的默认 | 项目可调 |
|---|---|---|
| 目标渲染器 + 版本约束 | 不 hardcode | 项目 memory / AGENTS.md 维护当前版本 + 能力边界 |
| 高亮配色 | 橘 `#fff3e0` / 红描边，且 fill 必配深色 `color:`（如 `#000`） | 团队配色约定 |

> 散文语言 / 黑话替换表的 tuning 移到 [`guidelines/writing/prose-and-register.md`](../../../guidelines/writing/prose-and-register.md)。

## 相关 Guidelines / Skills

- [`guidelines/writing/prose-and-register.md`](../../../guidelines/writing/prose-and-register.md) —— 文体规则本身（工作语言 / 不说黑话 / 简洁⇔不丢信息 / 不翻译腔）；本 skill 是它在文档场景的执行面 + 图示 discipline
- [`guidelines/workflow/documentation.md`](../../../guidelines/workflow/documentation.md) —— declarative 同步 / 拆分 / 索引规则；本 skill 是其「散文 + 图示执行面」补充
- [`guidelines/code/function-clarity.md`](../../../guidelines/code/function-clarity.md) —— 同形态的「写好」discipline，但对象是代码注释 / 函数结构而非文档散文
- [`skills/workflow/conversation-walkthrough/SKILL.md`](../conversation-walkthrough/SKILL.md) —— 收尾的注释体检跟本 skill 共用同一份 prose-and-register（注释场景执行面）
