---
name: project-takeover
description: 用户说「接手这个项目」「接手仓库」「别人做到一半的代码」「摸清这个仓库」「take over」，或 lane 被派去接手一个自己没写过的仓库时触发。固定五步：盘点现状（分支、未提交、最近提交、TODO、已有交接文档）→ graphify 建代码图 → Serena 查引用 → OpenWiki 宿主模式写 wiki → 知识库记接手总览。工具全在本机跑、不配模型密钥；生成物留本地，不经用户同意不提交进别人的仓库。不用于自己一直在写的仓库，也不用于只改一处的小修。
---

# 接手项目

接手要回答两个问题：**代码现在是什么样**，**上一个人做到哪了**。三个工具只回答第一个，第二个靠第 1 步自己做。顺序固定：盘点 → 代码图 → 查引用 → 写 wiki → 记总览；每步末尾的判据决定能不能进下一步。

工具没装或 MCP 没注册，先按 [setup.md](setup.md) 装，一台机器装一次。三个工具都是外部软件，版本钉在 setup 里；它们的 `--help` 和自带说明是事实源，附件只写查不到的坑。

## 1. 盘点现状

照 [inventory.md](inventory.md) 跑一遍 git 和仓库检索，先找仓库里已有的交接文档和实施计划，再写成一页「现状盘点」。

完成判据：没合的分支、未提交和 stash、最近提交在改什么、TODO 与 FIXME 集中在哪、已有交接文档和计划、能否构建并跑通测试，六项每项都有结论或写明「没查到」。

## 2. graphify：全局代码图

照 [graphify.md](graphify.md) 从代码的**导入根目录**建图，排除第三方目录和压缩文件；不跑 `graphify install`。

完成判据：`graphify-out/graph.json` 与 `GRAPH_REPORT.md` 存在；`god-nodes --top 20` 里实现代码的节点没有标准库和第三方名字（`vitest`、`pytest` 这类测试框架名来自 tests，跳过不算）；第 1 步里最近在改的模块能在图里找到。

## 3. Serena：精确查引用

照 [serena.md](serena.md) 启动 Serena，对第 1 步「最近在改」和第 2 步核心节点里的符号逐个查定义与引用。graphify 先粗圈影响范围，Serena 逐个确认。会话里没有 Serena 工具或连不上，按 serena.md「连不上」处理后重开会话，不在会话里绕路。

完成判据：对每个要动的符号，能说出引用它的文件和行；graphify 圈出的范围被 Serena 确认过或缩小过。

## 4. OpenWiki：写 wiki

照 [openwiki.md](openwiki.md) 用宿主模式生成，由当前 lane 的模型读代码写页；核心模块读实现，页数按代码量定。

完成判据：`openwiki_finish` 返回 `complete`；`openwiki/quickstart.md` 存在；`.github/workflows/openwiki-update.yml` 已删；`AGENTS.md` / `CLAUDE.md` 里 OpenWiki 写的那段按项目规矩处理过；生成物没进暂存区。

## 5. 知识库：接手总览

有 lane-router 知识库（`lane_kb_search` / `lane_kb_record`）的环境，用 `lane_kb_record` 建一页「<仓库名> 接手总览」，正文第一行写 `asOf: <YYYY-MM-DD>，commit <短 sha>`，然后是现状盘点的结论、wiki 入口路径、代码图路径、盘点和写 wiki 时发现的疑点。没有知识库的环境跳过，把同样内容并进现状盘点那一页。

完成判据：`lane_kb_search` 能搜到这页；页里每个路径都能打开；提交号与仓库 `git rev-parse HEAD` 一致。

## 约定

- 生成的 wiki 不手改。写错了就改源码注释或文档后重新生成，或把更正记进知识库。
- 更新 wiki 在新会话里跑。接着生成会话跑，上下文越滚越贵：实测一次更新花了生成那次八成的额度。
- 生成物（`openwiki/`、`graphify-out/`、`.serena/`，以及 OpenWiki 改的 `AGENTS.md`）留在本地；用户点头后才提交或推送到别人的仓库。
- lane-router 的图（`lane_graph_*`）只放人整理过的几十个节点的架构概览；整张代码图留在 `graphify-out/`，查调用用 graphify 和 Serena。
- 盘点和 wiki 都是某个提交时的快照，总览页写明提交号；用之前对照当前代码。
