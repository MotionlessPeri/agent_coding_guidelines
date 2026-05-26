# UE MCP 平台选择：fork vs UE 5.8 官方 Model Context Protocol

UE 5.8 引擎随包 ship 了 Epic 官方的 `ModelContextProtocol` plugin + `ToolsetRegistry`
plugin（均 Experimental），覆盖面碾压社区 fork。本文档给"现在 / 新项目分别该用哪个
MCP server"的判断标准 + 关键事实 + 不要走的坑（backport 旧 UE / 抄官方代码到 fork）。

跟 [`skills/ue/unrealmcp-usage`](../../skills/ue/unrealmcp-usage/SKILL.md) 的关系：
那篇 skill 是 **fork 怎么用** 的使用指南；本文档是 **什么时候用 fork、什么时候用官方** 的
**平台选型**。两条不重叠。

---

## 核心结论（决策表）

| 项目使用的 UE 版本 | 推荐 MCP server | 行动 |
|---|---|---|
| 5.7 及之前 | **只能用 fork** | 继续维护现状，不重构 |
| 5.8 及之后（新项目） | **官方 `ModelContextProtocol` 为主** | 直接装引擎自带 plugin |
| 5.8 项目接力自 5.x 旧项目 | **dual server 并存** | `.mcp.json` 同时配两个，日常用官方，整图 dump 等特殊场景用 fork |
| 想"把官方 backport 到 5.7 及之前" | **不要** | License + 工程量双 blocker |
| 想"把官方代码抄到 fork 重构" | **不要** | License 禁止 + 几人月工程量 + 无收益 |

详细论证见下。

---

## 关键事实

### 1. 官方 plugin 5.8 才 ship，旧版本 UE 完全没有

实测 5.2 引擎安装目录 `H:/Epic Games/UE_5.2/Engine/Plugins/`：

| Plugin | 5.2 | 5.8 |
|---|---|---|
| `ModelContextProtocol` | ❌ 不存在 | ✅ Experimental |
| `ToolsetRegistry` | ❌ 不存在 | ✅ Experimental |
| `FileSandbox`（ToolsetRegistry 依赖） | ❌ 不存在 | ✅ Experimental |
| `AIAssistant` | ❌ 不存在 | ✅ Experimental |
| `PythonScriptPlugin` | ✅ | ✅ |
| `HTTPServer` module | ✅ | ✅ |

5.2 只有"底层基础设施"，缺整套 MCP / toolset framework。

5.5 / 5.6 / 5.7 没逐版本 audit，根据 plugin 的 `IsExperimentalVersion=true` flag +
Anthropic MCP spec 公开时间线判断，**5.7 或 5.8 才首次随引擎 ship 的概率极高**。

### 2. 官方 plugin 是 NoRedist + Epic 版权

`ModelContextProtocol.uplugin` 和 `ToolsetRegistry.uplugin` 都标：

```json
"NoRedist": true,
"CreatedBy": "Epic Games, Inc."
```

所有源码 header 标 `// Copyright Epic Games, Inc. All Rights Reserved.`。

**含义**：
- 不能再分发（重新打包给团队 / 客户 / 开源）
- 直接复制源码到 license 不同的 fork 仓库 = license violation
- 自己机器上参考实现思路 OK，写产物给别人 ship 不 OK

### 3. 官方扩展机制：Python 优先，C++ 兜底

官方走 `UToolsetDefinition` 注册体系（不是 fork 的 `IUnrealMCPCommandHandler`）：

**Path A — Python（推荐，低门槛）**：

```python
@unreal.uclass()
class MyToolset(unreal.ToolsetDefinition):
    """Toolset 描述。"""

    @toolset_registry.tool_call
    @staticmethod
    def my_tool(asset: unreal.Object, value: int) -> bool:
        """Tool 描述。

        Args:
            asset: param 描述。
            value: param 描述。
        Returns:
            return 描述。
        """
        ...
```

- Docstring 自动 → tool description + parameter description
- Type hint 自动 → JSON Schema
- 放 plugin `Content/Python/<namespace>/<file>.py`，`init_unreal.py` 触发加载
- **不需编译**，改即生效

**Path B — C++（适合 Python binding 缺失的活）**：

```cpp
UCLASS(BlueprintType, Hidden)
class UMyToolset : public UToolsetDefinition
{
    GENERATED_BODY()
public:
    UFUNCTION(meta = (AICallable), Category = "MyTools")
    static FMyStruct GetSomething(UObject* Asset);
};
```

- `meta = (AICallable)` 注册为 tool
- `meta = (AIIgnore)` 抑制不想暴露的 UFUNCTION（不标的话 UHT 报错）
- 必须 `static`
- 返回 USTRUCT 字段必须 `UPROPERTY(BlueprintReadOnly)` 才能进 schema
- `Build.cs` 加 `"ToolsetRegistry"` 依赖

引擎自带的 C++ 子类只有一个（`UAIAssistantToolset` in `Plugins/Experimental/AIAssistant`），
说明官方推荐 Python 路径。C++ 路径适合：

- 调 `SGraphEditor` / `FBlueprintEditor` / `IMaterialEditor` 等编辑器内部 API
- 操作自定义 `UEdGraph` 状态（graph framework 几乎无 Python binding）
- `FBlueprintEditorUtils::*` 等 framework-internal helper
- 需要 `Modify()` + `FScopedTransaction` 精细 undo 控制
- 批量处理几百几千资产（performance critical）

混合模式：C++ 写底层 AICallable helper，Python toolset 包装业务逻辑。

---

## 三个常见判断

### Q1: 能不能抄官方代码到 fork 重构 / 重写

**不能**，两个独立 blocker：

1. **License 阻断** — NoRedist。fork 自用 + 内部"参考实现"是灰色地带，正式分发或开源
   就是 license violation
2. **工程量不值** — 即使"参考设计自己重写"（不复制文本，避开 license）：
   - 实现一套类 `UToolsetDefinition` UCLASS + `meta=(AICallable)` UHT 集成
   - 实现 USTRUCT → JSON Schema 自动生成（fork 目前手写每个 command schema）
   - 实现 Python toolset 自动注册机制（fork 目前 server 端 dispatcher 是 C++ 写死）
   - 工程量 = **几人月级别**，没人付钱

**实际建议**：fork 保持现状，专注填特定 niche（项目专用 toolset 如 LogicDriver / Dialogue），
不要追官方覆盖面。

### Q2: 能不能把官方 backport 到旧 UE

**技术上勉强可以，license 上不能，实际工程量上不值**：

- 技术上：`ModelContextProtocol` 主模块依赖简单（`Core / Analytics / HTTPServer /
  JsonUtilities / Json`），5.2 全有，理论能拷过去编。`ToolsetRegistry` 依赖
  `FileSandboxCore` 5.2 没有 — 要么 backport FileSandbox，要么砍 sandbox 功能（影响
  `ProgrammaticToolset` / `SlateInspectorToolset`）
- License 上：NoRedist，团队成员之间分享改后产物已属违规
- 工程量：backport 整个 4 plugin 树 + 解决跨版本 API 差异 + 每次 5.8 patch 后同步成本 =
  几人月起跳 + 长期维护负担

**结论**：旧 UE 项目继续 fork，不要走 backport。

### Q3: 5.8+ 项目什么时候可以"抛弃 fork"

抛弃 fork 的 checklist（一项项打勾才有资格）：

- [ ] 所有正在维护的项目都已在 5.8+
- [ ] 官方 MCP 在你工作流里能覆盖 fork 的所有用途（material 整图 dump、custom graph 状态读取、
      LogicDriver 编辑等）
- [ ] 你/团队熟悉 `ProgrammaticToolset` 沙盒 Python 编排（用来替代 fork "一次 dump"这种
      LLM-friendly 接口）
- [ ] 不需要给外部分发"开箱即用 MCP"（开源 fork 可以，官方 NoRedist 不能）
- [ ] fork 的项目 niche 模块（`UnrealMCPDialogue` / `UnrealMCPLogicDriver` /
      `UnrealMCPMaterial`）已用官方 Python toolset 重写或决定放弃

**短期不能 / 长期看场景**。短期 fork 必留（旧 UE 项目刚需）；长期等 5.7- 项目都退役 +
官方覆盖完 fork niche → fork 自然过时，不需要主动"抛弃"。

---

## 官方 vs fork 详细对比

| 维度 | fork (`UnrealMCP`) | 官方 (`ModelContextProtocol` + `ToolsetRegistry`) |
|---|---|---|
| 引擎版本 | 5.5+ 实测 OK，5.2 靠 patch | **5.8+ only** |
| 实现语言 | C++（10815 行 commands 总计） | Python 为主（core toolsets 5335 行 Python） + C++ thin UCLASS base |
| Tool 注册 | C++ `IUnrealMCPCommandHandler` + `FUnrealMCPCommandRegistry` 全 C++ | Python `@toolset_registry.tool_call` 装饰器自动注册 + C++ `UFUNCTION(meta=(AICallable))` |
| Tool 数量 | 几十个（按 BP/UMG/Material/Animation/BehaviorTree 几个 domain） | 46 个 toolset × N tool/toolset，覆盖几乎全 Editor 系统 |
| 写入完整度 | 偏 inspect / dump | **完整 CRUD** 每个 toolset 都有写入 API |
| 读取风格 | "单次 dump 整图"（material/BP graph） | "ObjectTools 通用反射 + 多 round trip" |
| Schema 生成 | 手写每个 command 的 inputSchema | docstring + type hint 自动生成 |
| License | fork 自己（社区 fork from chongdashu/unreal-mcp） | **NoRedist + Epic 版权** |
| 维护成本 | 跨 UE 版本升级要手 patch | 跟引擎升级走 |
| 扩展机制 | 改 fork C++ 源码 + 同步 sync 脚本到项目 | Python 加文件即生效 / C++ 加 UCLASS |
| 特色 | Substrate 节点专向 dump 优化、`UnrealMCPDialogue` 等 niche 扩展 | `ProgrammaticToolset` 沙盒 Python、`SlateInspectorToolset` Playwright 风格 UI 自动化、Sequencer 8 toolset 完整覆盖、GAS 5 toolset 完整覆盖 |
| 适合场景 | LLM 一次性吃整图做 high-level 分析 | LLM 在 Editor 里做"工程师"细粒度操作 + 编排 |

---

## 演进路径（建议）

### 短期（现在 - 6 个月）

- **旧项目（5.7-）**：fork 唯一选择，继续维护
- **5.8+ 项目**：dual server 并存（`.mcp.json` 同时配两个），日常用官方
- **新项目接入**：5.8+ 直接装官方，5.7- 继续装 fork

### 中期（6-12 个月）

- 5.8+ 项目用官方覆盖大部分场景后，从 `.mcp.json` 删 fork server 段，正式切单官方
- fork 不再扩 core 框架（dispatcher / 通用机制），但可以补 niche 模块（特定项目专用 toolset）

### 长期（1 年以上）

- 等 5.7- 项目全部退役 → fork 自然没人用 → 退役
- 不需要主动"抛弃 fork"，让它随项目代际更替自然过时

---

## Anti-Patterns

| 反 pattern | 为什么错 |
|---|---|
| "官方好我就抄过来重写 fork" | License 违规 + 几人月工程量 + 无明确收益 |
| "把官方 backport 到 5.5 让团队都能用" | 同上 + 跨版本 API 差异 + FileSandboxCore 等 5.8 新模块缺失 |
| "fork 跟官方功能重叠的部分立刻删掉" | fork niche 模块（Dialogue / LogicDriver / Material dump）官方还没覆盖 / 风格不同，断 fork 影响项目正常工作流 |
| "5.8 项目装了官方就把 fork 那边的 unrealMCP 立刻从 .mcp.json 删掉" | 短期切单边没有意义。fork 整图 dump 在分析场景仍有 token 优势，dual 零冲突，等不再用 fork tool 再删 |
| "用官方就一定要走 Python toolset，不要 C++" | C++ 路径官方明确支持（`UToolsetDefinition` + `AICallable` UFUNCTION）。`SGraphEditor` 内部状态 / 自定义 UEdGraph 读取这类必须 C++ |

---

## 相关 Guidelines / Skills

- [`skills/ue/unrealmcp-usage/SKILL.md`](../../skills/ue/unrealmcp-usage/SKILL.md) — fork
  的使用指南（什么时候 detect 项目装了 fork、用 TCP `ue_cmd.py` 怎么调、扩 fork 时
  两侧同步规则）。本文档管"用哪个"，那条 skill 管"fork 怎么用"
- [`guidelines/ue/external-automation-write-path.md`](external-automation-write-path.md) —
  任何外部脚本（MCP / Python commandlet / Editor Utility Widget）写入 UE 资产必走
  `PostEditChangeProperty` 同步路径。fork 和官方 MCP 都必须遵守这条
- [`guidelines/ue/build-plugin-limitations.md`](build-plugin-limitations.md) — UE plugin
  打包分发的两个 limitation，跟 fork ship 给团队成员相关
- `skills/ue/ue-reference-engine-source/SKILL.md` — 写 UE 功能前先找 reference 实现。
  本文档关于官方 MCP 扩展机制的判断（C++ Path B 适合什么场景）就来自读 engine source
  `Plugins/Experimental/AIAssistant/Source/AIAssistant/Private/AIAssistantToolset.h` +
  `Plugins/Experimental/ToolsetRegistry/Source/ToolsetRegistry/Public/ToolsetRegistry/ToolsetDefinition.h`

## 项目实例参考

UE 5.8 项目 `Painting_Test_5_8`（接力自 5.2 `Painting_Test_5_2`）2026-05-25 一次性
完成了官方 MCP 加载验证：

1. 官方 ModelContextProtocol plugin 启用 + HTTP server listen `127.0.0.1:8000`
2. Claude Code `.mcp.json` 配 dual server（`ueOfficialMCP` HTTP + `unrealMCP` stdio）
3. 实测官方 `SceneTools` / `ActorTools` / `BlueprintTools` / `ObjectTools` 4 个 toolset
   + 73 个具体 tool，全部跑通：spawn 4 actor → 设 mesh → outliner 文件夹 → 创建 BP +
   Component + Variable + Function + Compile → spawn BP instance
4. 验证 5.2 引擎装目录确认 `ModelContextProtocol` / `ToolsetRegistry` / `FileSandbox` /
   `AIAssistant` 4 个 plugin 在 5.2 完全不存在

调研过程结论是本文档的成文依据。
