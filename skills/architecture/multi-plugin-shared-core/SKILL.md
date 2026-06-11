---
name: multi-plugin-shared-core
description: Framework-agnostic architecture for systems where multiple plugins / features share one core entity (e.g. multiple DLLs over a common base layer). Six composable patterns — (1) type-keyed ExtensionContainer instead of subclass explosion, (2) feature-parser registry so the base layer has zero dependency on plugins, (3) Preset→Template→Instance data-driven three-stage init with a factory between layers, (4) Snapshot-as-data-hub + Ops-namespace separation instead of a god base class, (5) non-owning runtime Registry as the single lookup entry to decouple commands from any specific tool/context, (6) when the authoritative type is non-extensible (vendored / submodule / owned by another team), encode editing-/UI-only state by repurposing an existing value rather than forking the type or adding a parallel field that ripples through serialization/undo. Use when designing or extracting a multi-feature plugin system, deciding how features attach data to a shared object, or reviewing a "base layer + N plugins" architecture. Validated in one Maya multi-.mll project; treat as patterns to apply-and-refine, not hard rules.
when_to_use: Fires when (1) designing a system with a shared core/base layer and multiple feature plugins or modules attaching their own data, (2) deciding whether a new feature should subclass the core or attach via extension, (3) building config/preset loading where different presets carry different optional features, (4) designing undo/data-transfer around a value-like snapshot, (5) deciding where runtime entity lookup should live (central registry vs a tool's context), or (6) reviewing/refactoring a "god base class" that accumulates every feature's methods. Skip for single-plugin or single-module systems with no shared-core extensibility need.
---

# Multi-Plugin Shared-Core Architecture

五个**可组合**的架构模式，解决同一个问题：**多个插件/功能共享一个 core 实体，又不想让 core
知道每个插件的细节、也不想继承爆炸**。框架无关（在 Maya 多 `.mll` 场景提炼，但内核与 Maya
/ 动画无关，UE module / 通用 plugin 系统同样适用）。

> ⚠️ 状态：单项目验证。属于"应用并精炼"的 pattern，不是硬规则。第二个相关项目应验证 + 修正。

| 模式 | 一句话 |
|------|--------|
| 1. ExtensionContainer | core 实体带 type-keyed 扩展容器，替代"每 feature 一个子类" |
| 2. Feature-parser 注册制 | base 零依赖；各插件注册 parser 解析自己的配置段 |
| 3. Preset→Template→Instance | 数据驱动三段式初始化，层间各一 factory |
| 4. Snapshot + Ops | 数据（value-like）与操作（namespace 自由函数）分离 |
| 5. 非拥有 Registry | 命令走中央 Registry 查询，不耦合某个工具 context |
| 6. 编辑层 state 复用既有值 | 权威类型不可扩展（vendored/子模块/他队拥有）时，编辑/UI-only state 复用既有枚举值标记，别 fork 类型也别加并行字段 |

---

## 1. ExtensionContainer：type-keyed 扩展替代继承爆炸

**问题**：一个 core 实体（如 `CharacterInstance`）要被多个独立插件扩展。用继承会爆炸：
`Bezier + FootFix + Diffusion` 组合需要 N 个子类 / 多重继承 / 菱形。

**模式**：core 持有一个 `key → IExtension` 容器：

```cpp
struct IExtension { virtual ~IExtension() = default; };

class ExtensionContainer {
public:
    void setExtension(const std::string& key, std::shared_ptr<IExtension> ext);
    bool hasExtension(const std::string& key) const;
    template<typename T> T* getExtensionAs(const std::string& key) const {
        return dynamic_cast<T*>(getExtension(key));   // null-safe
    }
private:
    std::unordered_map<std::string, std::shared_ptr<IExtension>> extensions_;
};
```

每个插件定义 `XxxExtra : IExtension`，初始化时挂上。消费方 `obj->getExtensionAs<XxxExtra>("xxx")`。

**收益**：无继承复杂度；feature 自包含独立开发；新 feature 只注册不改 core（开闭原则）。
**代价**：key 是字符串无编译期检查；访问要转型 + null 检查（用 `requireXxx()` 包一层 + assert 兜底）。
**热路径注意**：别在逐帧循环里反复 `getExtensionAs`（dynamic_cast 开销），循环外缓存——见
[`../../../guidelines/cpp/hot-path-cpp.md`](../../../guidelines/cpp/hot-path-cpp.md)。

## 2. Feature-parser 注册制：base 零依赖

**问题**：传统做法 base 的配置类直接声明所有 feature 字段（`ikModelPath` / `footData` / ...）→
base 依赖每个插件，加第 N 个 feature 要改 base 头。

**模式**：base 只提供抽象 parser 接口 + registry，各插件主动注册：

```cpp
struct IFeatureParser {
    virtual std::shared_ptr<IExtension> parse(const Json& root) = 0;  // nullptr = 此配置无该 feature
};
// base 加载配置时：for (parser : registered) if (auto ext = parser->parse(root)) entity.setExtension(key, ext);
// 插件 startup: Registry::registerParser(make_unique<FootFixParser>());
// 判断有无 feature 统一用 entity.hasExtension("footfix")
```

**收益**：base 完全不知道插件存在；新插件 0 改 base；运行时动态（插件先加载才注册）；feature 可选
（配置缺字段 → parser 返回 nullptr）。**用字段存在性判断 feature，不要用 version 号判断。**

## 3. Preset→Template→Instance：数据驱动三段式

```
Preset(声明式配置, JSON)  --factory-->  Template(按配置初始化, 可共享)  --factory-->  Instance(运行时)
```

- 三层都继承 ExtensionContainer，各自挂自己的 Extra
- **Extension 归属**：通用/共享数据（如模型 handle）放 Template 层；实例独占状态（如缓存）放 Instance 层
- **初始化顺序**：Preset 加载 → Template 创建 + postInit → Instance 创建 + 把 Template 层扩展 applyTo(instance) → Instance 层初始化。**顺序打破**（instance 创建后才注册 Template 扩展）→ 新 instance 看不到该扩展；用 assert 在 applyTo 里兜底

## 4. Snapshot + Ops：数据与操作分离

**问题**：一个"超级基类"承载所有 feature 的转换方法 → 编译耦合 + 难测。

**模式**：核心数据结构保持**纯数据 + 通用查询**（value-like，可拷贝/进 undo stack/跨流程传）；
feature 专用操作拆成 namespace 自由函数：

```cpp
class Snapshot { /* 纯数据 + getJoint / frameCount ... */ };
namespace BezierSnapshotOps { void fillX(const Snapshot&, ...); }
namespace IkSnapshotOps     { void buildFromIk(...); }
```

**收益**：避免 RTTI/向下转型；Ops 文件各归各插件目录、无编译耦合；Snapshot 作为"数据中枢"屏蔽
底层 API（采集 Builder / 应用 Applier / 操作 Ops 三者分离）。core 的"私有数据通道"靠
ExtensionContainer（模式 1）提供。

## 5. 非拥有 Registry：单一查询入口解耦命令

**问题**：命令/工具要拿"当前实体"时，若都从"某个工具的 context"拿（`BezierContext->getInstance()`），
其他插件的命令就被迫依赖那个工具。

**模式**：建一个全局、**非拥有**（生命周期由别处管）的 Registry 作唯一查询入口：

```cpp
class RuntimeRegistry {
public:
    static RuntimeRegistry& instance();        // 跨 DLL：实现必须在 .cpp，见 multi-dll-plugin.md
    void registerEntity(Id, Entity* e);        // 非拥有指针
    void unregister(Id);
    Entity* find(Id) const;
};
```

**约束**：存非拥有指针；生命周期钩子明确（创建时注册 / 删除时反注册 / 场景重置时全清）。
**通信范式**：发布方 → Registry 注册，消费方 → Registry 查询，**而非**消费方 → 发布方 context。
跨 DLL 单例纪律见 [`../../../guidelines/cpp/multi-dll-plugin.md`](../../../guidelines/cpp/multi-dll-plugin.md)。

---

## 6. 编辑层 state 复用既有值：权威类型不可扩展时

**问题**：core 实体的权威类型（如某 enum / struct）由**别处拥有、你不能改**——vendored 第三方库、
git 子模块、算法同事维护的"几何真值"类型。但你的**编辑层/UI 层**需要给实体附一个状态（如"已删除/
dead"、"临时隐藏"、"待重算"），而这个状态不属于权威几何语义、塞进权威类型不合适也改不动。

**两条看似可行、实则更糟的路**：
- **fork / 扩权威类型**（给子模块 enum 加值）：跨 repo / 跨团队改动，升级即冲突，且把编辑层概念污染进几何真值类型。
- **加并行字段/属性**（与权威数组平行的一份 dead-mask）：制造**第二份权威**要同步，且**波及序列化 /
  undo 快照 / 每个 marshalling 出入口**——一处漏同步就 desync。

**模式**：**复用权威类型里某个既有值**当编辑层标记，让该状态落进已有的处理桶，零新增字段、零类型改动。
判据：找一个"语义上无害、且已有正确处理路径"的既有值——把待标记对象**降级**成它即可。

```text
例：控制点池里"已删除的端点"不能从池移除（索引不可 reindex，下游按索引对齐），
   权威 KnotRole{Endpoint, TangentHandle} 在子模块、不能加 Dead 值。
   → 把已删端点降级为"未引用的 TangentHandle"：绘制层本就"未引用手柄一律剔除"，
     于是它自动隐藏、不可选、不复用，且 undo 经既有 role 快照天然还原。零新字段、零子模块改动。
```

**前提 / 边界**：
- 复用的既有值必须有**已存在的、正好符合预期的处理路径**（上例：未引用手柄→剔除）。没有就别硬塞。
- 该 state 是**编辑/显示层**的，不进几何真值语义；权威类型的纯几何消费方（solver 等）应天然忽略它
  （上例：未被任何拓扑引用 → solver 本就忽略孤儿）。
- 在代码注释 + 数据格式文档里**写明这是复用语义的编辑层标记**，避免未来读者误判。

⚠️ 单项目单次验证（比其余 5 个模式更 tentative）；第二次遇到"不可扩展权威类型 + 需附编辑层 state"
再确认/精炼。

---

## 组合关系

五个模式不是孤立的，典型一起出现：core 实体 = ExtensionContainer（1）；配置经 feature-parser
注册（2）填出 Preset，沿三段式（3）下沉成 Instance；Instance 进非拥有 Registry（5）供命令查询；
所有数据操作围绕 value-like Snapshot + Ops（4）。

## Anti-Patterns

| 反 pattern | 修法 |
|-----------|------|
| 每个 feature 组合一个子类（继承爆炸） | ExtensionContainer 挂扩展 |
| base 配置类直接声明所有 feature 字段 | feature-parser 注册制 |
| 用 version 号判断 feature 有无 | 用字段存在性 / hasExtension |
| 超级基类承载所有 feature 方法 | Snapshot 纯数据 + Ops namespace |
| 命令从某工具的 context 取实体 | 非拥有 Registry 单一查询入口 |
| instance 创建后才注册 Template 扩展 | 固定初始化顺序 + applyTo assert |

## 项目实例参考

某 Maya C++ 插件套件（一个 `RDMayaBase` 共享 `.mll` + 三个功能插件 Bezier/Diffusion/FootFix）
的大型重构产物：core 实体（Preset / Template / Instance / Snapshot 四层）全继承 ExtensionContainer；
各插件用 `IPresetFeatureParser` 注册解析自己的配置段（`features.bezierInbetween` 等），base 层
零依赖具体插件；命令从 `CharacterRuntimeRegistry`（非拥有）查实体，从而让 Diffusion/FootFix 命令
不再耦合 Bezier 的 ToolContext。重构曾因"把 Bezier 专用类放进 core"走错方向需整体回滚——
**core/plugin 边界判断由人确认、agent 执行** 比 agent 自主决策更稳。

## 相关 Guidelines / Skills

- [`../../../guidelines/cpp/multi-dll-plugin.md`](../../../guidelines/cpp/multi-dll-plugin.md) — 非拥有 Registry 的跨 DLL 单例实现 + 两阶段初始化
- [`../../../guidelines/cpp/hot-path-cpp.md`](../../../guidelines/cpp/hot-path-cpp.md) — getExtensionAs 热路径缓存
- [`../../../guidelines/code/reuse-before-implementing.md`](../../../guidelines/code/reuse-before-implementing.md) — 架构 pattern 级复用归 skill 的依据
- `skills/ue/ue-module-architecture` — UE 版的 module 切分架构 skill（同形态，不同框架）
