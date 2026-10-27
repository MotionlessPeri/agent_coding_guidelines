# 第 2 步：graphify 建全局代码图

graphify 用 tree-sitter 解析代码建图，回答「模块怎么分群、哪些是核心节点、改这里波及哪」。代码部分不调模型、不花 token。

## 根目录：从代码的导入根建

`graphify extract <根>` 的 `<根>` 要是代码**导入时的根**，不是仓库根也不是你关心的子目录：

- Python：`from app.core import x` 能成立的那一层，也就是装着顶层包 `app/` 的目录。
- 单仓多产品：挑要接手的那个产品的根，分别建图。

根选错的症状：跨文件调用全认不出，`explain` 一个明知被广泛调用的函数只列出同文件的几个邻居。实测把一个子目录单拆出来建图，调用方召回从 87% 掉到 57%，三个工具一起掉。

## 排除第三方和压缩文件

在根目录放 `.graphifyignore`，gitignore 语法，和 `.gitignore` 叠加（只能多排除，不能重新包含）：

```
third_party/
vendor/
node_modules/
**/*.min.js
**/vendor/**
```

不排除的后果：打包进仓库的三维库、压缩 JS 的短变量名会占掉大半模块群，`god-nodes` 前排全是 `sys`、`numpy`、`json`。

## 建图

```
graphify extract <根> --code-only          # 只解析代码，不调模型；写 <根>/graphify-out/
graphify cluster-only <根> --no-label      # 分群并生成 GRAPH_REPORT.md，群名是 Community N
```

超过 5000 个节点时 `graph.html` 自动改成按群聚合的视图；不需要可加 `--no-viz`。

要群名能读（「相机采集源」而不是「Community 17」），用本机 `claude` 命令起名，花当前订阅额度：

```
graphify label <根> --backend=claude-cli
```

实测 7 万行给 263 个群起名约 15 万 token、不到 2 分钟。不传 `--code-only` 的 `extract` 还会让模型读文档和图片抽概念，7 万行的 16 篇文档约 61 万输入 token；接手时不急着做。

参考耗时（不调模型）：28 万行、1329 个代码文件全量 2 分 25 秒，2.35 万节点，`graph.json` 25 MB。

## 查

命令默认找当前目录下的 `graphify-out/graph.json`，不在根目录就带 `--graph <根>/graphify-out/graph.json`。

```
graphify god-nodes --top 20              # 架构枢纽；前排出现标准库名说明排除没做好
graphify explain "ClassOrFunction"       # 一个节点和它的邻居，带文件和行号
graphify affected "ClassOrFunction" --depth 2   # 改它波及谁；设计文档、交接文档里提到它的也会列出
graphify query "how does X get Y"        # 关键词定位后做 BFS，输出限 2000 token
graphify path "A" "B"                    # 两个节点之间的最短路
```

名字有歧义时退出码 3 并列出候选，用 `文件路径::符号` 或候选里的完整 id 再查一次；没匹配退出码 4。每次查约 5 秒，大头是读 JSON。

## 它漏什么

- 「`import xxx as 别名` 再 `别名.func()`」这种调用认不出。同一组 40 个函数：找到调用方文件 87%，找到具体调用行 66%（同一函数里多次调用只记一条），找到的里面 99% 对。
- 所以它给的是范围，不是清单。**要动的符号逐个用 Serena 确认**，见 [serena.md](serena.md)。

## 更新与 MCP

- 代码改了：`graphify update <根>`，不调模型，缓存命中约 85%。重新分群会把群重新编号，起过的名字用 `graphify label <根> --missing-only` 补。
- MCP（可选，lane 想在对话里直接查时）：`graphify-mcp <根>/graphify-out/graph.json`，stdio，工具有 `query_graph`、`get_node`、`get_neighbors`、`get_community`、`god_nodes`、`graph_stats`、`shortest_path`。注册方法见 [setup.md](setup.md)。
- `graphify-out/` 进 `.git/info/exclude`。
