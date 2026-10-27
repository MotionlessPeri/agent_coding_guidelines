# 第 3 步：Serena 精确查引用

Serena 是 MCP 服务，底层是语言服务器（Python 用 pyright，TypeScript 用 typescript-language-server，C++ 用 clangd）。它回答「谁引用了这个符号、定义在哪」，精确到行。Claude、Codex 和接 DeepSeek、GLM 等模型的 agent 都能用。

实测同一组 40 个函数：找到调用方文件 91%、具体调用行 93%、找到的里面 98% 对；每次查 1 到 7 秒。漏掉的那几处是文本搜索多算的（docstring 里提到、别的模块同名函数）。

## 启动

注册命令见 [setup.md](setup.md)。要点：

- `--project-from-cwd`：从当前目录往上找最近的 `.serena/project.yml` 或 `.git` 当项目根。项目根要和 graphify 的导入根一致，根不对同样认不出跨文件引用。
- `--context`：Claude Code 用 `claude-code`，Codex 用 `codex`，其他 agent 用 `agent`。
- `--enable-web-dashboard false`：不然每次启动开一个浏览器页。
- 第一次激活会自动建 `.serena/project.yml`，里面 `language_servers:` 按检测到的文件填；多语言仓库看一眼有没有把 `python`、`typescript`、`cpp` 都列上，没有就手动加。
- 大仓库先 `serena project index` 建符号缓存，之后查得快。

## 接口：REPL 还是 tools

Serena 2 默认 `agent_interface: REPL`，只暴露一个 `serena_repl` 工具，让模型写 Python 调 `lsp.find_symbol(...)` 这类 API。模型写不好 REPL 调用时，启动加 `--agent-interface tools`，每个操作一个工具：`find_symbol`、`find_referencing_symbols`、`find_declaration`、`find_implementations`、`get_symbols_overview`。接手阶段只用这几个读工具。

## 用法：graphify 圈范围，Serena 逐个确认

1. 从第 1 步「最近在改」和第 2 步 `god-nodes` / `affected` 里列出要确认的符号。
2. 每个符号：`find_symbol` 定位（名字路径形如 `ClassName/method_name`），`find_referencing_symbols` 列引用，读引用处的几行确认是真调用。
3. 记下 `文件:行`。graphify 说有而 Serena 没有的，多半是文本巧合；Serena 有而 graphify 没有的，多半是别名调用。

## 坑

- `SERENA_USAGE_REPORTING=false` 必须设，见 setup。
- `.serena/` 建在项目目录里，进 `.git/info/exclude`。
- C++ 要 `compile_commands.json`（CMake 加 `-DCMAKE_EXPORT_COMPILE_COMMANDS=ON`），没有的话 clangd 只能看单文件。
- 它带编辑工具（`replace_symbol_body` 等）。接手阶段只读；要保险就在 `.serena/project.yml` 里设 `read_only: true`，开始改代码再关。
- 许可 GPL-3.0：装在本机用没有问题，不把它打包进任何要分发的东西。
