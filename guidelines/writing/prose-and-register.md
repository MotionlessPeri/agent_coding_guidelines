# 行文与用词规范（prose & register）

面向**人读的散文**的通用文体规则——不管这段散文落在哪：交付文档 / 代码注释 / 任务书 / CHANGELOG / brainstorm 结论稿。防两个反方向的失败：一边是英文夹生 + 黑话 + 冗余把读者劝退，另一边是"简洁"过头把读者照做时需要的信息删了。

这是**声明式 SoT**——具体执行面由 skill 承接：文档场景走 [`skills/workflow/doc-writing-style`](../../skills/workflow/doc-writing-style/SKILL.md)（另加图示 discipline），代码注释场景走 [`skills/workflow/conversation-walkthrough`](../../skills/workflow/conversation-walkthrough/SKILL.md) Phase 3（另加注释 stability + Doxygen 契约头）。两个 skill 都引用本条，不各自复制。

## 适用范围

| 适用 | 不适用（走各自规则） |
|---|---|
| 文档散文 / 代码注释 / 交付文字（handoff / 任务书 / 用户文档 / CHANGELOG / 结论稿） | 技术标识符（类型名 / API / 字段 / 命令——**保留原文**，见规则 1） |
| | 对话回复（走 per-project 语言偏好） |
| | commit message（走 [`workflow/commits.md`](../workflow/commits.md)：项目工作语言、单主题） |
| | 私人 memory / session log / 临时草稿 |

## 核心五条

### 1. 用项目工作语言写散文，技术标识符保留原文

- **散文 / 解释 / 流程描述**：用项目工作语言（写进项目 AGENTS.md 的 "Documentation Language Policy" 段）。
- **保留原文不翻译**：框架类型名 / API 签名 / 字段名 / SQL 关键字 / shell 命令 / UI 按钮 label / 技术缩写（DB / UI / UPROPERTY …）/ 业务专名（LineID / Choice …）/ code block 内注释。
- **判据**：这个 token 对应代码里的某个标识符 → 保留原文（强译反增查找成本）；是说人话的散文 → 用工作语言。

### 2. 不说黑话

能本地化的**业务术语**就本地化；工程界共识技术词**不强译**。**半通用的 CS 词（marshalling / parity / legacy 这类）也算黑话**——它们不像 fixture / idempotent 那样无可替代，拿不准就本地化。

### 3. 简洁

砍冗余 callout、压重复句、合并相似段、删凑数的"（详见 §X.Y）"空引用。

### 4. 不丢信息（简洁的对立约束）

简洁 ≠ 删信息。**操作必需**的内容一字不少：具体期望值、验证示例（SQL / 命令 / 输出）、文件路径、限制描述、关键看点。砍的是冗余表达，不是信息密度。

> 3 和 4 是一对张力：每删一句先问"这是冗余表达，还是读者照做时需要的事实？"——前者删，后者留。

### 5. 别要翻译腔，别压成箭头公式

- **翻译腔**：英文习语直译成中文仍不地道——"thin method → 薄方法"、"under its name → 它名下的"、"first-class → 一等公民"。用中文惯用说法（"只做一层简单包装的方法" / "属于它的"）。**判据：这句中文你会对同事当面说出口吗**？不会就是翻译腔，重写。
- **别把摘要 / 职责行压成 "A → B" 箭头公式**塞满没交代的术语。反例："端点旋转 → 名下切线手柄在切平面 orbit（每端点一个）"——读者接不住。写成完整句子，讲清"谁、做什么、（必要时）为什么"；箭头公式留给图，不留给散文。
- **项目内部自造词**（既非框架标识符、又非通用词，如某项目的 carrier / 中性 / curvenet）：保留原文没问题，但**首次出现必须 grounding**——一句话交代它指什么，别假设读者懂。文档里可开篇放个「术语表」小节（标题用「术语表」或「术语说明」，别用「先认几个词」这类口语化标题）；注释里在首次出现处一句 inline 交代。

## 黑话替换表（项目可调示例）

具体表由项目补自己的业务术语（写进项目 AGENTS.md / memory）。示例：

| 黑话 | 本地化 | | 不强译（保留） |
|---|---|---|---|
| limitation | 限制 | | fixture |
| scope | 范围 | | smoke / dry-run |
| trigger | 触发 | | stale / orphan |
| expected / actual | 期望 / 实际 | | idempotent |
| marshalling | 数据格式转换 | | |
| parity | （两边）结果一致 | | |
| legacy | 旧（X）/ 旧路径 | | |

## Anti-Patterns

| 反 pattern | 为什么错 | 修法 |
|---|---|---|
| 散文里夹生英文（"已知 limitation" / "scope 边界"） | 增加阅读门槛 | 业务术语本地化，标识符才保留原文 |
| 强译工程共识词（fixture→夹具） | 反增查找成本 | 共识技术词保留原文 |
| 半通用 CS 词当共识词保留（marshalling / parity / legacy） | 其实是可本地化的黑话 | 本地化（见替换表）|
| 英文习语直译（薄方法 / 它名下的 / 一等公民） | 翻译腔、不地道 | 中文惯用语；"能当面说出口"作判据 |
| 摘要/职责行写成 "A → B" 箭头公式 + 没交代的术语 | 读者接不住、不知所云 | 完整句子讲清谁做什么；项目自造词先 grounding |
| 项目自造词首次出现不交代 | 读者无从理解 | 首次出现一句 grounding |
| 为"简洁"删掉验证示例 / 具体期望值 | 读者照做时缺信息 | 砍冗余表达，不砍操作事实 |

## 项目 Tuning（项目可调项）

| 项 | 默认 | 项目可调 |
|---|---|---|
| 散文语言 | 无默认 | 项目工作语言，写进项目 AGENTS.md |
| 黑话替换表 | 上表示例 | 项目补自己的业务术语 |

## 相关 Guidelines / Skills

- [`guidelines/workflow/documentation.md`](../workflow/documentation.md) —— declarative 文档同步 / 拆分 / 索引 / "结论先于细节"；本条管**用词 + 句子怎么写好**，那条管**文档整体结构怎么组织**
- [`guidelines/code/function-clarity.md`](../code/function-clarity.md) Rule 2 —— 注释 **stability**（stable why vs transient when / 不引用 ephemeral 文档）；跟本条正交——那条管"注释该引用什么"，本条管"注释怎么措辞"
- [`skills/workflow/doc-writing-style/SKILL.md`](../../skills/workflow/doc-writing-style/SKILL.md) —— 文档场景执行面（本条 + 图示 discipline）
- [`skills/workflow/conversation-walkthrough/SKILL.md`](../../skills/workflow/conversation-walkthrough/SKILL.md) —— 代码注释场景执行面（本条 + 注释 stability + Doxygen 契约头）
