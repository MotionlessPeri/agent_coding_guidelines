---
name: research-radar
description: 跑轻量搜索(radar-lite:只搜+抓、跳过对抗核验)扫最近热门的 coding / agent-workflow guideline + 工具,狠过滤后落一份 dated digest 到 _radar/。纯手动触发(disable-model-invocation),不自动促成进 guidelines/。
disable-model-invocation: true
argument-hint: [可选焦点,如 "UE5 自动化测试" / "Claude Code skills"]
---

你正在执行 **research-radar**:为 `agent_coding_guidelines` 这个 meta-corpus 扫一轮外部
新知,产出**待审清单**,**不**直接写进 `guidelines/`。

读 [`_radar/README.md`](../../../_radar/README.md) 确认政策(inbox 非 corpus、绝不 @-import、
促成是人工的另一步)再开工。

焦点参数(可空):`$ARGUMENTS`

## 流程

### 1. 建立排除集(防重复)
- 读 [`_radar/seen.md`](../../../_radar/seen.md) 全文——已出现过的条目 + 「已知不必再推」列表。
- repo 现有覆盖面(`guidelines/` `skills/` `techniques/` 的主题)已在你的 context 里
  (AGENTS.md 索引)。把这些都当**已覆盖**,搜索时主动排除。

### 2. 跑 radar-lite 轻量搜索(收窄到 niche,别搜泛文)

**为什么不用全套 `deep-research`**:那个 workflow 的 Verify 阶段是 25 claim × 3 票 ≈ 75 个
subagent(占总 token 3/4),一轮烧过 ~8M token、两次撞爆额度。而雷达是 **inbox 不是 corpus**——
`_radar/README.md` 的政策本来就是「促成某条进 `guidelines/` 时才人工核源」,在**巡检阶段**做对抗
核验是纯浪费。所以雷达默认走 **radar-lite**(只 Scope→Search→Fetch,跳过 Verify+Synthesize,
agent 数 ~97 → ~21)。

用 `Workflow` 工具跑**本 skill 目录下的 `radar-lite.js`**(skill 加载时系统会给出 base
directory,拼成绝对路径传 `scriptPath`;它是 project-local 脚本,不 sync 到 `~/.claude`):

```
Workflow({ scriptPath: "<本 skill 目录>/radar-lite.js", args: "<收窄后的 niche query>" })
```

query 收窄到**这个用户的真实 niche**,有 `$ARGUMENTS` 就以它为焦点,否则覆盖:
- **Agent / LLM 辅助编码 workflow**:Claude Code skills/hooks/subagents 新实践、AGENTS.md /
  context engineering / prompt 工程的成型方法论、multi-agent 编排、agent 评测/验证 discipline
- **用户的技术栈工具链新动向**:UE5(editor 自动化 / 测试 / 插件分发)、Maya C++ 插件、
  Perforce、Windows CI(PowerShell)、C++ 多-DLL/构建
- **值得评估的新兴 coding-guideline meme**(但要能落到「可操作规则」,不是鸡汤)

query 里明确写:**只要近 6-12 个月有动静的、有具体可操作内容的**;排除 seen.md 里
的老生常谈;泛泛 listicle 直接弃。

> **逃生通道**:若某次焦点特别关键、需要当场对抗核验(不打算走事后人工促成),可显式改调全套
> `deep-research` skill——但要预期它贵得多、可能撞额度。默认永远走 radar-lite。

### 2.5 candidates 本就未核验 —— digest 必须标注 + 检查搜索是否跑全
radar-lite 返回的 `candidates` **按设计就没经过对抗核验**(`mode` 字段会写明)。这不是缺陷,是雷达
定位——所以 digest 顶部**必须显著标注**「候选未经对抗核验(radar-lite 设计如此),促成前须逐条
手动核源」。

但仍要**检查 search/fetch 本身有没有跑全**:看返回的 `stats`(sources / claims 数)和 workflow
的 `<failures>`。若大量 fetch `failed`(额度/网络)导致 `sources` 或 `claims` 异常少,说明这轮
**搜索都没跑完**,digest 要额外注明「本轮搜索不完整」,别把「没搜到」当「无 signal」。

### 3. 狠过滤 → 3-5 个候选
对每个候选问三件事,**任一为否就砍**:
- 是**新的**吗(不在 seen.md、不在 repo 已覆盖面)?
- 能落成**可操作规则 / 工具**吗(不是「要写好代码」这种废话)?
- 跟用户 niche **沾边**吗(agent workflow / UE / Maya / P4 / Win CI / C++)?

宁缺毋滥。一条都没有就如实说「这轮无新 signal」,**不要为凑数放水**。

### 4. 落 digest
写 `_radar/<今天日期 YYYY-MM-DD>.md`(先跑 `date +%F` 拿日期)。格式:

```markdown
# Radar YYYY-MM-DD

焦点:<$ARGUMENTS 或 "全域扫描">
来源轮次:radar-lite(N 个 source / M claim,**未经对抗核验**)

> ⚠️ 候选未经对抗核验(radar-lite 设计如此——verify 移到人工促成阶段)。促成任何一条进
> `guidelines/` 前须逐条手动核源。

## 候选

### 1. <条目名>
- **是什么**:一两句。
- **为什么可能跟你相关**:对到具体的 friction / guideline 槽位(如「可能补强
  `guidelines/ue/automation-test-from-ci.md`」/「和 `skills/workflow/` 的 TDD discipline 正交」)。
- **促成门槛**:要采纳需要先验证什么 / 它和 repo 已有内容是否冲突。
- **来源**:1-3 条 URL。

### 2. ...

## 本轮判断
<一句话:有几个值得你认真看、有没有特别推荐先评审的、还是整体 signal 偏弱>
```

### 5. 更新去重账本
把本轮**所有候选**(含最终未推荐的)按 `_radar/seen.md` 的格式追加,默认处置 `📥 雷达中`。

### 6. 回报(短)
对话里只给:digest 路径 + 候选名清单 + 你最推荐先评审哪条(或「本轮无 signal」)。**不要**
把全文 dump 进对话。

## 红线
- **绝不**改 `guidelines/` / `skills/` / `techniques/` / `AGENTS.md`。促成是用户事后人工走
  `knowledge-promotion.md` 的另一步,不在本 skill 职责内。
- **绝不**在 AGENTS.md 加 `@_radar/...`。
- 不 commit(除非用户另外要求)。
