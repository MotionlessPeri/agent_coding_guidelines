# `_radar/` —— 外部知识雷达(暂存区,**不是**知识本体)

## 这是什么

`/research-radar` 命令的产出落点。每次跑 deep research 搜「最近热门的 coding / agent
workflow guideline + 相关工具」,把**狠过滤后的 3-5 个候选**写成一份 dated digest 存这里。

## 铁律:绝不进 `guidelines/`,绝不被 `@`-import

这个 repo 的立身原则(见 [`guidelines/workflow/knowledge-promotion.md`](../guidelines/workflow/knowledge-promotion.md)):
知识是**靠真实项目踩坑挣来的**(two-strike / hidden contract / 验证过的 discipline)。
明确**不 promote**「exploratory or unverified patterns」。

网上搜来的东西恰好相反——外部、没在你的语境验证过。所以:

- `_radar/` 的内容是 **inbox / 待审清单**,不是 corpus。
- **绝不**在 `AGENTS.md` 里写 `@_radar/...`。一旦 @-import 就会污染每个 session 的
  always-loaded context(见 [`techniques/context-budget-audit.md`](../techniques/context-budget-audit.md))。
- digest 文件本身永远不进 context,只在你主动读时才看。

## 促成(promotion)funnel —— 人工 gate

```
/research-radar
   └─> deep-research(收窄到你的 niche)
         └─> 写 _radar/YYYY-MM-DD.md(3-5 候选,每个一行 why-it-matters)
               └─> 你评审:这条戳中我真实感受过的 friction 吗?
                     ├─ 是 → 走 knowledge-promotion.md,adapt 进 guidelines/ 或 skill
                     │        (外部 idea 的「验证」= 它匹配你已经踩过的坑 / 已有的需求,
                     │         而不是「网上很火」)
                     └─ 否 → 留雷达里观察 / 丢弃
```

**关键**:从 `_radar/` 到 `guidelines/` 永远是**你**有意识的一步,不是 `/research-radar`
自动做的。命令只负责「搜 + 过滤 + 落 digest」,到此为止。

## 文件

| 文件 | 作用 |
|---|---|
| `README.md` | 本文件——政策 |
| `seen.md` | 去重账本——累积已出现过的条目,喂给下次搜索避免重复推老生常谈 |
| `YYYY-MM-DD.md` | 每次跑的 dated digest |

## 触发

当前**纯手动**:想跑就 `/research-radar`(可带焦点参数,如 `/research-radar UE5 自动化测试`)。
观察几轮 signal 质量后,若稳定有用,再考虑挂 `/schedule` 双周/月度自动跑。
