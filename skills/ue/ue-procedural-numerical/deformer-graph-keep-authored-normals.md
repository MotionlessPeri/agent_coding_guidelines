# UE Deformer Graph 的 `ComputeNormalsTangents` 全重算丢 authored 法线 → 用 `Keep{Imported,Input}Normals` 变体

给 SkeletalMesh 挂 Deformer Graph(Optimus)后蒙皮/法线改由图负责。图末尾常用引擎自带的连通性
RecomputeTangents 重算法线——但**纯版会主动丢弃 mesh 的 authored 法线**,在接缝/硬边/开放边界处
产生着色不连续(看着像边缘"塌陷/凹进")。引擎另 ship 了两个保留 authored 法线的变体,换上即修。
UE 5.8 实测,anchor 为 5.8 engine source。

## 核心规则

1. **`DG_Function_ComputeNormalsTangents`(纯版)= 全连通性重算,丢弃 authored 法线**。UV/光滑组接缝、
   硬边、开放边界边(`TwinEdgeIndex == -1`)、valence > `MaxIterationIndex`(纯版 16)的顶点,重算法线
   跟 mesh authored 不一致 → **Lit 着色不连续**。这是**着色/法线差异,不是几何**。
2. **改法 = 把图里那个 function-reference 换成引擎自带的保留变体**(同目录):
   - **`DG_Function_ComputeNormalsTangentsAndKeepImportedNormals`** —— 自动读 mesh **导入(authored)切线**
     + 未形变位置,内部保留。
   - **`DG_Function_ComputeNormalsTangentsAndKeepInputNormals`** —— reference 位置 + reference 切线走
     **显式输入 pin**,自己喂(更灵活,图里已有 LBS 蒙皮切线时用它)。
   两者 `MaxIterationIndex` 都是 32(顺带覆盖更高 valence)。
3. **零自定义 shader**:三个都是引擎官方函数,换节点即可,不偏离引擎、无维护负担。

三个函数都在 `Engine/Plugins/Animation/DeformerGraph/Content/DeformerFunctions/`。

## 机制:为什么 Keep 变体能保留 authored

纯版对每个顶点一环遍历相邻三角形,累加面法线 → `WriteOutTangentZ(normalize(SumTangentZ))`,**完全无视
mesh 自带法线**。authored 法线里编码的硬边/光滑组/接缝(render mesh 在这些地方 split 顶点、给不同法线)
全部被抹平成"连通性平均法线"。

Keep 变体多算一步 **delta 搬运**(注释原文 `Take into consideration also the original artist-authored
normals`):

```
UndeformedConnNormal = 连通性法线(未形变 reference 位置)
QuatDelta            = QuatBetween(UndeformedConnNormal, AuthoredNormal)   // authored 相对 naive 的偏差
DeformedConnNormal   = 连通性法线(形变后位置)
OutNormal            = QuatRotate(QuatDelta, DeformedConnNormal)           // 把偏差搬到形变后法线上
```

**关键性质**:未形变(rest)态 `形变后位置 ≡ reference 位置` → 两个连通性法线相等 → delta 复合成 identity
→ **输出法线逐点等于 authored**。形变态则"形变后 naive 法线 + authored 硬边/接缝特征",既跟形状走又保留
authored character。

## 症状 / 怎么发现(一次 viewport 定性,几何 vs 着色分离)

deformer 开/关对比,mesh 边缘有可见差异时:

| 操作 | 观察 | 含义 |
|---|---|---|
| viewport 切 **Wireframe** | 开/关线框**完全重合** | 几何逐点一致 → **不是几何/精度** |
| viewport 切 **Unlit** | 边缘差异**消失**(只 Lit 有) | **纯着色/法线** → 命中本条 |
| viewmode 看 Normals | 接缝/边界法线翻转/不连续 | 坐实重算法线 ≠ authored |

**别把"边缘看着塌陷"当几何/浮点精度 bug 去查顶点位置**——Wireframe 一致就证明几何没差,差在法线。

## wiring 要点:reference 位置 / authored 切线接哪个 DI

Keep 变体要一个**未形变的 reference 位置** + **authored 切线**。UE 的 SkinnedMesh 系有两个 DI,Position
读的是**不同 buffer**,别接错:

| DI | Position 读哪个 buffer | 会不会随图内 kernel 写入变 | anchor |
|---|---|---|---|
| **基础 `Skinned Mesh` DI** `OptimusSkinnedMeshDataInterface` | `PositionVertexBuffer`(bind-pose 静态) | **不变**(静态 ref) | `OptimusDataInterfaceSkinnedMesh.cpp:208` |
| **`Read Skinned Mesh` DI** `OptimusSkinnedMeshReadDataInterface` | `GetAllocatedPositionBuffer`(deformer 工作 buffer) | 视 RDG 依赖顺序 | `OptimusDataInterfaceSkinnedMeshRead.cpp:221` |

- authored 切线走 SkinnedMesh 的 `ReadTangentX/Z`(= `StaticMeshVertexBuffer` 自带切线,
  `OptimusDataInterfaceSkinnedMesh.cpp:187`)。
- reference 位置要的是**未被图内 deformation 覆写过的 bind ref**。**结构性判据**:若图里有 `LinearBlendSkin`
  节点、且 `Read Skinned Mesh` 的 Position 经加工后喂给它当输入,那这个 Position 必然是**未蒙皮 bind ref**
  (否则 LBS 会 double-skin)——此时 `Read Skinned Mesh` Position 可直接当 reference。拿不准时用基础
  `Skinned Mesh` DI 的 Position(`PositionVertexBuffer`,保证静态)。
- **验证纪律**:rest 态**分辨不了** reference 接得对不对(rest 下 ref ≡ 形变后,两种接法都出 authored 法线)。
  必须**上真形变(CtrlRig 摆 pose)测**:法线跟形变走 + 接缝保留 → 对;法线冻在 rest / 明显错 → reference
  接成了形变后位置,换成基础 `Skinned Mesh` DI 的静态 Position(见 `code/validation.md`:一个能跑 ≠ 另一个能跑)。

## Anti-Patterns

| 反 pattern | 后果 | 修法 |
|---|---|---|
| 图末尾用纯 `ComputeNormalsTangents` 且 mesh 有 authored 法线 | 接缝/硬边/边界着色不连续,像边缘塌陷 | 换 `Keep{Imported,Input}Normals` |
| 边缘看着塌陷 → 去查顶点位置/浮点精度 | 查错方向(几何没差,差在法线) | 先 Wireframe(几何)/Unlit(着色)分离 |
| Keep 变体的 reference 位置接 `Read Skinned Mesh`,以为"没变" | 该 DI 读工作 buffer,形变态可能拿到形变后位置 → 法线冻 rest | 用基础 `Skinned Mesh` DI 的静态 Position;真形变态实测确认 |
| 只测 rest 就认为 reference 接对了 | rest 分辨不了(ref≡形变后) | 上 CtrlRig 摆 pose 测形变态 |
| 自己内联抄一份 kernel 改接缝处理 | 偏离引擎、要长期维护 | 引擎已 ship 保留变体,直接换节点 |

## 项目实例参考

UE 5.8 curvenet 形变插件(CurveArticulationUE):给 SkeletalMesh 挂 curvenet rig deformer,**无 CtrlRig 的
rest 态**下 deformer 开/关对比,mesh 边缘可见塌陷。顶点位置已确认 bit-identical(纯 pass-through),用户 Wireframe
一测坐实几何逐点一致、只 Lit 有差 → 铁证是着色/法线。根因:`DG_CurvenetRig` / `DG_Curvenet` 末尾都用纯
`ComputeNormalsTangents`(strings 抓出的 kernel 跟引擎 `DG_Function_ComputeNormalsTangents` 逐字相同),重算法线
丢 authored。修法:两图的 function-ref 换成 `ComputeNormalsTangentsAndKeepInputNormals`,Position=形变后(rig 走
MyKernel Out / corrective 走 LinearBlendSkin Out)、Original Position=`Read Skinned Mesh`(corrective 图 LBS 输入
结构反推坐实=未蒙皮 bind ref)、Original Tangent X/Z=`Read Skinned Mesh`(authored)。rest 态输出 authored 法线逐点
→ artifact 归零;rig + corrective 两图均 GUI 实测通过。

## 相关 Guidelines

- `guidelines/code/diagnose-before-fixing.md` —— 本条的定位是范例:不猜"几何/精度",
  用 Wireframe/Unlit 设计成能区分"几何 vs 着色"两个竞争假设。
- `guidelines/code/validation.md` —— reference 位置对不对 rest 测不出、必须形变态实测,是"一个能跑 ≠
  另一个能跑"的实例。
- skill `ue-reference-engine-source` —— `Keep{Imported,Input}Normals` 变体 + 两个 SkinnedMesh DI 的 Position buffer
  差异全靠读 engine source(DeformerFunctions 资产 + `OptimusDataInterfaceSkinnedMesh*.cpp`);UE doc 没写官方 usage。
- [`rigvm-bulk-data-as-metadata-not-pins.md`](rigvm-bulk-data-as-metadata-not-pins.md) / [`controlrig-sequencer-bulk-key-bake.md`](controlrig-sequencer-bulk-key-bake.md)
  —— 同属"程序化用 UE Deformer/RigVM/ControlRig 的 hidden contract"族。
