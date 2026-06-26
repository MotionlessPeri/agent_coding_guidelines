# 升级到 UE 5.8 的构建 / 运行时隐藏契约

把工程 / 插件从 5.7 及更早升到 **UE 5.8** 时,三个文档没明说、只能靠踩坑得到的硬契约。都属"升 5.8 才暴露"——5.7 下不出现,所以容易在迁移期集中撞。

## 核心规则

1. **Target 升 `BuildSettingsVersion.V7` + `IncludeOrderVersion.Unreal5_8`**,否则用 installed engine 编时报 "modifies the values of properties ... not allowed"。
2. **`.uproject` 在 5.8 用 RapidJSON 读,JSON 字符串里的裸控制字符(换行/制表)→ 报 `Invalid encoding in string`**(极具迷惑性,看着像编码 bug,实为非法 JSON)。
3. **UE 5.8 editor 运行需要 VC++ redistributable `14.50.35719+`**,旧 redist → editor 启动期报 "redistributable is outdated" 并拒绝运行,且可能连带让上面 RapidJSON 误报。

---

## 1. Target.cs 必须升到 V7 / Unreal5_8

5.8 把若干 warning(`ReturnTypeWarningLevel` / `DanglingWarningLevel` / `UnreachableCodeWarningLevel`)默认升为 `Error`。Target 还停在旧 `BuildSettingsVersion`(如 V6)时,它的这些 warning level 跟 installed engine(按新默认编译的)**不一致**,UBT 拒绝:

```
<Target> modifies the values of properties: [ UnreachableCodeWarningLevel: Off != Error, ... ].
This is not allowed, as <Target> has build products in common with UnrealEditor.
```

UBT 升级提示自己会说 `Suppress this message by setting 'DefaultBuildSettings = BuildSettingsVersion.V7;'`。修法(`*.Target.cs`):

```csharp
DefaultBuildSettings = BuildSettingsVersion.V7;            // 5.8 的 Latest
IncludeOrderVersion  = EngineIncludeOrderVersion.Unreal5_8;
```

`V7` / `Unreal5_8` 的存在性按版本确认:`grep "enum BuildSettingsVersion\|Unreal5_" Engine/Source/Programs/UnrealBuildTool/.../TargetRules.cs`(`Latest = V7`)。升 V7 后这几个 warning 变 Error → 自己的代码须编译干净(vendored / ThirdParty 数值代码若触发,在该 module Build.cs 单独关对应 `CppCompileWarningSettings.*WarningLevel = Off`,module 级不撞 target 校验)。

## 2. `.uproject` 里 JSON 字符串含裸换行 → RapidJSON "Invalid encoding"

UE 5.8 用 **RapidJSON** 读 `.uproject`(`FProjectDescriptor::Load` → `FFileHelper::LoadFileToString` 解码为 TCHAR → `UE::Json::ParseInPlace` 带 `kParseValidateEncodingFlag`)。RapidJSON 的 `kParseErrorStringInvalidEncoding` 文案就是 `Invalid encoding in string.`。**JSON 字符串值里出现裸控制字符(原始 `\n`/`\r`/`\t`,非转义)= 非法 JSON,RapidJSON 报"Invalid encoding"** —— 这个错名极具误导(让你以为是文件编码/BOM 问题,实际是字符串里混了控制字符)。

典型来源:**脚本生成 `.uproject` 时把一个带前后换行的变量拼进字符串**:

```powershell
# ❌ 若 $name 含前后换行(某些 env 注入会),生成的 JSON 变成
#    { "Name": "\nFoo\n" } —— 字符串值里有裸换行 → RapidJSON Invalid encoding
'    { "Name": "' + $name + '", "Enabled": true },'
# ✅ 用字面量,或 $name.Trim();别把可能带换行的 env 直接拼进 JSON 字符串
```

排查要点:**dump 整文件十六进制,别只看开头**——裸换行往往在文件中段(被拼进去的那个值附近),只看前几十字节会误判"文件干净"。`FFileHelper` 对 no-BOM 文件**确定性按 UTF-8 解码**(`BufferToString`),所以纯 ASCII + no-BOM 不是编码问题;问题在内容里的控制字符。

## 3. UE 5.8 运行需要 VC++ redist 14.50.35719+

**编译器工具链** ≠ **VC++ 运行时 redistributable**,两者独立:

- 编译(UBT/MSVC):需非禁版工具链。UE 5.8 ban `14.40–14.43`;`14.44+` 可编。
- **运行**(启动 UnrealEditor):UE 5.8 检查 VC++ redist 版本,`< 14.50.35719.0` → 启动期报错并退出:
  ```
  Visual C++ redistributable version 14.44.x is outdated.
  Please install version 14.50.35719.0 (or above) from Engine\Extras\Redist\en-us\vc_redist.x64.exe.
  ```
- **连带坑**:redist 过旧时,§2 的 RapidJSON `.uproject` 解析也可能误报 "Invalid encoding"(运行时字符串处理函数行为异常)——所以撞到 5.8 各种"启动期诡异错误",先确认 redist ≥ 14.50.35719。

修法:在运行机器(尤其 **CI runner**——它只装了旧 redist 很常见)跑 `Engine\Extras\Redist\en-us\vc_redist.x64.exe`。注意:**编译过 ≠ 能运行**——build stage 用编译器工具链(够新即可),test/run stage 才需要 redist;所以可能出现"package/build 绿、test 一启动 editor 就挂"。

---

## Anti-Patterns

| 反 pattern | 后果 | 修法 |
|-----------|------|------|
| 升 5.8 不动 Target BuildSettingsVersion | "modifies properties ... not allowed" 编不过 | V7 + Unreal5_8 |
| 脚本拼 env 变量进 `.uproject` JSON 字符串 | 变量带换行 → RapidJSON "Invalid encoding" | 字面量 / `.Trim()` |
| 看见 "Invalid encoding" 就查 BOM/文件编码 | 查错方向(实为字符串里裸控制字符) | dump **整**文件 hex 找控制字符 |
| 装好新编译器工具链就以为能运行 5.8 | redist 旧 → editor 启动拒绝 + 连带诡异错 | 装 vc_redist.x64.exe(14.50.35719+) |
| 只看文件开头几十字节判"干净" | 中段的坏字节漏掉 | dump 整文件 |

## 项目实例参考

UE 5.7 → 5.8 curvenet 形变插件迁移期一次踩齐三条:

- Target `V6 + Unreal5_7` → 报 modifies-properties;改 `V7 + Unreal5_8` 编过(`14.44.35207` 工具链,跳过 ban 的 14.40–14.43)
- CI test stage 生成的 content-only host `.uproject` 用 `$env:PLUGIN_NAME` 拼进 JSON,该 env 带前后换行 → `"\nName\n"` → RapidJSON `Invalid encoding in string., Line 3`;改字面量后解析正常。排查走了弯路(先怀疑 redist、再怀疑文件编码),最后**整文件 hex** 才看到字符串里的裸换行
- runner VC++ redist `14.44.35211` → editor 启动报 outdated 要 `14.50.35719`;装 engine 自带 `vc_redist.x64.exe` 后通过(build/package 早就绿,只 test 一启动 editor 挂)

## 相关 Guidelines

- `guidelines/ue/leveleditor-modetools-lifetime.md` —— 另一条 5.8 删 API 的契约(`GLevelEditorModeToolsIsValid` 5.5 废弃 / 5.8 删定义)
- `guidelines/ue/build-plugin-limitations.md` —— BuildPlugin 交付包坑(同属 UE 构建/打包 hidden contract 族)
- `guidelines/ci-windows/gitlab-runner-service-and-powershell-pitfalls.md` —— CI runner 服务环境坑(§3 的 VC redist、网络盘 mapped-drive→UNC 都在 runner 上踩;那份覆盖 mapped-drive/PATH/exit-code)
- skill `ue-reference-engine-source` —— §1/§2 的 enum 值、`FProjectDescriptor::Load` 的 RapidJSON 路径都是读 engine source 确认的;UE doc 没写
