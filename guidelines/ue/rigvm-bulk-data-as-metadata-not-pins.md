# RigVM 程序化建图:大批量数据走 element metadata,别烤成节点 pin 默认值

## 核心规则

程序化构建 RigVM / Control Rig 图时,**逐元素的大批量数据(几百+ 项)必须存成 `URigHierarchy`
element metadata,不能烤成 RigVM 节点的 pin 默认值**。把大数组用
`URigVMController::SetPinDefaultValue(..., bResizeArrays=true)` 烤进节点 → 打开图时 Slate 给**每个
sub-pin 建一个 widget** → 几百+ sub-pin 直接卡死图编辑器(几十秒无响应 + 反复 BP 重编译),资产体积
也随文本默认值膨胀。

正解:在生成期(Editor)把数据逐元素写成 hierarchy metadata,RigUnit 运行时读。

## 机制

| | 节点 pin 默认值(❌ 大数组) | element metadata(✅) |
|---|---|---|
| 写 | `Controller->SetPinDefaultValue(node.Pin, "(a,b,...)", /*bResizeArrays=*/true)` | `Hierarchy->SetNameArrayMetadata(Key, "myKey", Names)` / `SetFloatArrayMetadata(...)` |
| 图编辑器开销 | 每个 sub-pin 一个 Slate widget;N 到几百~上千 → 打开卡死 | 不在图上,**零 pin widget** |
| 资产体积 | 按文本默认值膨胀 | 紧凑二进制 |
| RigUnit 运行时读 | pin → input 属性 | `Hierarchy->GetNameArrayMetadata(Key, "myKey")` 等 |

**为什么 metadata 在运行时读得到**:`URigHierarchy` 的 element metadata 会序列化(`FMetadataStorage`
的 `operator<<` + `ElementMetadata` 进存储),且实例初始化时经
`URigHierarchy::CopyHierarchy → CopyAllMetadataFromElement` **复制到运行时实例** —— 所以 RigUnit 的
`Execute` 读得到生成期(BP hierarchy)写入的值。typed array 访问器见
`Engine/Plugins/Animation/ControlRig/Source/ControlRig/Public/Rigs/RigHierarchy.h`
(`Get/SetNameArrayMetadata` / `Get/SetFloatArrayMetadata` / `Get/SetNameMetadata` 等)。

## 判断:pin 还是 metadata

| 数据 | 放哪 |
|---|---|
| 整图共享的**小**拓扑 / 少量参数(几个~几十项) | pin 默认值 OK |
| **逐元素**的大批量数据(每个 bone / control 的权重表、绑定、参数数组),总 sub-pin 几百+ | **element metadata** |

经验警觉线:**单节点 sub-pin 总数过几百就别走 pin**。

## Failure Symptom(怎么发现踩了)

- 打开 Control Rig 蓝图**几十秒无响应**,日志反复 `Compiling Blueprint`。
- CR 资产 `.uasset` 体积异常(把大数组烤进 pin 默认值后明显膨胀)。
- 节点上一个 array pin 展开成成百上千个 sub-pin。

## Anti-Patterns

| 反 pattern | 后果 | 修法 |
|---|---|---|
| 几百+ 项数组 `SetPinDefaultValue(bResizeArrays=true)` 烤进节点 | 图编辑器建 N 个 pin widget 卡死 + 资产膨胀 | 改 per-element metadata |
| 以为"RigUnit 要数据就得开 input pin" | 漏了 metadata 这条不上图的通道 | bulk / 逐元素数据走 metadata |
| 担心 metadata 运行时读不到而退回 pin | 误判 —— metadata 序列化且复制到实例 | 信 `CopyHierarchy→CopyAllMetadataFromElement`,实测确认(eval 时打 log 计数) |

## 项目实例参考

UE 5.7 curvenet 形变插件(CurveArticulationUE)的 bone-follow RigUnit:481 个 control × ~10 个
carrier 蒙皮影响 ≈ **9700 个 sub-pin**(BoneNames `FName[]` + Weights `float[]` + Counts `int[]`)第一版
烤成 Follow 节点的 pin 默认值 → 打开 CR 图卡死(34s 无响应 + 反复编译),资产 **3.46MB**。改成把每个
control 的 carrier 绑定存成 element metadata(`cnCarrierBones` NameArray + `cnCarrierWeights` FloatArray),
RigUnit `Execute` 遍历 control 读各自 metadata → 资产 **0.53MB**、**秒开**。运行时打 log 实测 `followed=481`
坐实 metadata 复制到了实例。commit `4bdbd90`。

> 同图共享的 spline 拓扑索引(几百项 int)仍走 pin 默认值,没问题 —— 它是**整图一份**、且 Draw/Propagate
> 本就要当 input 消费;真正爆炸的是**逐 control** 的 carrier 表(control 数 × 每 control 影响数)。

## 相关 Guidelines

- [`guidelines/code/validation.md`](../code/validation.md) —— "看代码对 ≠ 验证";本坑只在**打开图**(GUI)
  才暴露,headless 编译 + 生成都 OK,必须编辑器内实开确认。
- skill `ue-reference-engine-source` —— metadata API 是读 `RigHierarchy.h` engine source 找到的;
  "RigUnit 怎么拿生成期数据"这类问题先翻 ControlRig 源码,别假设只能开 input pin。
- [`guidelines/ue/external-automation-write-path.md`](external-automation-write-path.md) —— 同属"程序化
  写 UE 资产的 hidden contract"族;那条管走 `PostEditChangeProperty` 同步,本条管 RigVM 数据投递通道。
