# 批量烤 key 到 Control Rig (Sequencer):别走逐 key 的 SetControlValue/SetLocalControlRig*

## 核心规则

程序化把一段动画**批量烤**到 Sequencer 里的 Control Rig 控件上时,**不要**用
`UControlRigSequencerEditorLibrary::SetLocalControlRig{Positions,EulerTransforms,...}` 或
`UControlRig::SetControlValue(..., bNotify=true, SetKey=Always)` 逐 key 写——这条是引擎给
**交互式单 key 编辑**用的 autokey 路径,**每个 key 触发一次 Sequencer 通知 + 重求值**,实测
**~35ms/key**,成本 = O(总 key 数) 且常量巨大(几百控件 × 几十帧 → 分钟级,甚至几分钟)。

正解:**直接批量写 `UMovieSceneControlRigParameterSection` 的浮点通道**(`Reset` + 逐帧
`AddCubicKey` + 一次 `AutoSetTangents`),整批包一个 `FScopedTransaction`,**最后只刷一次**
`RefreshCurrentLevelSequence()`。逐 key 零通知 → 亚毫秒/控件。

## 机制(为什么逐 key 这么贵)

`SetLocalControlRigPositions/EulerTransforms` 内部对每个 key 调
`ControlRig->SetControlValue(..., bNotify=true, bSetupUndo=true, Context.SetKey=Always)`:

```
SetLocalControlRig*  (loop PER KEY)
  └─ SetControlValue(bNotify=true, bSetupUndo=true, SetKey=Always)
       └─ SetControlValueImpl (每 key):
            ├─ DynamicHierarchy->SetControlValue(..., bSetupUndo=true)        ← 每 key 一个 undo 事务
            └─ OnControlModified.Broadcast(...)                              ← 每 key 一次
                 └─ FControlRigParameterTrackEditor::HandleControlModified
                      └─ AddControlKeys → AddKeysToControlRig
                           └─ ModifyOurGeneratedKeysByCurrentAndWeight       ← 每 key 重求值(weight/层)
```

`bNotify`/`bSetupUndo`/`SetKey=Always` 在 `SetLocalControlRig*` 里**硬编码**,公共 API 关不掉。
源码锚点(UE 5.7):
- `Engine/Plugins/Animation/ControlRig/Source/ControlRigEditor/Private/ControlRigSequencerEditorLibrary.cpp`
  (`SetLocalControlRigPositions` 的逐 key 循环)
- `.../ControlRig/Private/ControlRig.cpp` `UControlRig::SetControlValueImpl`(broadcast)
- `.../ControlRigEditor/Private/Sequencer/ControlRigParameterTrackEditor.cpp` `HandleControlModified`

## 正解:直接写 section 浮点通道

```cpp
#include "Sequencer/ControlRigSequencerHelpers.h"          // FindControlRigTrack / GetFloatChannels
#include "Sequencer/MovieSceneControlRigParameterSection.h"
#include "Channels/MovieSceneFloatChannel.h"
#include "LevelSequenceEditorBlueprintLibrary.h"            // RefreshCurrentLevelSequence
#include "ScopedTransaction.h"

// 1) 取 section(每 rig 一个 CR 参数 track/section)
UMovieSceneControlRigParameterTrack* Track =
    FControlRigSequencerHelpers::FindControlRigTrack(Seq, Rig);
UMovieSceneControlRigParameterSection* Section = /* Track->GetSectionToKey() 或 GetAllSections()[0] */;

FScopedTransaction Transaction(LOCTEXT("BakeAnim", "Bake"));   // 整批一个 undo step
Section->Modify();

// 2) 每控件:取它的浮点通道,Reset + 逐帧 AddCubicKey + 一次 AutoSetTangents
const TArrayView<FMovieSceneFloatChannel*> Ch =
    FControlRigSequencerHelpers::GetFloatChannels(Rig, ControlName, Section);
// 通道数/顺序按控件类型(见下表)。帧要 DisplayRate -> TickResolution:
const FFrameNumber Tick =
    FFrameRate::TransformTime(FFrameTime(DisplayFrame), DisplayRate, TickResolution).RoundToFrame();
Ch[c]->Reset();
for (...) Ch[c]->AddCubicKey(Tick, Value);
Ch[c]->AutoSetTangents();

// 3) 整批只刷一次
Section->MarkAsChanged();
ULevelSequenceEditorBlueprintLibrary::RefreshCurrentLevelSequence();
```

`Build.cs` 依赖:`ControlRig`(helpers + section)、`MovieScene`(float channel)、`LevelSequenceEditor`
(refresh)、`UnrealEd`(`FScopedTransaction`)。

### 浮点通道顺序(`FControlRigSequencerHelpers::GetFloatChannels` 返回的切片)

引擎在 `MovieSceneControlRigParameterSection` 里按固定顺序建通道(`GetInfoAndNumFloatChannels`):

| 控件类型 | 通道数 | 顺序 |
|---|---|---|
| `Position` / `Scale` / `Rotator` | 3 | X, Y, Z(Rotator = Roll, Pitch, Yaw) |
| `Vector2D` | 2 | X, Y |
| `Float` / `ScaleFloat` | 1 | — |
| `TransformNoScale` | 6 | Loc X/Y/Z, Rot Roll/Pitch/Yaw |
| `Transform` / `EulerTransform` | 9 | Loc X/Y/Z, Rot **Roll/Pitch/Yaw**, Scale X/Y/Z |

旋转通道存的就是 `FRotator` 的 Roll/Pitch/Yaw(度),直接写,无需额外编码。CR 参数 section 用
**float** 通道(`GetChannels<FMovieSceneFloatChannel>`);其它 handle 类型可能是 double,但 CR 控件是 float。

## 判断:什么时候必须走批量通道

| 场景 | 走哪条 |
|---|---|
| 用户拖一个控件、设单个 key(交互) | `SetControlValue`/`SetLocalControlRig*`(就是给这个用的)|
| 把一段 clip / 动画**批量烤**到 N 控件 × M 帧 | **批量写通道 + 一次刷新** |
| 几十 key 以上、或控件数多 | 批量(逐 key 的常量太大,几十 key 就到几秒)|

经验线:**只要是"一次写一串 key"就别逐 key**。逐 key 路径每 key ~35ms,几十就秒级、几百控件就分钟级。

## Anti-Patterns

| 反 pattern | 后果 | 修法 |
|---|---|---|
| 批量烤用 `SetLocalControlRig*` 逐 key | O(总key) × ~35ms,几百控件→几分钟 | 批量写 section 浮点通道 |
| 以为慢在解析 / `AddKey` 数据准备 | 改错地方(数据准备通常 <10%)| 先 profile,分段计时定位到 `set`(写 key)段 |
| 逐 key 还各自刷 Sequencer | 每 key 一次重求值 | 整批末尾**一次** `RefreshCurrentLevelSequence` |
| 逐 key `bSetupUndo=true` | 每 key 一个 undo entry | 整批一个 `FScopedTransaction` |
| 不 `Reset` 通道直接追加 | 重复烤制叠加重复 key | 烤前 `Channel->Reset()`(全量覆盖语义)|

## 验证要点

此路径**无法单测覆盖**(依赖 Sequencer/MovieScene 运行期状态),改完必须**编辑器内人工眼校**:
烤出的动画(位置/旋转/缩放/时间轴)跟旧逐 key 路径**逐帧一致**。性能用分段计时
log(sample / convert / **set** / notify)证明 `set` 段塌缩,不靠读代码推断(见 `code/validation.md`)。

## 项目实例参考

UE 5.7 curvenet 形变插件:Sequencer「Import CurveNet Animation」把 `.cnclip` 烤到 curvenet
Control Rig 的 cp 控件。7-cp/140-key 的小 clip 就要 ~5s;profile 显示 `set`(`SetLocalControlRig*`)
占 99.997%、逐控件 **~35ms/key 恒定**(首尾控件一致 → 实测 per-key 线性,非一次性 init),604-cp
预设外推 ~7 分钟。改直接写 section 浮点通道(`GetFloatChannels` + `Reset`/`AddCubicKey`/`AutoSetTangents`)
+ 一次 `RefreshCurrentLevelSequence` + 一个 `FScopedTransaction`:**set 4971ms→0.41ms、total
4977ms→18ms(273×)**,604-cp 外推→亚秒级。

## 相关 Guidelines

- [`rigvm-bulk-data-as-metadata-not-pins.md`](rigvm-bulk-data-as-metadata-not-pins.md) —— 同族
  「程序化写 RigVM/ControlRig 大批量数据的 hidden contract」:那条管"拓扑/绑定数据投递通道"
  (走 hierarchy metadata 不走 pin),本条管"动画 key 投递通道"(走 section 通道不走逐 key autokey)。
- [`external-automation-write-path.md`](external-automation-write-path.md) —— 外部脚本写 UE 资产走
  正规同步路径;本条是其在「Sequencer key 批量写」上的特例(逐 key API 正确但性能不可用)。
- [`../code/diagnose-before-fixing.md`](../code/diagnose-before-fixing.md) / [`../code/validation.md`](../code/validation.md)
  —— 先分段 profile 定位热点(本案头号嫌疑被证伪、真热点在另一条路径),性能结论靠计时数据。
- skill `ue-reference-engine-source` —— `FControlRigSequencerHelpers` / 通道顺序 / `SetControlValueImpl`
  的逐 key broadcast 都是读 engine source 得到的;UE doc 没写。
