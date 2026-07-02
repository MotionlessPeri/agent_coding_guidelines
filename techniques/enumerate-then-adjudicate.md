# Enumerate-Then-Adjudicate：先机械枚举候选，再让 LLM 逐条裁决

## 核心规则

需要"找全某类东西的所有实例"时（所有 caller / 所有引用 / 所有违规点 / 所有待迁移 site / 所有实体 / 所有日期），**不要**把整份文档丢给 LLM 让它"找全 X"。改成两段：

1. **确定性方法过度召回**——先用 regex / 语义搜 / 语法 / grep / AST 查询把候选**枚举**出来，宁可误报，不要静默漏。
2. **LLM 逐条裁决**——把枚举出的候选做成显式 worklist，让 LLM 对**每一条**判"是不是真的、含义对不对"，accept / reject 各自留痕。

这样把"无界、不可见的漏"换成"有界、可量化的漏"。

## 为什么"找全"是 agent 的静默失败模式

让 LLM 直接"find all X"有一个**看不见**的失败模式：它漏掉的实例**不留任何痕迹**。

- non-event 无法审计——你永远不知道它没返回什么。
- 它有时返回得比实际少，而且是 non-deterministic 的，没有任何信号提示"这里少了"。
- "它找全了吗？"这个问题**根本不可回答**。

对比之下，机械枚举出的候选集是**有限、可枚举、可逐条 inspect** 的——LLM 不再能静默省略，每个候选都在 worklist 上必须被处置，漏掉变成一次显式的 reject（留痕），而不是一次无声的消失。

## 流程

```mermaid
flowchart LR
    A["原始文档 / 语料"] --> B["确定性过度召回<br/>regex / 语义搜 / 语法 / grep / AST"]
    B --> C["枚举候选集<br/>(宁可误报，不要静默漏)"]
    C --> D["LLM 逐条裁决<br/>real? 含义对?"]
    D --> E["确认集<br/>每条 accept/reject 留痕"]
    classDef det fill:#fff3e0,stroke:#e65100,color:#000
    classDef llm fill:#e3f2fd,stroke:#1565c0,color:#000
    class B,C det
    class D,E llm
```

关键是**反转信任顺序**（有点反直觉）：先让老派的确定性机械把问题变成有限、显式的，**再**请 LLM 来做它真正擅长的——在一个它无法悄悄跳过的枚举集上做判断。前置约束 LLM，正是它输出可信的原因。

## 为什么这是可信 check（对上四要素）

对照 [`adversarial-verification.md`](adversarial-verification.md) 的 MFIC 四要素：

- **Mechanically**——召回由机器穷举保证，不靠 LLM 的注意力或采样。要考虑的集合是**被生成的**，不是"被注意到的"。
- **Falsifiable / 逐条可审计**——"找全了吗"（不可答）变成"这里有 N 个候选，每个都有 accept / reject 裁决"（完全可查）。
- **Independent**——prefilter 与 LLM 的失败模式解耦：regex 会过度召回但不会悄悄跳过它本该匹配的形态；LLM 会拒掉误报但再也藏不住一个漏。组合体拿到 prefilter 的召回 + LLM 的精度，两套不同机制互不替代。

## 诚实的限制（也是真正的收益）

组合体**只能找到 prefilter 捞出来的东西**——prefilter 漏掉的候选，LLM 永远看不到，所以召回被 prefilter **封顶**，不是被 LLM 提高。

但这恰恰是收益所在：prefilter 的召回是一个**可测量、可刻画的数**（拿 labeled corpus 跑、或用 input-mutation 量化），而"LLM 到底找全没有"根本无从测量。你未必提高了召回，但你把一个**无界、不可见**的失败，换成了一个**有界、可量化**的失败。永远优先选那个你能给出一个数的失败模式。

## 何时用 / 何时不用

| 用 | 不用 |
|---|---|
| "找全所有 X"，且**漏掉不可见**（找全 caller / 引用 / 违规点 / 待迁移 site / 实体 / 日期 / 引文）| 候选集天然有界且很小——直接读完就行 |
| 要对每个 Y 做审计式判断（每条都要 accept / reject 留痕）| 任务是判断**单个已知对象**，不是"找全" |
| 有可用的确定性 prefilter（哪怕召回不完美，只要可测）| 没有任何确定性 prefilter 可用，且漏报本身可接受 |

## 具体做法

1. **选 prefilter**——按"X 已知的形态"选：已知文本形态用 regex（如法律引文工具 *eyecite* 就是先匹配已知引文形态）；易出现的区域用向量 / 语义搜；结构化的用语法 / classical parser / AST 查询；代码里找用途用 grep 关键字 + 继承图。
2. **让它过度召回**——刻意接受误报，以换取"不静默漏报"。
3. **把候选做成显式 worklist**——每条一个待处置项。
4. **LLM 逐条裁决**——real? 含义对? → accept / reject，每条留痕。
5. **（可选）量化 prefilter 的召回**——拿 labeled corpus 或 input-mutation 给出一个覆盖率数字，让"漏"变得有界可报。

## 跟 iterative-retrieval 的区别

[`coordination-patterns.md`](coordination-patterns.md) 的 iterative-retrieval 是"worker 自己迭代 fetch 上下文"——探索**未知的文件集**，扩大搜索面。本 pattern 相反：先用机械方法把候选集**定死、收窄、枚举**，再逐条判。两者互补——探索阶段可以 iterative-retrieval 把范围摸出来，一旦要"列全某个 X 的清单"就切到 enumerate-then-adjudicate。

## Anti-Patterns

| 反 pattern | 为什么错 | 修法 |
|---|---|---|
| 把整份文档丢给 LLM 让它"找全 X" | 漏掉的实例不留痕、不可审计、non-deterministic | 先机械枚举候选，再逐条裁决 |
| prefilter 追求精确、宁缺毋滥 | 漏报=静默失败，正是要消除的那种 | prefilter 刻意过度召回，把去误报交给 LLM |
| 候选不落成显式 worklist，让 LLM"顺手都看看" | LLM 又能静默跳过 | 每个候选是必须处置的一项，reject 也要留痕 |
| 声称"覆盖了全部"但不给数 | 不可证伪的空话 | 用 labeled corpus / input-mutation 给召回一个数 |
| 忘了 prefilter 封顶召回，以为 LLM 会补漏 | LLM 看不到 prefilter 没捞的东西 | 明确"召回上限=prefilter"，把功夫花在 prefilter 的召回上 |

## 项目实例参考

本 pattern 提炼自 pmarreck 的 [MFIC — Mechanically-Falsifiable Independent Control](https://gist.github.com/pmarreck/b30aa3ca69cb70a5526f8a63ab8c8d7e)（Section 2 例 2），essay 里给的真实世界例子是 *eyecite*（法律引文先按已知形态匹配再判定）。**尚未在本机项目里跑过一轮验证**——落地时按 [`guidelines/workflow/knowledge-promotion.md`](../guidelines/workflow/knowledge-promotion.md) 的态度，先在一个真实"找全 X"任务上用一次，确认 prefilter 的召回可测、逐条裁决确实堵住了静默漏，再当成定规。

## 相关 Guidelines / Techniques

- [`techniques/adversarial-verification.md`](adversarial-verification.md) —— "选可信 check：四要素 + oracle 判据"，本 pattern 是其一个具体落地
- [`techniques/coordination-patterns.md`](coordination-patterns.md) —— iterative-retrieval（探索未知文件集），跟本 pattern 互补
- [`guidelines/code/validation.md`](../guidelines/code/validation.md) —— "看代码对 ≠ 验证"；"让 LLM 找全" 的静默漏是同类自欺的一种
- [`guidelines/workflow/knowledge-promotion.md`](../guidelines/workflow/knowledge-promotion.md) —— 外部来源、未在项目验证的内容，落地时的态度
