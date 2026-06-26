---
name: official-mcp-usage
description: How to consume UE 5.8+ official `ModelContextProtocol` MCP server from a Claude Code session — the setup that actually exposes tools and the undocumented usage quirks. Covers (1) setup: the 4 plugins needed (`ModelContextProtocol` server shell + `AllToolsets` aggregator that is the REAL tool provider + `MCPClientToolset` + optional `AIAssistant`) — enabling only the server shell connects fine but lists no tools; plus auto-start-server setting / console command / `.mcp.json` HTTP config / default port 8000 path `/mcp`; (2) usage hidden contracts: `load_toolset` only takes effect next turn, reconnect is the only way to refresh client-side tool list (after editor restart / session-id expiry), tool-name dot→single-underscore mapping, session-id bound to server lifecycle (`Invalid session id -32600` → reconnect), several schema mislabels (`find_actors(tag="")` ok, `set_properties` UObject ref = raw path string), refPath conventions; (3) failure discipline: when an official-MCP call errors, STOP and ask the user to Reconnect — never silently fall back to a fork or another backend. Symmetric counterpart to the `unrealmcp-usage` skill (which covers the fork). Platform-choice (fork vs official) lives in `guidelines/ue/mcp-platform-choice.md`.
when_to_use: Fires when (1) the current project is UE 5.8+ and has the official MCP enabled (`.mcp.json` / `.claude/mcp.json` pointing at `http://127.0.0.1:8000/mcp`, or `ModelContextProtocol` + `AllToolsets` in the `.uproject`); (2) a task needs to programmatically read/mutate UE editor state (spawn/list/modify actors, edit blueprints/graphs, components, level, Sequencer, GAS, Niagara, UMG, settings) via the official MCP; (3) an official-MCP tool call fails (`No such tool` / `Unknown tool` / `Invalid session id` / connection refused); (4) `list_toolsets`/`load_toolset`/`call_tool` are involved; (5) onboarding a new UE 5.8+ project to the official MCP and tools come up empty. Skip when the project uses only the fork (see `unrealmcp-usage`) or has no MCP integration.
---

# Official UE MCP Usage (UE 5.8+)

UE 5.8 ships Epic's official `ModelContextProtocol` plugin (Experimental, NoRedist) — an HTTP MCP server that exposes editor automation through the `ToolsetRegistry` system. This skill is the **consumer-side** how-to: the setup that actually produces tools, and the undocumented runtime quirks. Which server to use (fork vs official) is a separate decision — see `guidelines/ue/mcp-platform-choice.md`. Fork usage is `skills/ue/unrealmcp-usage`.

## When This Fires

| 触发信号 | 行动 |
|---|---|
| 项目是 5.8+ 且 `.mcp.json` 指向 `http://127.0.0.1:8000/mcp`，或 `.uproject` 开了 `ModelContextProtocol` + `AllToolsets` | 已集成官方 MCP，编辑器自动化优先走它 |
| 任务要 spawn/改 actor / 编 BP / 改 component / level / Sequencer / GAS / Niagara / UMG / settings | 用官方 MCP（toolset 分类很全），先确认工具已 load（见下） |
| 官方工具报 `No such tool` / `Unknown tool` / `Invalid session id` / 连不上 | **停下问 user Reconnect**，不要静默换后端（见 §失败纪律） |
| 新项目接官方 MCP 但 `list_toolsets` 是空的 / 工具调不到 | 99% 是只开了 server 没开 `AllToolsets`（见 §Setup 第 1 条） |

## Setup — 让官方 MCP 真的有工具

### 1. ★ 必须开 `AllToolsets`，否则连上也没工具

`ModelContextProtocol` 只是 **HTTP server 外壳** —— 开了它 server 能 listen、`initialize` 能握手，但 `list_toolsets` 基本是空的。真正注册工具的是 `AllToolsets`：一个 `EditorOnly` 聚合 plugin，依赖全部 ~21 个 toolset 子插件（Editor / GAS / Niagara / UMG / Sequencer / Slate / PCG / StateTree / …）。

`.uproject` 验证过的工作配置（4 个 plugin）：

```jsonc
{ "Name": "ModelContextProtocol", "Enabled": true, "TargetAllowList": ["Editor"] },
{ "Name": "AllToolsets",          "Enabled": true },   // ★ 真正提供工具的聚合器
{ "Name": "MCPClientToolset",     "Enabled": true },   // 其实已被 AllToolsets 包含，冗余但无害
{ "Name": "AIAssistant",          "Enabled": true }    // 编辑器内 AI 助手；外部 MCP 不强依赖，可选
```

这些都是 engine 自带的 Experimental + NoRedist 插件（`Engine/Plugins/Experimental/ModelContextProtocol` 和 `.../Toolsets/`）。带 C++ 模块 → 加完要 **cold rebuild + 重开编辑器**（不要 Live Coding）。

### 2. 启动 HTTP server（默认不自动起）

Server 默认 `bAutoStartServer=false`。三种起法：

| 方式 | 操作 |
|---|---|
| 控制台命令（当场起） | `ModelContextProtocol.StartServer`（端口默认 8000，`ModelContextProtocol.StartServer <port>` 覆盖） |
| 项目设置（下次自动起） | Project Settings → **Model Context Protocol** → 勾 **Auto Start Server** |
| 命令行 flag | 启动加 `-ModelContextProtocolStartServer`（旧名 `-StartModelContextProtocolServer` 已 deprecated） |

设置类是 `UModelContextProtocolSettings`（`config=EditorPerProjectUserSettings`，**per-user**，存 `Saved/Config`）—— 所以 Auto Start 由 user 在 UI 勾，不便提交进版本库。起好看 log：`LogHttpListener: Created new HttpListener on 127.0.0.1:8000`。

### 3. 客户端配置 `.mcp.json`

Claude Code 走项目根 `.mcp.json`（key `mcpServers`，HTTP transport）：

```json
{ "mcpServers": { "unreal-mcp": { "type": "http", "url": "http://127.0.0.1:8000/mcp" } } }
```

- server **key 名你自己定**（引擎 `WriteClientConfiguration` 默认写 `unreal-mcp`；也常见手命名 `ueOfficialMCP`）。**这个 key 决定后面所有工具的前缀**（见 §quirks 工具命名）。
- 端口默认 8000，URL path 默认 `/mcp` → `http://127.0.0.1:8000/mcp`。
- `.mcp.json` 是会话**启动时**扫描 + 弹信任提示。运行中创建的 `.mcp.json` 当前会话看不到 → **重载窗口 / 新开会话**才生效，首次还要批准。
- 验证 server 独立于 Claude Code：
  ```bash
  curl -s -X POST http://127.0.0.1:8000/mcp \
    -H "Content-Type: application/json" -H "Accept: application/json, text/event-stream" \
    -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-06-18","capabilities":{},"clientInfo":{"name":"diag","version":"0"}}}'
  ```
  返回 `result.capabilities.tools` 即 UE 端 OK，问题就只在 Claude Code 配置侧。

## 使用 Hidden Contracts（文档没写、实测得到）

Heavy use 之前先扫一眼，避免反复撞同一坑。

### 1. `load_toolset` 跨 turn 才生效

`list_toolsets → describe_toolset → load_toolset`。`load_toolset` 报 "Loaded N tools" **不代表本 turn 可用** —— 同 turn 立刻调具体工具会 `No such tool available`。工具 schema 要**下一个对话 turn** 才出现在 deferred tools 列表（前缀 `mcp__<server-key>__...`）。

应付：想 heavy use 一组工具就**先一次性 load 完所有需要的 toolset**，让 user 随便回一句开新 turn，工具就到位。`bEnableToolSearch=true`（默认）时 `tools/list` 只暴露 `list_toolsets`/`describe_toolset`/`call_tool`，LLM 按需发现 + 走 `call_tool` 派发。

### 2. Reconnect 是 client tool list 刷新的唯一入口

`load_toolset` 在 **server 端** register 工具；**client 端要 reconnect 才会重拉 tool list**。流程：

1. 调 `load_toolset` 报 Loaded
2. **让 user 在 `/mcp` 弹窗点 Reconnect**（选你的 server → Reconnect）—— 对话内无法触发
3. 新 turn 出现 system reminder "N deferred tools are now available"
4. `ToolSearch select:mcp__<server-key>__xxx,...` 加载 schema → 调用

**跨编辑器重启 / 多次 reconnect 后**：即使等了下一 turn + load 报 Loaded，deferred tools 可能仍没注册（`list_toolsets` 还能返回完整列表，证明 server 侧工具都在，是 client list 没刷）。修法一样：让 user 在 `/mcp` Reconnect，等 "deferred tools available" reminder 再用。**没有这条 reminder 不要假设工具可用就连续重试**（白烧 turn）。

### 3. 工具命名：点转**单**下划线

`list_toolsets` 返回形如 `toolset_registry.toolsets.core.actor.ActorTools.set_label`。Claude Code 端：

```
mcp__<server-key>__toolset_registry_toolsets_core_actor_ActorTools_set_label
     ↑↑ server key 与路径间双下划线        ↑ 路径里的点 . 全转单下划线 _
```

**不要**猜成全双下划线（`...registry__toolsets__core__...` — 错）。`<server-key>` 是你 `.mcp.json` 里的那个 key。

### 4. Session id 绑 server 生命周期

UE Editor 重启 / server 重启后，对话内缓存的 session id 立即作废 → 调任意工具报 `Invalid session id (-32600)`。注意：`claude mcp list` / `/mcp` 弹窗显示 Connected **≠** 当前对话内 client session 仍 valid（前者每次新进程重握手）。修法：让 user 在 `/mcp` Reconnect 重握手拿新 session id。

### 5. 几个 schema 误标 / 宽松行为

| 工具 | 实测行为 |
|---|---|
| `find_actors(glob="*", tag="")` | schema 标 `tag` required，但空字符串 OK = 不按 tag 过滤 |
| `set_properties(values='{"StaticMesh":"/Engine/BasicShapes/Cube.Cube"}')` | UObject 引用属性直接传 raw path 字符串，**不用** `{"refPath":...}` 包装 |
| `add_to_scene_from_class(name=...)` | `name` 影响 label，但 actor 内部 unique name 由 UE 自动生成（`PointLight_0/1/2`）；自定义显示名用 `ActorTools.set_label` |
| `add_function_param(input_param=true)` 返回 `direction: EGPD_Output` | 对的 —— K2Node_FunctionEntry 从 output pin 把参数"输出"给函数体，别被字面 Output 误导 |

### 6. 常用 refPath 约定

- C++ class：`/Script/<Module>.<Class>`（如 `/Script/Engine.PointLight` / `/Script/Engine.StaticMeshActor` / `/Script/Engine.Actor` 作 BP parent）
- Asset：`/<MountPoint>/<Path>/<Name>.<Name>`（如 `/Engine/BasicShapes/Cube.Cube`；`.Name` 后缀是对象名，单资产 = 文件名）
- BP class：`/Game/<Path>/BP_Foo.BP_Foo`；BP CDO component：`/Game/<Path>/BP_Foo.BP_Foo_C:CompName_GEN_VARIABLE`

## 失败纪律：报错 → 停下问 user Reconnect，不要静默 fallback

官方 MCP 调用收到 server error（`No such tool` / `Unknown tool` / `Invalid session id -32600` / 连接拒绝 / streamable HTTP error）→ **立刻停手**，告诉 user 哪个工具错了 + 可能原因（多半是 §2/§4 的 reconnect/session），让 user 在 `/mcp` Reconnect，从中断点续。

**不要**自己改用 fork 的同名工具 / 别的后端继续推进 —— 静默 fallback 会让 session 跑着跑着默默换后端，user 不知情；fallback 语义可能微妙不同、出错难追；还掩盖了官方 MCP 真实连接状态让 user 没机会及时修。例外：user **明确说**"先用 X 顶替" → 走时**显式声明切换**让 user 知情。这是通用原则的 MCP 实例：主后端报错，停下问，别偷偷换后端。

## Anti-Patterns

| 反 pattern | 后果 | 修法 |
|---|---|---|
| 只开 `ModelContextProtocol` 不开 `AllToolsets` | server 连得上但 `list_toolsets` 空 | 开 `AllToolsets`（真正的工具提供者） |
| 同 turn `load_toolset` 后立刻调工具 | `No such tool available` | load 完让 user 开新 turn / Reconnect |
| 工具名猜全双下划线 | 工具找不到 | 点转单下划线，server key 后才双下划线 |
| 报 `Invalid session id` 当 server 挂了 | 误判 | server 没挂，是 session 过期 → Reconnect |
| 官方报错就静默切 fork | user 不知情 + 难追 | 停下问 user Reconnect |
| 运行中建 `.mcp.json` 以为立刻可用 | `/mcp` 看不到 | 重载窗口 / 新会话 + 批准 |

## 项目实例参考

`Painting_Test_5_8`（UE 5.8）2026-05 接官方 MCP：dual server 验证后明确"本项目 heavy use 官方 MCP"。`.uproject` 开 `ModelContextProtocol` + `AllToolsets` + `AIAssistant` + `MCPClientToolset`，`.mcp.json` server key `ueOfficialMCP`（→ 工具前缀 `mcp__ueOfficialMCP__...`），73 工具实测跑通 spawn actor / 改 BP / 改 component property / 建 folder 等。上面 9 条 quirks + 失败纪律都来自该项目反复实战（project memory `official-mcp-quirks` / `official-mcp-failure-stop-and-ask`；"本项目偏好官方" `prefer-official-mcp` 是项目专属，未促升）。

`WRR_Paint_Test`（UE 5.8）2026-06 接官方 MCP 时直接复用本 skill —— 第一版只开了 `ModelContextProtocol` 没开 `AllToolsets`，正好命中 §Setup 第 1 条的坑。

## 相关 Guidelines / Skills

- `guidelines/ue/mcp-platform-choice.md` —— 用哪个 MCP（fork vs 官方）的平台选型 + 决策表 + 扩展机制。本 skill 管"官方怎么用"，那篇管"用哪个"
- `skills/ue/unrealmcp-usage/SKILL.md` —— 对称的 fork 使用指南（TCP `ue_cmd.py`）
- `guidelines/ue/external-automation-write-path.md` —— 任何外部脚本（含 MCP）写 UE 资产必走 `PostEditChangeProperty` 同步路径
- `guidelines/code/diagnose-before-fixing.md` —— "工具调不到"先 curl 探针把问题 isolate 到 UE 侧还是 client 侧，别凭猜
