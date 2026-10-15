# 证据层：事故记录

这里是本语料库唯一的一手材料：一条事故一个文件，只追加，不改写。经验页（`class: experience` 的 guideline）从这里派生，`evidence/INDEX.md` 从这里生成。执行任务时不必读这里；要判断一条经验规则该不该信、该不该退役时才来。

## 规则

- 一条事故一个文件，放 `incidents/<YYYY-MM>-<slug>.md`，`slug` 用 ASCII 短横线词。十行左右，超过二十行先问自己是不是在写规则。
- 只追加。事实写错了，新加一条记录引用旧 id 更正，不改旧文件的事实部分；错别字和链接可以改。
- 本仓公开。不写公司名、机器名、内部路径、同事姓名；带这些的事故记到组织叠加仓自己的 `evidence/`，这里只放剥掉后仍成立的版本。
- 一条事故可以被多个页面引用。页面 frontmatter 的 `incidents` 列表和事故的 `pages` 字段必须互相对得上，`python scripts/kb/kb.py lint` 检查。
- 记录事故不需要两击；从事故升成规则才走 [知识促升](../guidelines/workflow/knowledge-promotion.md) 的门槛。
- `date` 是事故发生的月份。只知道写下日期时就填写下日期，并在正文注明。

## 模板

```markdown
---
id: 2026-08-example-slug
date: 2026-08
kind: 命中
model: unknown
project: unknown
caught_by: 用户
tags: [rule-1]
pages: [guidelines/code/some-page.md]
---

**现象**：当时报出去 / 做出来的是什么。

**真因**：实际是什么，机制一句话。

**代价**：造成或差一步造成什么。

**怎么被发现的**：谁、靠什么打破的。
```

## 字段

| 字段 | 取值 |
|---|---|
| `kind` | `命中`：观察到的实例，有实际代价。`生效`：已有规则当场拦住一次误判，且错误状态留下了第三方能看见的痕迹。`提议`：从机制推演，无实例 |
| `model` | 当时干活的模型；没记录写 `unknown`，不猜 |
| `project` | 来源项目的通用代称，不写内部名；没记录写 `unknown` |
| `caught_by` | `自查` / `用户` / `外部追问` / `第三方复核` / `实验` / `事后复盘` |
| `tags` | 所属规则或主题的短标签，供索引统计，如 `rule-3` |
| `pages` | 引用本事故的页面，相对仓库根的路径 |

## 怎么记

用 skill `record-incident`，或照模板手写，然后在仓库根运行：

```powershell
python scripts/kb/kb.py lint
python scripts/kb/kb.py index
```
