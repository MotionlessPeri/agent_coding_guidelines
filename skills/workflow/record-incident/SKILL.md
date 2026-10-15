---
name: record-incident
description: 用户说「记一条事故」「这个坑记下来」「record incident」，或会话里抓到一次值得留证据的误判并经用户同意时触发。按模板在规范库 evidence/incidents/ 写一条十行记录并挂到对应经验页，跑 lint 和 index。不用于项目内部的缺陷跟踪；带公司名、机器名、内部路径的事故记到组织叠加仓，不记到公开仓。
---

# 记一条事故

事故记录是语料库唯一的一手材料，只追加。记录不需要两击，从记录升成规则才走知识促升的门槛。

## 步骤

1. 定去处。内容里有公司名、机器名、内部路径、同事姓名，就记到组织叠加仓自己的 `evidence/incidents/`；剥掉这些仍成立的版本才进公开的规范库。拿不准先按组织仓处理。
2. 照 [`evidence/README.md`](../../../evidence/README.md) 的模板写 `evidence/incidents/<YYYY-MM>-<slug>.md`。四段各一句：现象（当时报出去或做出来的）、真因（机制一句话）、代价（造成或差一步造成的）、怎么被发现的（谁、靠什么）。`model` 和 `project` 不知道写 `unknown`，不猜。
3. 挂到页面。已有对应的经验页就把 id 加进它 frontmatter 的 `incidents`，并在事故的 `pages` 里回指；没有对应页面就让 `pages` 为空，lint 会把它列为待归类。
4. 在仓库根跑 `python scripts/kb/kb.py lint` 和 `python scripts/kb/kb.py index`，错误清零再提交。
5. 单独一条提交：`docs: 记事故 <id>`。

## 不做的事

- 不从这一条事故直接改规则或新建规范，那是另一次有意识的决定。
- 不把项目里的普通缺陷当事故：事故记的是 agent 的判断错在哪，不是代码错在哪。
- 不改旧记录的事实；要更正就新加一条引用旧 id。
