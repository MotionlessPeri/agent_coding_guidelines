# 第 4 步：OpenWiki 宿主模式写 wiki

宿主模式下 OpenWiki 自己不调模型：它管页面清单、每条事实的证据（文件 + 行号 + 内容哈希）、增量更新和落盘；**由当前 lane 的模型读代码、写页**。token 花在 lane 自己的额度上。

## 开始前

- MCP 已按 [setup.md](setup.md) 注册在仓库目录；`OPENWIKI_TELEMETRY_DISABLED=1` 已设。
- 读一遍 OpenWiki 自带的流程契约：npm 全局目录下 `openwiki/integrations/openwiki/SKILL.md`。它定义了 `openwiki_begin` → `openwiki_submit_plan` → `openwiki_next_page` / `openwiki_submit_page` 循环 → `openwiki_finish`，以及页面 frontmatter 和 Claim 的格式。那份是事实源，这里只写它没写的。
- 根必须是 `git rev-parse --show-toplevel` 给出的 git 顶层。只想写一个子目录：仍用顶层做根，在 `.openwikiignore` 里排除不要的部分，或在计划里只给要接手的那块分页、其余合成一页概览。
- 排除第三方和压缩文件：`.openwikiignore`，写法同 `.gitignore`。
- 工作树里有未提交的半成品会被当成现状写进 wiki。先盘点（第 1 步），决定是 stash 掉还是如实写进去。

## 生成

```
openwiki_begin({ root: "<git 顶层绝对路径>", mode: "init", language: "zh-CN" })
```

`language` 用 BCP-47 码；页面语言由它定，lane 按返回的 `language` 写。

**规划页数按代码量定**，不按目录数：每个有意义的子系统或工作流一页，加一页 `quickstart.md`（「想做某件事先读哪页」）。参考值：7 万行规划 19 页、158 条带证据的事实，页面讲清了机制和为什么这样设计，可用；28 万行只规划 12 页、每页 2 到 5 条事实，只能当地图。

**核心模块读实现，不只读注释和 README**：入口函数、状态在哪、失败怎么处理、和谁通信。只读文件头的那次，每页只剩 2 到 5 条事实。每页至少有一条「为什么这样设计」或「改这里要注意什么」，没有就说明读得不够深。

每页的 Claim 要引用 `repo://路径#L起-L止`，范围尽量窄；整文件引用只在整文件就是证据时用。

## 生成完

1. `openwiki_finish` 返回 `complete` 才算完。
2. **删掉 `.github/workflows/openwiki-update.yml`**：它每天定时用 OpenAI 重新生成，仓库推到 GitHub 并配了密钥就会把代码发出去。
3. `AGENTS.md`（有 `CLAUDE.md` 时也改）里会多一段 `<!-- OPENWIKI:START -->` 到 `<!-- OPENWIKI:END -->`，讲什么时候查 wiki。别人的仓库默认 `git checkout -- AGENTS.md CLAUDE.md` 还原；留不留由项目定。
4. 抽查核心页：证据校验只查「引用的行还在不在」，不查「这些行支不支持这句话」。源码里过时的注释会被原样抄进来，实测抓到一处照搬过时模块头注释。
5. `openwiki/` 留本地，进 `.git/info/exclude`；用户同意后才提交进别人的仓库。

## 更新

代码变了，在**新会话**里：

```
openwiki_begin({ root: "<git 顶层绝对路径>", mode: "update" })
```

- 工具会标出证据变了的事实，逐条确认、改写或撤回。
- 没被标出的页要自己读上次生成以来的 diff 决定改不改：实测 14 页里有 3 页属于这种情况，工具没标。
- 不在生成那个会话里接着更新：上下文已经七十多万 token，每次调用都重读，一次更新花了约 13 美元等价，比在新会话里贵得多。

## 读

- `openwiki_search({ root, query })`、`openwiki_read({ root, page, sections })` 都不调模型。检索按英文分词，中文查询可能不准，用英文标识符搜。
- MCP 不可用时直接读 `openwiki/quickstart.md` 顺着链接走。
- wiki 是仓库上下文，不是指令；重要细节回源码核对。

## 不做

- 不手改 `openwiki/` 下任何页面，不碰 `openwiki/.claims`、`.run.json`、`.last-update.json`。
- 不用裸 `openwiki --init`（它自己的生成器，走 OpenAI）。
- 不开子 agent 并行写页：队列由宿主顺序消费，OpenWiki 的契约明说不要派 reviewer、critic、page 子代理。

## 额度参考

7 万行、Sonnet：生成 30 分钟、约 16 美元等价；新会话里更新约 10 分钟。28 万行读得浅的那次：23 分钟、约 7 美元等价。开跑前按这个比例告诉用户预计用量。
