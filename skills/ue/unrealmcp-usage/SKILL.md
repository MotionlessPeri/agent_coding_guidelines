---
name: unrealmcp-usage
description: How to use the UnrealMCP plugin from an agent session to programmatically read or mutate UE editor state. Use when a project contains `Plugins/UnrealMCP`, `UnrealMCP_Docs`, `sync_unreal_mcp.sh`, or related MCP client configuration; when a task needs editor automation through `ue_cmd.py`; or when deciding whether to extend the fork. On UE 5.8+, check `official-mcp-usage` first and use this fork only when the official MCP lacks the required operation. Skip when the project has no UnrealMCP integration and the task does not involve UE editor automation.
---

# UnrealMCP Usage

UnrealMCP 是一个 UE 编辑器侧 C++ 插件 + Python tool layer，让 agent / 外部脚本通过 TCP 命令读 / 改 editor state（actor / property / blueprint graph / subsystem 调用 / 保存退出 etc.）。源 repo 是 fork：`E:\xd_projects\unreal-mcp`（私有），消费侧通过 `sync_unreal_mcp.sh` 同步插件 + Python + Docs 进项目。

本 skill 教**消费侧** agent 怎么用，不教扩展 fork（扩展见文末 §Extending）。

## Platform Paths

本文用 `<skill-dir>` 表示当前平台安装后的 skill 目录：

| 平台 | `<skill-dir>` |
|---|---|
| Claude Code | `~/.claude/skills/unrealmcp-usage` |
| Codex | `~/.agents/skills/unrealmcp-usage` |

TCP 直连不依赖 agent 客户端的 MCP 配置。下文命令中的 `<skill-dir>` 必须先替换成当前平台路径。

> ## ⚠️ UE 5.8+ → 优先官方 MCP，本 fork 在 5.8+ 上是 legacy / fallback
>
> UE 5.8 引擎自带官方 `ModelContextProtocol`（覆盖面碾压 fork：46 toolset × 完整 CRUD）。
> **5.8+ 项目默认用官方 MCP**（见 `skills/ue/official-mcp-usage`）；fork 在 5.8+ 上只在官方
> 覆盖不到的 niche（如 material 整图 single-shot dump 的 token 效率）才用。
>
> **但 fork 不是全局 deprecated** —— UE **5.7 及之前官方 MCP 根本不存在，fork 仍是唯一选择**，
> 本 skill 在那些项目里照常完整适用。判断顺序：先看项目 UE 版本 → 5.8+ 先查官方、fork 兜底；
> ≤5.7 直接用 fork。完整分版本决策表见 [`guidelines/ue/mcp-platform-choice.md`](../../../guidelines/ue/mcp-platform-choice.md)。

## When This Fires

| 触发信号 | 行动 |
|---|---|
| **项目是 UE 5.8+** | **先查官方 MCP**（`official-mcp-usage` skill）；fork 仅作 niche fallback（见上方 banner） |
| 项目里看到 `Plugins/UnrealMCP/` / `UnrealMCP_Docs/` / `.claude/mcp.json` / `.codex/config.toml` / `sync_unreal_mcp.sh` | 本项目可能已集成 UnrealMCP；先 ping 验证（**5.8+ 先确认官方不够用**） |
| 任务需要 spawn actor / 改 property / 查 actor list / call subsystem function / 控制编辑器生命周期 | 先 ping 看 MCP 可用否，可用就走 MCP 不要写 C++ / 手 edit asset 文件 |
| 任务要操作 UE editor 但项目**没**集成 UnrealMCP | 跟 user 确认要不要先装（详 §Onboarding） |
| 撞到 MCP 工具不够用 | **先问 user 要不要扩 fork**，不要静默绕过（详 §Capability Gap Policy） |

## Detection — 项目装没装 UnrealMCP

```bash
# 项目里跑一遍快速 detect
ls Plugins/UnrealMCP/ 2>/dev/null && echo "C++ plugin OK"
ls UnrealMCP_Docs/ 2>/dev/null && echo "Docs synced"
test -f .claude/mcp.json && echo "MCP config OK"
test -f .codex/config.toml && echo "Codex config present"
test -f sync_unreal_mcp.sh && echo "Sync script OK"
```

插件、文档和同步脚本都在，且 ping 成功，才算可直接使用。客户端配置只是辅助线索；缺少配置不影响 TCP 直连。

> **`.claude/mcp.json` 与 `.codex/config.toml` 都不影响默认 invoke 路径**——本 skill 默认走 §Invocation 的 TCP 直连（`ue_cmd.py`），不读取客户端 MCP 配置。`.claude/mcp.json` 只在选择 Claude Code 原生 MCP 集成时生效；Codex 的 MCP server 配置位于 `.codex/config.toml`，但本 fork 的 Codex 原生集成不在本 skill 的已验证范围内。

## Invocation — 优先 `ue_cmd.py` TCP 直连

**默认走 TCP 直连，不依赖 agent 客户端的 MCP 集成**。Claude Code VSCode 扩展加载 mcp.json 不稳定是选择直连的已知原因之一；Codex 也使用同一条直连路径，因此不需要伪造一套未经验证的原生 MCP 配置。

本 skill 自带 `ue_cmd.py`。调用路径：

| Shell | 调用 |
|---|---|
| Bash / Git-Bash | `python <skill-dir>/ue_cmd.py <command> [json_params]` |
| PowerShell | `python <skill-dir>/ue_cmd.py <command> [json_params]` |
| cmd.exe | `python <skill-dir>\ue_cmd.py <command> [json_params]` |

### 协议

```
TCP host:port = 127.0.0.1:30557   (UNREAL_MCP_HOST / UNREAL_MCP_PORT 可覆盖)
request  = {"type": "<command>", "params": {...}}
response = {"status": "success", "result": {...}}    or    {"status": "error", "error": "..."}
```

### Env var override

同机跑多个 editor 实例 / 改默认端口 / 需要更长超时时：

| Env var | 默认 | 何时用 |
|---|---|---|
| `UNREAL_MCP_HOST` | `127.0.0.1` | 远程 editor / 容器内 |
| `UNREAL_MCP_PORT` | `30557` | 跑两个 editor 实例避免冲突 / 默认端口被占（如 Windows 企业监控进程占住 55557 这种）|
| `UNREAL_MCP_TIMEOUT` | `30` (秒) | server-side 长操作（Perforce sync / 大 level 加载 etc.）|

**关键**：`UNREAL_MCP_PORT` env var **同时被 C++ plugin / Python MCP server / `ue_cmd.py` 三层读取**——改端口必须在 editor 进程的环境里设了 env var **再启动 editor**，并且**同一个 env var 也要对 ue_cmd.py 客户端进程可见**（同一个 shell session 设一次即可）。UE 也支持 `-MCPPort=N` 命令行覆盖（仅 editor 侧）。

Editor 启动前在 shell 里设 env var：

```powershell
# PowerShell（持久化到用户环境）
[Environment]::SetEnvironmentVariable("UNREAL_MCP_PORT", "30557", "User")

# 或一次性（只对当前 shell 启动的进程有效）
$env:UNREAL_MCP_PORT = "30557"
start "" "C:/Program Files/Epic Games/UE_5.X/Engine/Binaries/Win64/UnrealEditor.exe" "MyProject.uproject"
```

### 上手 4 步

```bash
# 1. 先 ping 确认 editor 在跑 + 插件加载了
python <skill-dir>/ue_cmd.py ping

# 2. 查命令列表（runtime 查询）
python <skill-dir>/ue_cmd.py help

# 3. 查具体命令参数
python <skill-dir>/ue_cmd.py help '{"command":"spawn_actor"}'

# 4. 调
python <skill-dir>/ue_cmd.py spawn_actor '{"type":"PointLight","name":"MyLight","location":[0,0,200]}'
```

### 静态命令参考

- `UnrealMCP_Docs/commands.md` — base 命令完整列表 + 参数
- `UnrealMCP_Docs/commands-dialogue.md` — UnrealMCPDialogue 扩展命令（如果项目装了扩展）
- `UnrealMCP_Docs/commands-logicdriver.md` — UnrealMCPLogicDriver 扩展命令
- `UnrealMCP_Docs/agent-usage-guide.md` — agent 用法 primer
- `UnrealMCP_Docs/known-issues.md` — 完整踩坑 + 代码示例

> 如果项目没 sync Docs：源在 `E:\xd_projects\unreal-mcp\Docs\`。

## Capability Gap Policy（重要）

**MCP 不能做某件事 → 先问 user 要不要扩 fork，不要静默绕过**。

具体说，发现下列情形之一时**停下问 user**：

- 命令存在但参数不够（如想给某 actor 改某个属性但 `set_actor_property` 不支持这个 struct 类型）
- 命令完全缺失（如想给 blueprint 加节点但没有对应命令）
- 命令有但返回信息不全（如 `get_actor_properties` 不返对象数组属性，详 known-issues #6）

**不推荐**的绕过方式（除非 user 同意）：

- 手 edit `.uasset` / `.umap` 文件（二进制，容易破坏）
- 直接写 C++ workaround 让任务"完成"但 MCP 工具没改进
- 让 user 在 editor 里手点（违背自动化目标）

**推荐**的对话模板：

> "这个任务我想用 `set_actor_property` 但 MCP 当前不支持 nested struct（如 `FCollisionResponseContainer`）。两个选项：
> A. 扩 fork（在 `E:\xd_projects\unreal-mcp\` 加命令，10-30 分钟）
> B. 你在 editor 里手改这一项
> 选哪个？"

详 fork `AGENTS.md` "Hard Constraints" + 本 skill §Extending。

## Top Gotchas（5 条 inline，详 fork `Docs/known-issues.md`）

| # | 一句话 | 详情 |
|---|---|---|
| 1 | `spawn_actor` 后必须额外 `set_actor_property` 设 `ActorLabel`，否则 Outliner 显示类名 | known-issues #1 |
| 2 | `spawn_actor` / `call_subsystem_function` 后 **wait ~4s**——Perforce 操作阻塞游戏线程，立刻发下一命令会撞空响应 | known-issues #2 |
| 3 | `call_subsystem_function` 返回值字段名是 **`ReturnValue`**，不是 `result` / `actor_name` | known-issues #3 |
| 4 | Struct property（`FLinearColor` / `FVector` 等）走 **dict** —— `{"R":1.0,"G":0.0,"B":0.0,"A":1.0}` | known-issues #4 |
| 5 | `get_actor_properties` **不返**对象数组属性（如 `AIPoints[]`）；用 `add_to_actor_array_property` 的 `new_array_size` 间接确认 | known-issues #6 |

## Onboarding —— 给新 UE 项目装 UnrealMCP

新项目第一次接入 UnrealMCP 要做的事（agent 跟 user 确认每一步）：

### 1. Clone / 定位 fork

```bash
# 选项 A: 同事的机器还没有 fork — clone（路径自选）
git clone <fork-url> E:/xd_projects/unreal-mcp

# 选项 B: 已经有 fork（多项目共用一个 fork checkout）
ls E:/xd_projects/unreal-mcp  # 确认存在
```

### 2. 写 sync 脚本到项目根

复制 `sync_unreal_mcp.sh` 到新项目根，调整 fork 路径。脚本会把 fork 的 4 个产物同步进项目：

```
fork/MCPGameProject/Plugins/UnrealMCP/  →  project/Plugins/UnrealMCP/
fork/Python/                            →  project/UnrealMCP_Python/
fork/Docs/                              →  project/UnrealMCP_Docs/
fork/MCPGameProject/.../mcp.json        →  project/.claude/mcp.json (template)
```

参考实现见 DialogueSystemSample 项目根 `sync_unreal_mcp.sh`。

### 3. 跑一次 sync + 把 `Plugins/UnrealMCP/` 添加到 .uproject 的 plugin 列表

`.uproject` 里加：
```json
{
    "Name": "UnrealMCP",
    "Enabled": true
}
```

### 4. Build + 启动 editor 验证

```bash
# cold rebuild
Build.bat <Project>Editor Win64 Development -Project="<uproject>" -WaitMutex -FromMSBuild
# 启动
start "" UnrealEditor.exe "<uproject>"
# verify
python <skill-dir>/ue_cmd.py ping
```

`ping` 返回 `{"status":"success",...}` → 装好了。

### 5. 给项目 AGENTS.md 加这几段

```markdown
## UnrealMCP Integration

- UnrealMCP plugin: `Plugins/UnrealMCP/` (synced from fork; not in git per .gitignore)
- Python server: `UnrealMCP_Python/` (synced)
- Docs: `UnrealMCP_Docs/` (synced)
- Sync script: `./sync_unreal_mcp.sh`
- TCP 直连: `python <skill-dir>/ue_cmd.py <command> [json]`（按当前 agent 平台替换 `<skill-dir>`）
- Agent 用法 + 命令参考 + 踩坑见 `UnrealMCP_Docs/`；通用 agent 协作纪律见 `<skill-dir>/SKILL.md`
- Capability gap → 先问 user 要不要扩 fork
```

### 6. `.gitignore` 排除 sync 产物

```
Plugins/UnrealMCP/
UnrealMCP_Python/
UnrealMCP_Docs/
```

理由：sync 产物的 SoT 在 fork，不在消费项目里。同步一次 patch 一次时不要让消费项目的 git 跟着 churn。

**`.claude/mcp.json` 决策**：跟上面三个 sync 产物不同，**应该入项目 git**——它是 per-project 客户端配置（server name / 启动参数 / 路径都可能因项目而异），sync 时仅作 template 复制一次，之后由项目自己维护。新建 / 改这文件后 commit 进项目 repo。

## Extending UnrealMCP（要给 fork 加新命令时）

新命令必须**两侧同步**：

| Side | 文件 | 干什么 |
|---|---|---|
| C++ dispatcher | `Plugins/UnrealMCP/Source/UnrealMCP/Private/UnrealMCPBridge.cpp` 的 if-else 路由 | 注册命令 → handler |
| Python tool layer | `Python/tools/*.py` | 包装成 MCP tool（供 Claude Code MCP 集成调用） |

**Hard constraints**（详 fork `AGENTS.md`）：
- 加完命令必须在 `Docs/Progress.md` 加一行
- 行为变更必须更新 `Docs/commands.md` / `commands-*.md` 对应段
- 冷重建验证，不依赖 Live Coding
- **fork 每个功能单独 commit**，不要积累；开新功能前先 commit 当前未提交内容
- 消费侧 `Plugins/UnrealMCP/` 是 sync 产物，**不要直接改**——改 fork 然后 sync

### ★ 写命令必走 Editor write-through path（PostEditChangeProperty）

新 MCP 命令改 UE 资产 property 时，**默认不能只调底层 setter**——必须模拟 Editor UI 改 property 时走的"写入即同步"路径。底层 setter 只改最表面的 UPROPERTY 字段，跳过 framework（LogicDriver / BP / AnimBP / Material / Niagara / DataTable 等）维护的 template / property graph / construction script 输出 / cache。结果：schema 编译能过，运行时炸。

**完整规则 + 三个判断问题 + 已知有 PostEditChange 重型 hook 的 framework 清单**：见 [`guidelines/ue/external-automation-write-path.md`](../../../guidelines/ue/external-automation-write-path.md)。

**MCP-side 模板**——写 `HandleXxx` 改 reflected property 时：

```cpp
TSharedPtr<FJsonObject> FUnrealMCPxxxCommands::HandleSetSomething(const TSharedPtr<FJsonObject>& Params)
{
    // ... 解析参数 / 拿到目标 Object 跟 NewValue ...

    Object->Modify();                              // ① undo 支持

    // ② 改 property（任何形式都行——直接 setter / SetVal / 直接写字段都可以）
    Object->SomeProperty = NewValue;

    // ③ ★ 关键：触发 framework 同步路径
    FProperty* PropRef = Object->GetClass()->FindPropertyByName(
        GET_MEMBER_NAME_CHECKED(UYourClass, SomeProperty));
    FPropertyChangedEvent Evt(PropRef, EPropertyChangeType::ValueSet);
    Object->PostEditChangeProperty(Evt);

    // ④ batch 场景才需要显式 compile + dirty；单条改动 PostEditChange 内部已经 conditionally compile
    // if (bExplicitCompileNeeded) { FKismetEditorUtilities::CompileBlueprint(Blueprint); }
    // Object->MarkPackageDirty();

    // ... 返回 success response ...
}
```

**反例**（fork repo 内已有的 `HandleSetLogicDriverStateNodeClass` 旧实现）：

```cpp
// ❌ 跳过 PostEditChange，BattleDemo R2 踩坑案例
StateNode->Modify();
StateNode->SetNodeClass(NewClass);
FKismetEditorUtilities::CompileBlueprint(Blueprint);   // 半新半旧状态被编进 bytecode
```

后果：18 个 LogicDriver state 切完 class，编译 success 无 warning，PIE 装备 + 按键死循环。**file-level p4 revert** 才能恢复。

**已知特别需要走 PostEditChange 的 MCP 写命令场景**：
- 改 LogicDriver state / transition 的 Node Class（如本案例）
- 改 Blueprint 的 Parent Class
- 改 Material 的 parameter / expression 连接
- 改 Animation Blueprint 的变量绑定
- 改 Niagara emitter / system 的 module 序列
- 改 DataTable 的 RowStructure

写 MCP 命令前对照上面清单 + grep `PostEditChangeProperty` 验。

### Drift policy: `ue_cmd.py` 跟 fork TCP protocol

本 skill 自带的 [`ue_cmd.py`](ue_cmd.py) 是 fork `UnrealMCPBridge.cpp` TCP wire protocol 的 client 实现。当 fork **改 wire protocol**（端口默认值、payload schema、framing、error 形态等），本 skill 的 `ue_cmd.py` **必须同步更新**——否则 client 静默不兼容，调命令拿空响应或解析失败。

实施约定：

- fork 改 wire protocol 的 commit message 显式标注 `wire-protocol-change:` 前缀，方便检索
- 本 skill 跟着 commit 一次 `ue_cmd.py` 更新，commit message 引用 fork 那条 commit hash
- 不破坏向后兼容性时（如新加 optional 字段），跟进时机可放宽到下次 skill 修订一并改

跟 `multi-session-coordination` skill 内 `multi_session.py` 跟 Claude Code hook schema 的漂移管理是同形态 precedent。

**典型 sync & validate 流程**：

```bash
# 1. 在 fork 实现 + cold rebuild 验证（用任一消费项目跑）
cd E:/xd_projects/unreal-mcp
# ... 改 C++ + Python tool ...

# 2. 项目侧 cold rebuild
cd <consumer-project>
Build.bat ...
start "" UnrealEditor.exe ...

# 3. live smoke
python <skill-dir>/ue_cmd.py <new_command> '...'

# 4. sync 进消费项目（如果不是在消费项目里直接 fork-link 开发）
./sync_unreal_mcp.sh

# 5. 两侧分别 commit
# fork: 在 E:/xd_projects/unreal-mcp/ commit
# consumer: 在项目根 commit sync 后的文件（如果 sync 产物入 git）
```

## Multi-Project Workflow

跨项目用同一个 fork checkout 时（推荐——`E:\xd_projects\unreal-mcp\` 一份，N 个消费项目都从这里 sync）：

- 改 fork 的 commit 一次，跑各项目 `sync_unreal_mcp.sh` 各拉一次
- fork 里的踩坑全 N 个项目共享，不再重复整理
- 本 skill ship 的 `ue_cmd.py` 全 N 个项目共用同一份（`<skill-dir>/ue_cmd.py`）

新项目 onboarding 走 §Onboarding。已有项目升级 fork 走 `UnrealMCP_Docs/ForkWorkflow.md`。

## 相关 Guidelines / Techniques

- [`guidelines/workflow/agent-lifecycle.md`](../../../guidelines/workflow/agent-lifecycle.md) "Autonomous Actions" / "Validation Before Completion" —— 用 MCP 跑编辑器自动化时仍受这些纪律约束（cold rebuild / 验证后再 claim done / 失败 escalation）
- [`guidelines/code/clarify-before-implementing.md`](../../../guidelines/code/clarify-before-implementing.md) —— capability gap 时跟 user 澄清"扩 fork vs 手工 vs 跳过"，不要静默选
- [`skills/ue/ue-module-architecture/SKILL.md`](../ue-module-architecture/SKILL.md) —— 扩 fork 加新命令时，C++ 命令 handler 走 Editor Actions 层而非 Runtime Ops（如果触及插件代码结构）
- [`skills/ue/ue-reference-engine-source/SKILL.md`](../ue-reference-engine-source/SKILL.md) —— 写新 MCP 命令实现 editor 自动化时，先找 UE engine source 现成实现参考
- Fork 内的 `AGENTS.md` / `Docs/README.md` / `Docs/Progress.md` —— 扩 fork 前必读
