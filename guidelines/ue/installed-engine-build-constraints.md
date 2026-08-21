# Installed（发行版）引擎的构建约束：三道墙都能穿，别停在"这个 distribution 不支持"

**installed / distributed build**（`Engine/Build/InstalledBuild.txt` 存在的引擎——Epic Launcher 装的、
或公司自建源码打出来的发行版）会拒绝一部分 target 类型：

```
Game targets are not currently supported from this engine distribution.
Program targets are not currently supported from this engine distribution.
```

**这条报错是 UBT 的拒绝，不等于"编不出来"。** 撞到它时先分清两件事：

| | 判据 | 处置 |
|---|---|---|
| **UBT 拒绝** | 报错文本就是上面那句，来自 distribution 检查 | 本文件——要么绕开（改用被开放的 target），要么穿过去（下面那条路径） |
| **真的编不出来** | 缺源码 / 缺 SDK / 平台不支持 | 换引擎，本文件帮不上 |

> **这条曾是本语料库的一个错误结论。** [`build-plugin-limitations.md`](build-plugin-limitations.md)
> Limitation 4 原来的处置是"接受 editor-only，或换开放 Game target 的引擎"，并在反模式表里把
> "改引擎的 installed 标记"标成风险过大的做法。**那个结论对 `BuildPlugin` 场景成立**（那里有
> `-NoTargetPlatforms` 这个干净得多的绕法），但被写成了对整个 distribution 的能力断言 —— 而**当时
> 没有人试过能不能穿过去**。实测穿过去了：76 秒并行编译、link 零错、产物在真实链路端到端跑通。
> 这是 [`../code/reporting-limits-and-null-results.md`](../code/reporting-limits-and-null-results.md)
> 规则 1「这个『做不到』是对某个解法证明的，还是对整个层证明的」的一次实际命中。

---

## 先试绕开：走被开放的 target

installed distribution 通常**开放 Editor target**（它自己就是一个 installed editor）。所以：

- **走 `RunUAT BuildPlugin`** 时，`-Rocket` 默认还会给每个目标平台编 `UnrealGame` → 撞墙。传
  **`-NoTargetPlatforms`** 只编 editor host target 即可，代价是包里没有 game/runtime 二进制。
  完整说明见 [`build-plugin-limitations.md`](build-plugin-limitations.md) Limitation 4。
- **editor 工具型插件到此为止**，不需要读下面。

下面那条路径是给**绕不开的场景**的：要编的就是 Program 或 Game target 本身（例如一个把引擎某模块
编成独立 exe / dll 的第三方桥接插件），而手上只有发行版引擎。

---

## 穿过去：三道独立的墙，按顺序撞到

⚠️ **先读本文件末尾的副作用与边界。** 其中第 2 道墙的解法在窗口期内会改变**整个引擎对所有进程**的
表现——共享机器 / CI runner / 编辑器正开着时**不要照做**。

### 墙 1：rules assembly 根本不重编（改了没反应）

**症状**：加了新的 `*.Target.cs`，UBT 报
`Expecting to find a type to be declared in a target rules named 'XTarget'` —— 你的文件明明在那儿。

**根因**：`DynamicCompilation.cs:33-40` 的 `RequiresCompilation()` 开头就是

```csharp
if (UnrealBuildTool.IsFileInstalled(OutputAssemblyPath))
    return false;
```

引擎目录下的 `UE5ProgramRules.dll` 被判定为 installed ⇒ **任何源码改动都不触发重编**。

**修法**：`-SkipRulesCompile -ForceRulesCompile` **两个开关一起传**。

看起来矛盾，但这是必须的 —— `CompileAndLoadAssembly()` 的执行顺序（`DynamicCompilation.cs:301-305`）是：

```csharp
bNeedsCompilation = ForceCompile;
if (!DoNotCompile)
    bNeedsCompilation = RequiresCompilation(...);   // ← 把上一行整个覆盖
```

**只传 `-ForceRulesCompile` 会被第二行覆盖掉**；必须用 `-SkipRulesCompile` 让它跳过那次覆盖。

> **同一个短路的另一副面孔（跨项目两击）**：另一个项目撞的是"**误删**了 installed build 的预编译
> `UE5Rules.dll` 之后报 `Precompiled rules assembly does not exist`，而 installed build 不会自动重建"。
> 一个是"删了不会重建"、一个是"改了不会重编"，**症状完全不同、根因是同一条语句**。⇒ 记住这条短路
> 本身，而不是记住某一种症状。

### 墙 2：target 类型白名单

**根因**：`UEBuildTarget.cs` 按 `InstalledPlatformInfo` 校验 target type，不在白名单就 throw
（UE 5.3 在 `:1277-1285`，UE 5.8 在 `:1403`，**同一条语句**）。白名单来自 `Engine/Config` 的
`[InstalledPlatforms] HasInstalledPlatformInfo`，而它**只在 `Unreal.IsEngineInstalled()` 为真时生效**
（`InstalledPlatformInfo.cs:335`）。

**修法**：构建窗口内把 `Engine/Build/InstalledBuild.txt` **临时改名**，构建完**立即还原**。

⚠️ 这是本文件里唯一有全局副作用的一步，见末尾边界。

### 墙 3：launcher 版裁掉了 Core 依赖的三方源码

**这道墙是 launcher 版特有的**；公司自建源码构建的 installed build 有完整三方源码，不会撞。

**症状**：编 Core 必挂，因为 `Engine/Source/ThirdParty/` 下有几个库只剩壳：

| 库 | 实际留下的 |
|---|---|
| `SSEMathFun` / `xxhash` | **只有 `.tps` 许可文件** |
| `mimalloc` | 只有 `include/`，**没有 `src/`** |

而 Core 的三个编译单元硬 include 它们。

> 顺带：这正是 [`../code/reporting-limits-and-null-results.md`](../code/reporting-limits-and-null-results.md)
> 规则 3「镜像形态」的实例 —— `ls -d` 查这三个目录**全部存在**（许可要求文件必须留着，所以骨架一定在），
> 据此报"三方源码齐全、问题在别处"是**系统性的假阳性**。要往里查一层具体文件。

**修法**：

- `SSEMathFun` / `xxhash`：从公开上游补齐（xxhash 也可从本机更新版本的引擎拷 —— 实测 0.8.0 无 Epic 补丁）。
- `mimalloc`：**不能用上游替换** —— 它的 `include/` 带 Epic 私有补丁（`// BEGIN EPIC MOD`）。改为在
  `Core.Build.cs` 里临时把 `PLATFORM_BUILDS_MIMALLOC=1` 改成 `0`（插件退回默认分配器，无功能影响）。

⚠️ 改引擎目录里的文件时，**不要用 `sed -i`** —— 见
[`../ci-windows/posix-tools-on-windows.md`](../ci-windows/posix-tools-on-windows.md)：它不是原地编辑，
会改掉全文件行尾、还能穿透只读属性且不留痕。先整文件备份，还原走覆盖 + 字节比对。

---

## Anti-Patterns

| 反 pattern | 后果 | 修法 |
|---|---|---|
| 撞到 `... targets are not currently supported` 就去查插件代码 / 模块 type | 查错方向（是**引擎 distribution 的检查**，不是插件问题） | 认准这句话来自 UBT 的 distribution 校验 |
| 把它读成"这个引擎编不出来"，直接要求换源码构建引擎 | **一个错误的放弃** —— 实测能穿过去 | 先按上面三道墙评估；editor 工具插件先试绕开 |
| 反过来：把"能穿过去"读成"UE 支持在 installed 引擎上编这些 target" | 下游以为开箱即可，而实际要三处临时改动 + 一个全局副作用 | 报这条能力时**必须连代价一起报**（见下） |
| 只传 `-ForceRulesCompile` | 被 `RequiresCompilation()` 覆盖，rules 仍不重编 | 两个开关一起传 |
| 在共享机器 / CI runner / 编辑器开着时改名 `InstalledBuild.txt` | 窗口期内**整个引擎对所有进程**都表现为非 installed | 只在单人本机、短窗口内做，做完立即还原 |
| 用 `sed -i` 改引擎文件 | 全文件行尾被改；只读属性拦不住它且无痕 | 用编辑工具；必须用时先整文件备份 + 字节比对还原 |

## 诚实边界

- **副作用**：改名 `InstalledBuild.txt` 的窗口内，该引擎对**所有**进程都表现为非 installed build。
  实测那次是单人本机、窗口 76 秒。**这条必须跟做法一起读，否则照抄会出事。**
- **验证范围**：只在 **UE 5.3.2 launcher 版 + Program target** 上验证。**Game target 能不能同样穿过去
  没试** —— Limitation 4 对 Game target 的结论可能仍然成立。
- 墙 3 是 **launcher 版特有**；自建源码 installed build 不会撞。
- 补进引擎目录的三方头文件来自公网上游，**与 Epic 内部用的是否逐位一致未核**（编译通过 + 产物跑通，
  但没做 ABI 层面比对）。Epic Launcher 的 "Verify" 可能覆盖这些改动。
- **报这条能力时的措辞纪律**：写"有一条实测可行的穿越路径，**代价是三处临时改动 + 一个全局副作用**"，
  不要写"UE 支持在 installed 引擎上编 Program target"。差别就是那句代价 —— 见
  [`../code/reporting-limits-and-null-results.md`](../code/reporting-limits-and-null-results.md)
  规则 1 的反方向（把自己这层的扩展说成下层框架的能力）。

## 相关 Guidelines

- [`build-plugin-limitations.md`](build-plugin-limitations.md) —— `RunUAT BuildPlugin` 场景的四个 limitation；
  Limitation 4 是本文件那道墙在 BuildPlugin 流程里的表现，含 `-NoTargetPlatforms` 绕法
- [`../code/reporting-limits-and-null-results.md`](../code/reporting-limits-and-null-results.md) —— 规则 1
  （"做不到"要说清哪一层、对哪个解法）；本文件的更正就是那条规则的一次命中
- [`../ci-windows/posix-tools-on-windows.md`](../ci-windows/posix-tools-on-windows.md) —— 改引擎 / SDK
  目录里的文件时的工具约束
- skill `ue-reference-engine-source` —— 本文件三道墙的根因全部来自读 UBT 源码，不是从文档得到的
