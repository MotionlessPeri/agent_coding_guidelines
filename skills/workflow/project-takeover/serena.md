# 第 3 步：Serena 精确查引用

Serena 是 MCP 服务，底层是语言服务器（Python 用 pyright，TypeScript 用 typescript-language-server，C++ 用 clangd）。它回答「谁引用了这个符号、定义在哪」，精确到行。Claude、Codex 和接 DeepSeek、GLM 等模型的 agent 都能用。

实测同一组 40 个函数：找到调用方文件 91%、具体调用行 93%、找到的里面 98% 对；每次查 1 到 7 秒。漏掉的那几处是文本搜索多算的（docstring 里提到、别的模块同名函数）。

## 启动

注册命令见 [setup.md](setup.md)。要点：

- `--project-from-cwd`：从当前目录往上找最近的 `.serena/project.yml` 或 `.git` 当项目根。项目根要和 graphify 的导入根一致，根不对同样认不出跨文件引用。
- `--context`：Claude Code 用 `claude-code`，Codex 用 `codex`，其他 agent 用 `agent`。
- `--enable-web-dashboard false`：不然每次启动开一个浏览器页。
- **注册 MCP 之前**先在仓库根建项目并建索引，语言显式给出（不给 `--ls` 它会交互问「要不要再开别的语言」）：

  ```
  serena project create <仓库根> --ls typescript --ls python --index
  ```

  `--index` 顺带把语言服务器下载好、建好符号缓存，之后 MCP 启动快、查得快。仓库里已经有 `.serena/project.yml` 的，打开看 `language_servers:` 是不是空列表，空的就手填语言再 `serena project index <仓库根>`。
- 不要靠 MCP 首次启动来生成 `project.yml`：`--project-from-cwd` 激活没有配置的目录时走异步探测，先写一份 `language_servers: []` 落盘，探测完再改写（`serena/agent.py` 里 `add_project_from_path(..., asynchronous_autogen=True)`）。进程在这之间被结束，比如 `claude mcp list` 探活后立刻断开，文件就停在空列表；空列表下所有符号工具都报没有语言服务器。

## 接口：REPL 还是 tools

Serena 2 默认 `agent_interface: REPL`，只暴露一个 `serena_repl` 工具，让模型写 Python 调 `lsp.find_symbol(...)` 这类 API。模型写不好 REPL 调用时，启动加 `--agent-interface tools`，每个操作一个工具：`find_symbol`、`find_referencing_symbols`、`find_declaration`、`find_implementations`、`get_symbols_overview`。接手阶段只用这几个读工具。REPL 返回的 `start_line` / `end_line` 和引用处的行号都从 0 起，记成 `文件:行` 时加 1。

## 用法：graphify 圈范围，Serena 逐个确认

1. 从第 1 步「最近在改」和第 2 步 `god-nodes` / `affected` 里列出要确认的符号。
2. 每个符号：`find_symbol` 定位（名字路径形如 `ClassName/method_name`），`find_referencing_symbols` 列引用，读引用处的几行确认是真调用。
3. 记下 `文件:行`。graphify 说有而 Serena 没有的，多半是文本巧合；Serena 有而 graphify 没有的，多半是别名调用。

## 连不上

会话里 Serena 工具不出现或报连接超时，按顺序查，查完重开会话，不在当前会话里等：

1. `.serena/project.yml` 的 `language_servers` 是否为空（成因见上）。实测一次：空列表时会话内 MCP 报 `CONNECT_TIMEOUT`，填上 `[typescript]` 并 `serena project index` 后 `claude mcp list` 报 Connected；没做单变量验证，空列表和下面第 2 条可能同时在起作用。
2. 第一次启动要下载语言服务器，可能超过宿主的 MCP 启动超时。先用 `serena project create ... --index` 或 `serena project index` 在命令行把它下完。
3. 本会话中途才注册或才修好的 MCP，Claude Code 和 Codex 都不会在当前会话里出现，要重开会话。所以这一整步的准备都放在开 lane 之前，由开 lane 的人在仓库目录做好。
4. 会话刚开的头几秒 MCP 还在连，这时搜工具清单会说没有 serena；等几秒再搜，不要当成没注册。

改后的路线新会话实测通过（2026-10-28）：仓库里 `language_servers: [typescript]`、建过索引、MCP 以本地作用域注册，在该目录新开一个 Sonnet 会话只做第 3 步，`serena_repl` 几秒内出现，`find_symbol` 定位到类定义，`find_referencing_symbols` 返回 12 个文件 27 处引用，整个会话 44 秒、7 个回合。

## 坑

- `SERENA_USAGE_REPORTING=false` 必须设，见 setup。
- `.serena/` 建在项目目录里，进 `.git/info/exclude`。
- C++ 要 `compile_commands.json`（CMake 加 `-DCMAKE_EXPORT_COMPILE_COMMANDS=ON`），没有的话 clangd 只能看单文件。
- 它带编辑工具（`replace_symbol_body` 等）。接手阶段只读；要保险就在 `.serena/project.yml` 里设 `read_only: true`，开始改代码再关。
- 许可 GPL-3.0：装在本机用没有问题，不把它打包进任何要分发的东西。
