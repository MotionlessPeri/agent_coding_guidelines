# Reuse Before Implementing

## 核心规则

实现新功能或修复缺陷前，围绕当前功能、调用方和相关模块查找已有实现；已有且仍有效的调查结果可以复用，不要求每次巡视整个代码库。重点确认：

- **已有实现满足当前契约**：核实正确性、前提和副作用后优先复用，避免无理由另写一份。
- **流程近似但参数或行为有差异**：判断共同职责是否稳定；公共 helper、模板或基类是候选方案，不是发现相似后的必选动作。
- **局部相似的代码段**：检查是否需要共同变化，再权衡保留重复与提取函数的成本。

跟 `clarify-before-implementing.md` 互补：那条处理影响结果的需求歧义，本条查找或排除复用对象。调查范围服务于当前决定，不自动增加规划审批或无关探索。

**抽象层级对应**：复用的 survey 有三个层级，从近到远：

| 层级 | survey 什么 | 由谁管 |
|---|---|---|
| **helper / function 级** | grep 本仓库现有函数 / helper | **本条 guideline** |
| **架构 pattern 级** | "流程跟 X 像不像 / 要不要走 X 的 base class" | 当前项目已有的架构资料或模式目录；相关技能仅在能解决当前设计问题时按需使用 |
| **框架侧 reference impl 级** | 本机随装的 SDK samples 与头文件里，官方是怎么做这件事的 | **本条下面那一节** |

三者互补，但不是固定读取顺序。局部函数修改通常只需查看相关实现；涉及架构选择或不熟悉的框架契约时，再查对应资料。目录或技能不存在时，不要求补建，也不自动调用其他工作流。

## 框架侧 reference impl：按问题查目标版本的样例与头文件

涉及不熟悉、变化或可疑的 DCC / 引擎 / SDK 契约时，可从本机目标版本的 samples 与头文件查起；已有适用于当前版本和调用路径的有效证据可以复用。先确认实际安装版本与资料来源，不能仅因文件在本机就认定版本匹配。

**为什么**：样例与头文件能补充官方说明中的用法和调用前提，目标版本的实际代码也有助于排除跨版本推测。样例是否适用仍取决于对象类型、配置和执行路径；公开契约可先查对应版本的官方文档，不把资料载体排成固定读取顺序。

**动作**：需要本地证据时，定位安装目录下相关的 samples / devkit / include，按当前问题找定义、调用者和相近样例；没有随装资料时再查对应版本的其他来源。无需每次重复巡视安装目录。

**实测的随装情况**（同一台机器核销，供估计概率用）：

| 宿主 | 随装 |
|---|---|
| MotionBuilder 2018 / 2019 / 2022 / 2023 | 四个版本**全部**随装 `OpenRealitySDK/Samples/`（含十余个设备样例） |
| Maya 2022 / 2024 / 2025 | 随装 `devkit/` |
| 3ds Max 2024 | 顶层**无** maxsdk —— SDK 是可选安装组件 |

⇒ "随装"不是普适前提（Max 就不成立，Houdini / Blender 未核），所以这条是**先查一下**，不是**假定有**。

**跨域经验**：UE 域的[查证方法与案例](../../skills/ue/ue-reference-engine-source/reference-engine-source.md)强调证据须适用于目标版本与调用路径；不熟悉、变化或可疑的契约需要查证，已有有效证据可复用，不把源码与 API 文档简单对立。MoBu 域原记录中，一个"设备插件怎么写、跨版本有无差异"的问题，本来要靠旧版本经验加网络搜索推测，`ls` 一下发现 **2023 SDK samples 里就有正好对应那个场景的完整官方实现**，由此获得了对应场景的直接参考，并顺带在头文件注释里核销了四项 API 事实。

⚠️ **这曾是本语料库的结构性覆盖漏洞**：机制框架无关，却只在 UE 域被写下（`guidelines/maya/` 对 samples / reference impl 零命中，尽管 Maya 也随装 devkit）⇒ 做 Maya / MoBu / 其他宿主的 agent 不会想到去查。所以它落在这份框架无关的文件里，UE skill 作为该层级的域内实例。

## 跟"premature abstraction"的边界

[`guidelines/code/constraints.md`](../code/constraints.md) "Simplicity" 节：

> Three similar lines of code is better than a premature abstraction.

跟本条**不冲突**，是同一光谱不同位置：

| 时机 | 该做什么 |
|---|---|
| **第一次写**（还没有同类代码）| 实现当前需要；有清晰职责时可以拆单一调用方使用的函数，不为假想调用方设计通用接口 |
| **发现第二处相似实现** | 对照语义、依赖和副作用，判断复用是否能减少共同维护成本 |
| **多处代码需要同步修改** | 这是提取公共实现的有力信号；仍需确认共同契约，而非仅按出现次数抽象 |

防的是两端：
- **过早抽象**：为不存在的需求加入参数、继承层次或通用接口。
- **重复堆叠**：同一职责在多处实现，需要同步修正却没有合理的维护边界。

调用方数量是线索，不是抽象是否合理的判据；按职责拆分和跨调用方复用也不是同一件事。

## 什么时候 survey

新建一个文件 / 类 / helper 之前，确认 codebase 里有没有它的"近亲"：

| 信号 | 该 survey 的关键字 |
|---|---|
| 要写一个新的 modal / dialog | grep 现有 `S*Dialog` / `S*Modal` / 看是否有可复用的容器 |
| 要做"调外部 process + 收集 stdout/stderr" | grep `CreateProc` / `ReadPipe` / 已有 helper |
| 要做"打开数据库 + 跑 query + 关连接" | grep RAII guard / 现有 DB 访问层 |
| 要做"asset list + filter + 排序" | grep 类似 list widget / 现有 panel |
| 要做"数据 import + dry-run + apply 两阶段" | grep 现有 pipeline 入口 |
| 要做"反向索引 entity → owners" | grep registry / index 类 |
| 要做"per-row UI 状态展开 / 折叠" | grep `SExpandableArea` 现有用法 |
| 要写一个 `UEditorValidatorBase` / `UFactory` / `UAssetDefinition` 子类 | grep 同 base class 现有子类 |

通用 survey 工具：
- `grep -r` / ripgrep 关键字
- 类继承图：`UFunction → ` 接口或 `class Foo : public X` 已有子类
- Agent 调度：把"找 codebase 里所有做 X 的地方"丢给 Explore / Grep agent

## 找到 similar code 后的决策树

```
找到 N 处相似代码
  ├── 契约、前提与副作用一致
  │     → 核实正确性后优先复用；多处需要共同维护时评估公共实现
  │
  ├── 流程一致但内层有差异
  │     → 判断差异是否适合一个稳定接口
  │       只有确有收益时才提取 helper / template / strategy
  │
  ├── 表面相似但语义不同（参数含义 / 副作用不一致）
  │     → 不要勉强复用
  │       差异不明显且容易被误改时，简短说明关键原因
  │
  └── 只看到文本重复，尚未确认共同职责
        → 先查调用上下文，不按重复次数或相似行比例决定抽象
```

## 复用之前先验它是否**正确**，不只读懂它的副作用

反模式 3（下面那条）说"复用前读懂被复用函数的全部副作用"。还要往前一步：**先验它对不对。** 因为一段错误实现可以长期不崩、不报错、测试也不红，条件有两种：

| 形态 | 为什么原地无害 |
|---|---|
| **输出被覆盖** | 错的值算出来了，但真正生效前被另一条路径整个盖掉，于是错误从不表现 |
| **全链一致地错** | 某个约定（旋转序 / 单位 / 分量序）声明了却没实现，全链都用同一个默认值，彼此自洽所以功能正常 |

这两种代码在原地是无害的，**危害在被继承的那一刻产生**：新实现照抄它（以为它对），或者只抄一半（打破了那个"全链一致"）。此时错误第一次显形，而显形位置离根因很远——你会在新代码里查一个其实是从旧代码继承来的假设。

之所以需要一条明写的规矩：**常规判断手段全部失效**——这段代码有注释、命名合理、被真实调用、功能也确实在跑。想发现它只能反过来问：

- **谁读它的输出、读之前发生了什么？**（追到真正生效的那一点，看有没有被覆盖）
- **这个配置字段的读取点在哪？**（grep 字段名；解析进结构体之后再无读取点 = 声明了但没实现）

实测两个实例（同一仓库、机制不同，不是同一个坑踩两遍）：一个"局部转全局"的矩阵函数把入参在函数内覆盖后自乘，算出的是父变换的平方、骨骼自身的成员从未参与——而结果在首帧被整块缓冲覆盖，所以对最终画面零影响，**静静活了整个项目周期**；另一个配置文件声明了旋转序，解析进字段后再无任何读取点，全链走框架默认序，两侧一致所以姿势正确。代价是：**若不追到覆盖链条，就会把一个错误实现当作参考实现递给下游**，而下游没有源码上下文，无法自行发现。

> 同族的另一种形态（不单列成条）：**锁的范围和函数的调用位置，隐含着对函数体大小的假设；函数体随演化增长时这个假设静默失效，而代码形态上看不出异常**——锁还是那一行，调用点还是那一处。实测形态是一个只做数据搬运时合理的"整函数加锁 + 在实时回调里调用"，后来被塞进了重计算。

## 复用决策记录

只有不复用的理由不明显、预计会影响后续维护判断时，才在已有审查记录、PR 说明或相应代码附近简短解释。普通局部选择无需新增记录或注释。例如：

```cpp
// NOTE: 看起来跟 ParseXlsxBatch 的 subprocess 逻辑相似，没复用 PythonSubprocessHelper 是因为
// 这里需要返回 stderr 给 caller 做交互式 prompt，helper 当前签名只暴露 exit code。
// 两者的错误交互契约不同，当前分别实现。
```

说明当前契约差异即可，不必承诺未来统一，也不要求每次选择都提交一份复用说明。

## Anti-Patterns

### 1. Copy-paste 进入 codebase

```
版本 1: ParseXlsxBatch 内联 660 行 subprocess 逻辑
版本 2: ParseTranslationsBatch 又写一遍同样 660 行
版本 3: ExportDialogueToXlsx 再写一遍
版本 4: ParseSomethingElseBatch 又来一遍
```

每次新增 caller 都是 660 行膨胀；某次 subprocess timeout 行为要改，4 处都得改且容易漏。

**修法**：发现相同 subprocess 契约需要在多处同步维护时，评估提取公共实现；重点是共享的超时、输出和错误处理行为，不是第几处出现。

### 2. 各自实现"看起来相似但实际相同"的功能

两个 dev / 两个 agent 各自实现"打开 DB → 查表 → 返回"的逻辑，签名不同、错误处理不同、close DB 时机不同——后面接 caller 时困惑两套用哪套。

**修法**：开工前 survey；如果发现已经有人在做同类工作，先沟通 / 合并工作流。

### 3. 错误的复用（强行套用语义不同的"近亲"）

发现一个 `OnFooChanged` callback 看起来跟新需求差不多就直接复用——但实际 `OnFooChanged` 有副作用（清缓存 / 触发其他事件），新需求不需要副作用反而被坑。

**修法**：复用前**读懂被复用函数的全部副作用**。如果副作用不匹配，宁可分开实施。

### 4. "抽完才发现不该抽"

刚抽完 `Helper::DoX` 就发现只有一处 caller 用得到，其他 caller 参数都不一样硬塞参数。

**修法**：用真实调用场景检查接口是否自然，不为"未来可能的 caller"硬塞参数。只有一个调用方的函数，也可以因职责清晰、降低复杂度而值得提取；没有第二个调用方不构成撤销拆分的理由。`constraints.md` 的 "Simplicity" 防的是没有当前需求支撑的通用化。

## 项目实例参考

DialogueSystemSample 插件 3 个月开发期间，下列复用 / 抽公共代码都来自"发现已有 similar 后动手前 surface 出来"：

| Helper / 基类 | 来源 |
|---|---|
| `PythonSubprocessHelper::RunPythonImportSubprocess` —— 抽 ParseXlsxBatch 的 660 行 subprocess 逻辑（path 校验 / CreateProc / 30s 超时 / exit code / MessageLog），后续 ParseTranslationsBatch / ExportDialogueToXlsx 复用 | I-007 / commit `a56dd1d`（v0.5.1）|
| `FScopedSQLiteDb` RAII guard —— 5 处 query callsite 各自 `Db.Close()` 容易漏 stmt finalize；统一 RAII 让 Stmt 先析构、Database 后析构 | commit `e8c9347`（v0.5.1）|
| `SDialogueXlsxBatchSelectDialog` 独立 header —— 一开始只 Lines import 用；Translation import 后来复用同一 modal | commit `4ea4c6c`（v0.5.1）|
| `FStateGraphAssetEditorBase` 基类 —— DialogueAssetEditor / ManagementAssetEditor 共用工具栏 / 节点 customization / undo client 注册等 | v0.4.5 → v0.4.6 |
| `SComboButton + SPathPicker popup` pattern —— I-005 修 Import preview modal AssetPath 输入后，commit `4d1e387` 把 Sidecar Bulk Create directory 输入也换上同 pattern | commits `dc779b2` + `4d1e387` |
| `FillTopologyFromRows<RowT>` template helper —— `BuildTopologyFromDB` + `BuildTopologyFromLineRegistry` 同样"按行结构填 topology"的逻辑抽 template | commit `ce43071`（Phase 2 review F10）|

反例：I-007 之前 660 行 subprocess 在 ParseXlsxBatch 内联了好几个月，到 Phase 3 要写第 2 个 / 第 3 个 subprocess caller 时才由用户指出可以抽 helper。这个案例的复用依据是共同的进程执行与错误处理契约，不是“第二个调用方出现就必须抽象”。

## 相关 Guidelines

- [`guidelines/code/clarify-before-implementing.md`](clarify-before-implementing.md) —— 对称的另一条 prep work（澄清需求 vs survey 现有代码）
- [`guidelines/code/constraints.md`](constraints.md) —— "Simplicity" 节防 premature abstraction，跟本条互补
- [`guidelines/workflow/agent-lifecycle.md`](../workflow/agent-lifecycle.md) —— 围绕具体疑问读取代码，再行动或验证；本条用 survey 找到或排除复用对象，支持下一步决策，避免无目的重复探索
