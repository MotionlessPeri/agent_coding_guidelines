# Documentation Guidelines

## Sync Rules

- When you gain new code understanding or design details during a session, update the
  corresponding doc immediately. Do not wait for the user to prompt you.
- When you modify code, update the doc that describes that flow in the same change.
- When you find a doc is wrong, correct it immediately — do not preserve errors.
  **例外:错误文档住在他人的备份 / 镜像 / vendored / 他队拥有的树里时,不要就地改。**
  就地改会同时毁掉两样东西:(a) 镜像的**证据价值** —— 它不再是"源机当时的样子",
  后续任何以它为基准的核对都失效;(b) 它会**静默分叉** —— 对方那份源文件不会因此
  改变,两份内容从此不同,而没人知道哪份是真的。正确动作是把勘误**路由回上游作者**
  (必要时经用户转交),镜像保持原样。
  ⚠️ 这个例外要明写,是因为**上面那条常驻规则会指示你做错的事**:要改的往往只是
  一段话,文件就在眼前且可写。
- When a new important file, class, or interface is added, update the project index.

## 会静默过期的东西：两支修法

「已写好」跟「现在还对」是两件事。而这类东西的病因不是"作者不上心",是——
**没有任何东西会因为它过期而变红。** 代码有编译器和测试兜着，散文没有。

实测两例，都发生在**改动仍在进行中**的时候：

- **commit message**：写在改动**中途**，之后又加了三件事 ⇒ 递出去时已经不覆盖实际内容。
  （它被抓住只是因为有人**要原文而不接受复述** —— 若按复述转发，过期的是复述，没人会知道。）
- **注释里的计数**：「上游有 20 个 X，这里接了三个」 ⇒ 实际是 22 和 6。两个数都错，而它们错了不影响任何测试。

### 两支修法，按"能不能配一条会红的东西"选

| 情形 | 修法 |
|---|---|
| **能配** | 给那个数字配一条会红的判据。例：「全部 18 个字段」旁边有一条断言"遍历了全部 18 个"，字段数一变就红 ⇒ **这个数字可以写**，而且它比指针有信息量（它说的是"少一个就是将来被丢掉的那个"） |
| **配不上** | **不写会过期的东西**。数字换成指针（"全部 X 见 `<那个文件>`"）—— **数字会过期，指针不会** |

⇒ 所以准确的规矩**不是**「注释里别写数字」，而是 **「没有判据撑着的数字别写」**。前者会把一批**有牙的**
数字一起否掉。

### 配不上判据时只剩一个动作，且它是最弱的一档

commit message 这类东西没法配断言 ⇒ 只能靠 **提交前重读一遍自己的消息**。
⚠️ 明知它弱也要写下来，因为**它是那一档唯一可做的事**；而"弱"的具体含义是：
它跟本仓库其他"必须做的动作"一样，**可以被自认为做过**（见
[`../../techniques/adversarial-verification.md`](../../techniques/adversarial-verification.md)
「判据才留痕」）。⇒ 递交付物给别人时，**要原文、不接受复述**，是对这一档的外部补强。

## Writing Style

- Put conclusions before details.
- Convert conversation output into structured knowledge. Avoid transcript-style notes.
- Prefer sections: `Conclusion`, `Why`, `Typical Approaches`, `Open Questions`.
- Separate general principles from project-specific choices.

## Document Splitting

- If a document covers 3 or more independent topics, split it.
- If a document exceeds roughly 200-300 lines, evaluate splitting before extending further.
- If one section needs substantial background to stay readable, move it to its own file.

## Index Maintenance

- Every new document must be registered in the project's index file in the same work step.
- When a new term may be ambiguous, add it to the project glossary (if one exists).

## Deferred Topics

- Maintain a visible queue of deferred topics in the documentation.
- Phrase deferred topics as discussable questions, not vague reminders.
- When a deferred topic is later resolved, integrate the result into formal documents.

## In-Progress Docs

- Refactoring plans and progress records should be committed during active work so
  reviewers can track progress.
- Remove or archive them in a separate cleanup commit when the work is complete.
