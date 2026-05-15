# Claude Code Hook Hidden Contracts

写自定义 hook（settings.json `hooks` 块 + 外挂脚本）时遇到的几条**官方文档没明说但实际行为如此**的约定。属于"看着该 work 的 idiom 实际不 work"hidden contract 集——跟 `guidelines/ci-windows/powershell-native-command-pitfalls.md` 同形态，但作用层不同（hook 是 Claude Code harness ↔ 用户脚本，pitfalls 是 PS ↔ native exe）。

## 1. Hook 命令字符串里**只有 Claude Code 自己的占位符变量**会展开

写在 `command` 字段里的字符串被 Claude Code 在执行时做受限替换——**不是 shell 完整变量展开**。

| 占位符 | 展开 | 备注 |
|---|---|---|
| `${CLAUDE_PROJECT_DIR}` | ✅ | 当前 working dir |
| `${CLAUDE_PLUGIN_ROOT}` | ✅ | 当前 plugin 安装根（仅 plugin 场景） |
| `${CLAUDE_PLUGIN_DATA}` | ✅ | plugin 持久数据目录（仅 plugin 场景） |
| `%USERPROFILE%` | ❌ | 字面传递；python 收到字面 `%USERPROFILE%\...` 当路径报 ENOENT |
| `$HOME` / `${HOME}` | ❌ | 同上 |
| `$env:USERPROFILE` | ❌ | 同上 |
| `~/...` | ❌ | 同上 |

**含义**：
- **用户级 skill**（装在 `~/.claude/skills/<name>/`）没有 `${CLAUDE_PLUGIN_ROOT}` 类等效变量——必须在 install 时把绝对路径**bake** 进 settings.json
- **plugin** 可以靠 `${CLAUDE_PLUGIN_ROOT}` 写出可移植的 hook 命令

### Install-time path baking 模板

```powershell
# install.ps1: bake user-level absolute path before writing settings.json
$snippetRaw = Get-Content $SnippetPath -Raw
$userProfileForJson = $env:USERPROFILE.Replace('\', '\\')  # JSON 转义
$snippetRaw = $snippetRaw.Replace('%USERPROFILE%', $userProfileForJson)
$snippet = $snippetRaw | ConvertFrom-Json
# ... merge into settings.json
```

snippet 里 keep `%USERPROFILE%` 占位符方便人读；install.ps1 在写入前替换为运行机器的真实路径。

## 2. Hook exit code: **2 = hard block**，不是 1

| Exit | 行为 |
|---|---|
| 0 | 成功——stdout JSON 被 harness 解析影响后续行为 |
| **2** | **Block**——tool call 被拒，stderr 反馈给 agent |
| 其他（含 1）| 非阻塞错误——stderr 显示，tool 继续执行 |

### 致命场景：自己装的 hook 把自己 lock 住

最危险的 self-deadlock 形态：

1. 你装一个有 bug 的 hook（路径错 / import 缺 / 任何让 script 启动失败的因素）
2. python 启动失败默认 **exit 2**（"can't open file" / `ImportError` / etc）
3. 该 hook 注册在 `PreToolUse` matcher Edit|Write|Bash 上
4. 你想用 Edit / Bash 改 settings.json 修 hook → **每次 tool 都被自己装的 broken hook 拦**
5. 完全无法在 agent 内修复——必须**用户手动**从 `settings.json.bak.*` 恢复

### 防御措施

- **handler 全包 try-except**，永远 `return 0`，让 harness 看到的退出码不会因为内部异常变 2
- 安装脚本提供**自动备份**到 `.bak.<timestamp>`，让 user 能 1 命令回滚
- 测 install 必须用**真 HOME 路径**跑一次，不能只用 temp HOME（temp HOME 让 `%USERPROFILE%` 这种坑藏不住——见 §1）

```python
# multi_session.py 的兜底模板
def main(argv):
    try:
        result = handler(payload)
    except Exception as e:
        print(f"[hook] {hook} failed: {e}", file=sys.stderr)
        return 0   # NEVER 2 — would block agent unexpectedly
    ...
```

## 3. PreToolUse 输出 schema：**`permissionDecision` 不是 `decision: "block"`**

| Event | Block 的字段 |
|---|---|
| `PreToolUse` | `hookSpecificOutput.permissionDecision` ∈ `{allow, deny, ask, defer}` + `permissionDecisionReason` |
| `UserPromptSubmit` / `Stop` | 顶层 `decision: "block"` + `reason` |

**两套不混用**——给 PreToolUse 用 `decision: "block"` 会被 harness 忽略不阻塞。

```json
// PreToolUse deny — 正确
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "deny",
    "permissionDecisionReason": "File X leased by session Y"
  }
}
```

## 4. 上下文注入用 `hookSpecificOutput.additionalContext`

任何 hook 想把内容注入 agent prompt → 写 stdout JSON：

```json
{
  "hookSpecificOutput": {
    "hookEventName": "SessionStart",
    "additionalContext": "Text injected into agent prompt"
  }
}
```

SessionStart / UserPromptSubmit 最常用这个字段。

## 5. Stdin payload 是 JSON，session_id / cwd 等从 stdin 拿

每个 hook 调用 harness 把 JSON 写到 stdin：

```json
{
  "session_id": "uuid",
  "transcript_path": "/path/to/transcript.jsonl",
  "cwd": "current working dir",
  "hook_event_name": "PreToolUse",
  "tool_name": "Edit",
  "tool_input": { "file_path": "...", ... },
  "tool_use_id": "..."
}
```

**不要从 env var 拿 session_id**——只有 3 个 Claude Code 官方 env var（见下），`CLAUDE_SESSION_ID` 不存在。

## 6. 可用 env vars 只有 3 个

| Env Var | 含义 |
|---|---|
| `CLAUDE_PROJECT_DIR` | 当前 project working dir |
| `CLAUDE_PLUGIN_ROOT` | plugin 安装根（仅 plugin 场景） |
| `CLAUDE_PLUGIN_DATA` | plugin 持久数据目录（仅 plugin 场景） |

**没有** `CLAUDE_SESSION_ID` / `CLAUDE_CWD` / `CLAUDE_TOOL_NAME` 之类。这些从 stdin 的 JSON 字段拿。

## 7. `~/.claude/projects/<encoded>/` 路径编码规则**未官方文档**

观察得到的规则（多机验证前**不要依赖**）：
- `:` `\` `/` `_` `空格` → `-`
- 大小写：**部分场景保留，部分场景全小写**——不一致，估计跟实际 disk 路径的 case 有关

**含义**：写 hook 时要存自己的 per-project state，**不要塞进 `~/.claude/projects/<their-encoded>/`**——他们改编码规则你立挂。用自己独立的 root，比如 `~/.claude/<your-name>/<your-encoding>/`，编码算法你自己控。

## 8. Matcher 匹配规则

| Event | Matcher 含义 |
|---|---|
| `PreToolUse` / `PostToolUse` / `PermissionRequest` | 匹配 tool name；支持纯字符串 `Bash` / pipe-OR `Edit\|Write\|MultiEdit` / 含特殊字符时按 JS regex 处理 |
| `SessionStart` | 匹配 session source: `startup\|resume\|clear\|compact` |
| `UserPromptSubmit` / `Stop` | 无 matcher 支持，留空 string |

## 项目实例参考

DialogueSystem 项目（agent_coding_guidelines repo）的 multi-session-coordination skill ship 时撞了 §1 §2 两个坑：
- 初版 settings-snippet.json 写 `%USERPROFILE%\.claude\skills\...` 期望展开 → 装好后 hook 每次 invoke 让 python ENOENT → exit 2 → 整个 Claude Code 对话 Edit/Write/Bash 全 block。详 commit `3ade894`
- 因为 self-deadlock，修法只能让 user 手动从 `~/.claude/settings.json.bak.<ts>` 恢复——install.ps1 提供的自动备份是唯一逃生通道

修法：install.ps1 读 snippet 时 `Replace('%USERPROFILE%', $env:USERPROFILE.Replace('\', '\\'))` 在写 settings.json 之前 bake 绝对路径。每次 sync-skills.ps1 后必须重跑 install.ps1。

## 相关 Guidelines / Techniques

- `guidelines/ci-windows/powershell-native-command-pitfalls.md` —— 同类形态 hidden contract（PS ↔ native exe 的展开陷阱），跟本文是兄弟篇
- `techniques/claude-code-autonomous-permissions.md` —— 改 settings.json 的另一面（permissions ask/allow/deny 块，不是 hooks 块），三种 list 间的 precedence 规则
- `skills/multi-session-coordination/SKILL.md` —— 本文规则的具体应用案例（用户级 skill 装 5 个 hook，绝对路径 bake，handler try-except return 0 防 self-deadlock，permissionDecision 用 deny 不用 block）
