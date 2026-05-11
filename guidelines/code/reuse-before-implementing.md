# Reuse Before Implementing

## 核心规则

实现新功能 / 修 bug **动手前必须先扫一遍代码库**，确认有没有：

- **已经存在的同类功能** → 直接复用，不要再写一份
- **流程近似但参数 / 行为有差异** → 抽 helper / 模板 / 基类，新旧调用方都走它
- **局部相似的代码段** → 抽函数，避免 copy-paste

跟 `clarify-before-implementing.md` 对称：那条讲"开工前先澄清需求"，本条讲"开工前先 survey 现有实现"。两条都属于 prep work，**优先级高于直接动手写**。

## 跟"premature abstraction"的边界

[`guidelines/code/constraints.md`](../code/constraints.md) "Simplicity" 节：

> Three similar lines of code is better than a premature abstraction.

跟本条**不冲突**，是同一光谱不同位置：

| 时机 | 该做什么 |
|---|---|
| **第一次写**（codebase 里还没有同类代码）| 直接写，三行相似没事，**不要先抽** |
| **第二次写**（开工前 survey 发现已有同类代码）| **必须**考虑复用 / 抽公共代码 |
| **第三次写**（同类代码已经在 codebase 里出现 ≥2 处）| 抽抽象**是基本要求**，再 copy-paste 就是技术债 |

防的是两端：
- **过早抽象**：还没第二处就先抽
- **重复堆叠**：第二/三处出现却不抽

本条防的是后者。

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
  ├── 完全一致或几乎一致（差 < 10% 行）
  │     → 直接复用（如果调用约定允许）/ 抽到 helper 函数
  │
  ├── 流程一致但内层有差异
  │     → 抽 template / strategy / 提取 hook function
  │       新旧 caller 都走同一个 helper 接口
  │
  ├── 表面相似但语义不同（参数含义 / 副作用不一致）
  │     → 不要勉强复用
  │       但**显式记录**为什么"看起来相似但不复用"，避免后人误判
  │
  └── 一处现有 + 一处即将新建 = 2 处
        → 至少抽函数，避免 copy-paste 进入 codebase
```

## 复用决策记录

如果你**决定不复用**已发现的 similar code，commit message / PR description / 代码注释里**简短说明为什么**：

```cpp
// NOTE: 看起来跟 ParseXlsxBatch 的 subprocess 逻辑相似，没复用 PythonSubprocessHelper 是因为
// 这里需要返回 stderr 给 caller 做交互式 prompt，helper 当前签名只暴露 exit code。
// 等 helper 加 stderr out-param 后再切。
```

这避免下一个人 review 时问"为什么不用 helper"——你已经给出了 trade-off。

## Anti-Patterns

### 1. Copy-paste 进入 codebase

```
版本 1: ParseXlsxBatch 内联 660 行 subprocess 逻辑
版本 2: ParseTranslationsBatch 又写一遍同样 660 行
版本 3: ExportDialogueToXlsx 再写一遍
版本 4: ParseSomethingElseBatch 又来一遍
```

每次新增 caller 都是 660 行膨胀；某次 subprocess timeout 行为要改，4 处都得改且容易漏。

**修法**：第 2 处出现时**就**抽 helper，不要等第 4 处才动手。

### 2. 各自实现"看起来相似但实际相同"的功能

两个 dev / 两个 agent 各自实现"打开 DB → 查表 → 返回"的逻辑，签名不同、错误处理不同、close DB 时机不同——后面接 caller 时困惑两套用哪套。

**修法**：开工前 survey；如果发现已经有人在做同类工作，先沟通 / 合并工作流。

### 3. 错误的复用（强行套用语义不同的"近亲"）

发现一个 `OnFooChanged` callback 看起来跟新需求差不多就直接复用——但实际 `OnFooChanged` 有副作用（清缓存 / 触发其他事件），新需求不需要副作用反而被坑。

**修法**：复用前**读懂被复用函数的全部副作用**。如果副作用不匹配，宁可分开实施。

### 4. "抽完才发现不该抽"

刚抽完 `Helper::DoX` 就发现只有一处 caller 用得到，其他 caller 参数都不一样硬塞参数。

**修法**：抽 helper 时至少有 **2 个真实 caller** 验证签名合理；不要为"未来的可能 caller"先抽。这是 `constraints.md` "Simplicity" 防的"premature abstraction"。

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

反例：I-007 之前 660 行 subprocess 在 ParseXlsxBatch 内联了好几个月，到 Phase 3 要写第 2 个 / 第 3 个 subprocess caller 时才被 user surface 出来要求抽 helper——本该第 2 个 caller 出现时就动手。

## 相关 Guidelines

- [`guidelines/code/clarify-before-implementing.md`](clarify-before-implementing.md) —— 对称的另一条 prep work（澄清需求 vs survey 现有代码）
- [`guidelines/code/constraints.md`](constraints.md) —— "Simplicity" 节防 premature abstraction，跟本条互补
- [`guidelines/workflow/agent-lifecycle.md`](../workflow/agent-lifecycle.md) —— "Let me read the code first" 列在 procrastination pattern；本条**不是** procrastination，是 prep work（survey 关键字 → 找到/没找到 → 决策，不是 open-ended exploration）
