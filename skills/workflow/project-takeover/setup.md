# 安装与注册：按机器装一次

三个工具都是本机命令行程序，不配任何模型密钥。写 wiki 用的是当前 lane 的模型和额度。另一台机器要再装一遍。

## 版本钉死

| 工具 | 版本 | 装法 | 验证 | 许可 |
|---|---|---|---|---|
| graphify | 0.9.96 | `uv tool install "graphifyy==0.9.96"`（PyPI 包名是 `graphifyy`，命令是 `graphify`） | `graphify --version` | Apache-2.0 |
| Serena | 2.1.0 | `uv tool install "serena-agent==2.1.0"` | `serena --version` | GPL-3.0，只在内部用，不再分发 |
| OpenWiki | 0.7.2 | `npm install -g openwiki@0.7.2` | `npm ls -g openwiki` | MIT |

前提：`uv`（Python 3.12 以上）、Node.js 22 以上、git。`uv tool` 装的命令在 `~/.local/bin`，不在 PATH 就跑 `uv tool update-shell` 或手动加。

钉版本的原因：graphify 几乎天天发版，`graph.json` 格式还在变；换版本后重建图，不迁移旧图。升级三者任何一个，先在一个公开小仓库上把五步重走一遍，再改这里的版本号。

## 关掉上报

| 工具 | 做法 | 来源 |
|---|---|---|
| Serena | 用户环境变量 `SERENA_USAGE_REPORTING=false` | 代码 `serena/agent.py` 只认这一个变量；文档没写。它每次启动往作者服务器报一次系统、版本和模式 |
| OpenWiki | 用户环境变量 `OPENWIKI_TELEMETRY_DISABLED=1`，另写进 `~/.openwiki/.env` | 它默认向 PostHog 发使用统计 |
| graphify | README 声明无遥测；查询日志写在本机 | 顺手设 `DO_NOT_TRACK=1` 不亏 |

## 不跑的命令

- `graphify install`、`graphify claude install`、`graphify hook install`：往 Claude Code 装拦截 `Grep`/`Read` 的钩子，往 `CLAUDE.md`/`AGENTS.md` 写段落，往仓库装 git 钩子。只用它的 CLI 和 `graphify-mcp`。
- 裸 `openwiki` / `openwiki --init`：那是它自己的 TUI 生成器，默认走 OpenAI，要密钥且会把代码发出去。只用 `openwiki mcp`（宿主模式）。
- `openwiki integrations install <host> --project <dir>`：能用，但它会往目标仓库写 `.agents/skills/openwiki/` 或 `.claude/skills/openwiki/` 和一份 MCP 配置。接别人的仓库时手动注册，不往仓库里添文件。

## 注册 MCP：按项目目录，本地作用域

Serena 和 OpenWiki 都要绑定具体仓库，所以在该仓库目录里注册、只对该目录生效。

先把 Serena 的项目配置和索引建好，再注册（原因见 [serena.md](serena.md)「连不上」）：

```
serena project create <仓库根> --ls typescript --index      # 语言按仓库给，可多个 --ls
```

仓库里已有 `.serena/project.yml` 的，先看 `language_servers:` 非空。

**Claude Code**（`--scope local` 写进 `~/.claude.json` 的项目条目，不进仓库，不需要别人批准）。bash / zsh / pwsh 7.3 以上：

```bash
cd <仓库根>
claude mcp add --scope local serena -- serena start-mcp-server --context claude-code --project-from-cwd --enable-web-dashboard false
claude mcp add --scope local openwiki -e OPENWIKI_TELEMETRY_DISABLED=1 -- openwiki mcp --host claude
claude mcp add --scope local graphify -- graphify-mcp graphify-out/graph.json   # 可选，建完图以后
claude mcp list
```

Windows PowerShell 5.1 会吞掉 `--`，上面的命令报 `unknown option '--context'`。改用 `add-json`，JSON 里的引号写成 `\"`，JSON 里不留空格：

```powershell
cd <仓库根>
claude mcp add-json --scope local serena '{\"type\":\"stdio\",\"command\":\"serena\",\"args\":[\"start-mcp-server\",\"--context\",\"claude-code\",\"--project-from-cwd\",\"--enable-web-dashboard\",\"false\"]}'
claude mcp add-json --scope local openwiki '{\"type\":\"stdio\",\"command\":\"openwiki\",\"args\":[\"mcp\",\"--host\",\"claude\"],\"env\":{\"OPENWIKI_TELEMETRY_DISABLED\":\"1\"}}'
claude mcp add-json --scope local graphify '{\"type\":\"stdio\",\"command\":\"graphify-mcp\",\"args\":[\"graphify-out/graph.json\"]}'
claude mcp list
```

**Codex**（`~/.codex/config.toml` 全局，或仓库里的 `.codex/config.toml` 只对该仓库生效）：

```toml
[mcp_servers.serena]
command = "serena"
args = ["start-mcp-server", "--context", "codex", "--project-from-cwd", "--enable-web-dashboard", "false"]

[mcp_servers.openwiki]
command = "openwiki"
args = ["mcp", "--host", "codex"]
env = { OPENWIKI_TELEMETRY_DISABLED = "1" }

[mcp_servers.graphify]
command = "graphify-mcp"
args = ["graphify-out/graph.json"]
```

**其他走 MCP 的 agent**（接 DeepSeek、GLM 等）：同样的三条 stdio 命令。Serena 的 `--context` 换成 `agent`；OpenWiki 的 `--host` 是任意小写标识，只用来记谁写的页。

注册是给**下一个**会话用的：Claude Code 里当前会话不会自动拿到新注册的 MCP，要重开会话（或 `/mcp` 里重连）；Codex 同样要重开。所以注册放在开工前，由开 lane 的人在目标目录先做好。Claude Code 里 MCP 工具可能只列出名字、不带参数定义（延迟加载），调用前先 `ToolSearch` 取 `select:<工具名>` 的 schema。

Windows 上宿主报「连不上」：`openwiki`、`graphify-mcp` 是 `.cmd` / `.exe` 垫片，有的宿主不会经 `cmd` 启动。改成 `cmd /c openwiki mcp --host claude`，或直接指 `node <npm 全局目录>\node_modules\openwiki\dist\cli\cli.js mcp --host claude`。

Serena 第一次启动会自动下载语言服务器（Python 用 pyright，TypeScript 用 typescript-language-server）；离线机器先在联网时跑 `serena download-ls-dependencies`。

## 它们往项目里写什么

| 路径 | 谁写的 | 处理 |
|---|---|---|
| `graphify-out/` | graphify | 本地生成物，几十 MB |
| `.serena/`（`project.yml`、缓存、memories） | Serena | 本地配置 |
| `openwiki/` | OpenWiki | 生成的 wiki 和 `.claims` 证据 |
| `.github/workflows/openwiki-update.yml` | OpenWiki | **删掉**：它每天用 OpenAI 重新生成，把代码发出去 |
| `AGENTS.md` / `CLAUDE.md` 里 `<!-- OPENWIKI:START -->` 到 `END` 一段 | OpenWiki | 按项目规矩定去留；别人的仓库默认 `git checkout --` 还原。只有一行 `@AGENTS.md` 的 `CLAUDE.md` 会被再加一行 `@AGENTS.md`，成了重复导入 |

把前三项加进 `.git/info/exclude`（不改仓库里被跟踪的 `.gitignore`）：

```
graphify-out/
.serena/
openwiki/
```

## 不选的工具

| 工具 | 一句原因 |
|---|---|
| CodeWiki | MCP 模式的增量更新在 Windows 上把反斜杠路径和 git 的正斜杠对不上，一次真实更新判了「0 个模块要改」；页面也浅 |
| codebase-memory-mcp | 同一组 40 个函数上找到的调用方最少（32%），默认跳过测试文件 |
| DeepWiki、Google Code Wiki、Zread 等托管服务 | 私有代码要交给厂商 |
| GitNexus | 许可 PolyForm Noncommercial，禁止商用 |
| Claude Code 官方 `pyright-lsp` / `clangd-lsp` / `typescript-lsp` 插件 | 能用，但只有 Claude 有；跨模型用 Serena。Claude lane 想加可以加，不替代 Serena |

## 依据

2026-10-27 在一个约 28 万行（Python 为主、带 C++ 和 JS）的内部仓库和它 7 万行的子目录上实测得出；数字见各附件。实测记录和用户决定在 lane-router 问答 `87057c97`。
