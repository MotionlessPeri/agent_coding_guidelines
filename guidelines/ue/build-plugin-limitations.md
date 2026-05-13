# `RunUAT BuildPlugin` 的两个非显然 limitation

UE 5.x（验证版本 5.5）通过 `RunUAT BuildPlugin -Rocket` 打 plugin binary artifact
分发给 marketplace / 内部用户时，**默认产物不包含 plugin 自带的 `Config/` 和
`Scripts/`**，**也不保留 `.uplugin` 里 `PythonRequirements` 这类 UE 5.x 扩展字段**。

两个 bug **独立**，但联动让"接收方拿到 plugin 后跑不通"——CI 调试时容易当成同
一个问题反复绕。

---

## Limitation 1: 默认 `FilterPluginFiles` 不带 `Config/` 和 `Scripts/`

### 现象

```bash
RunUAT.bat BuildPlugin -Plugin=MyPlugin.uplugin -Package=Out -TargetPlatforms=Win64 -Rocket
```

`Out/` 目录里有：

| 目录 | 是否进包 |
|---|---|
| `Source/` | ✅ |
| `Binaries/` | ✅ |
| `Content/` | ✅ |
| `Resources/` | ✅ |
| `Shaders/` | ✅ |
| `.uplugin` | ✅（但字段被剥，见 Limitation 2）|
| **`Config/`** | ❌ **完全不进包**（含 `CoreRedirects` / 自定义 ini 配置全丢）|
| **`Scripts/`** | ❌ **完全不进包**（含 plugin 自己的 Python / shell 脚本全丢）|

接收方拿到包后：

- `CoreRedirects` 失效 → 旧版本资产里引用的类名找不到 → asset corruption / load fail
- plugin 内嵌的 Python 脚本 / 工具丢失 → 走 subprocess 调脚本的功能失效
- 任何放在 `Config/Engine.ini` / `Config/DefaultGame.ini` 的 plugin-level 配置丢失

### Root cause（带源码引用）

UE 5.5 `Engine/Source/Programs/AutomationTool/Scripts/BuildPluginCommand.Automation.cs:432-464` 的 `FilterPluginFiles` 函数硬编码 include 白名单：

```csharp
static IEnumerable<FileReference> FilterPluginFiles(...)
{
    FileFilter Filter = new FileFilter();
    Filter.AddRuleForFile(PluginFile, ...);          // .uplugin 本身
    Filter.AddRuleForFiles(BuildProducts, ...);       // Binaries
    Filter.Include("/Binaries/ThirdParty/...");
    Filter.Include("/Resources/...");
    Filter.Include("/Content/...");
    Filter.Include("/Intermediate/Build/.../Inc/...");
    Filter.Include("/Shaders/...");
    Filter.Include("/Source/...");
    Filter.Exclude("/Tests/...");
    // ← 没有 /Config/...  也没有 /Scripts/...

    // line 447: 额外读 plugin 自己的 FilterPlugin.ini 加 include 规则
    AddRulesFromFileToFilter(Filter,
        FileReference.Combine(PluginFile.Directory, "Config", "FilterPlugin.ini"));
    ...
}
```

默认 filter 只 include 6 类目录。`Config/` 和 `Scripts/` 不在白名单。

### 修法：plugin 提供 `Config/FilterPlugin.ini`

在 plugin 根目录建 `Config/FilterPlugin.ini`：

```ini
[FilterPlugin]
; This section lists additional files which will be packaged with the plugin.
; Paths relative to plugin root. Wildcards: ... * ?

/Config/...
/Scripts/...

; 排除开发期产物
-/Scripts/__pycache__/...
-/Scripts/.../__pycache__/...
-/Scripts/.../*.pyc
-/Scripts/tests/...
-/Scripts/.../tests/...
```

注意：

- 路径相对 plugin 根，**不带前导通配**（`/Config/...` 不是 `/.../Config/...`）
- `...` 是 P4-style 递归通配
- `-` 前缀是 exclude，include rules 之后写
- `FilterPlugin.ini` **自己**会一起进包（因为它在 `Config/` 下）—— 不影响功能，可接受

### 这个 ini 是 UE 官方推荐做法

Marketplace plugin 提交流程的标准要求。但**默认 plugin 模板不带这个文件**，新建 plugin 的开发者很容易不知道这个 ini 的存在。直到走 BuildPlugin 才暴露——也就是说 plugin 在 dev 模式（直接源码挂载）跟 BuildPlugin 模式行为不一致。

### 跟 Marketplace 的对照

| 分发方式 | `Config/` `Scripts/` 表现 |
|---|---|
| 直接源码挂载（`Plugins/<name>/` in project tree） | 进包，正常加载 |
| Marketplace 上架 zip | 走 BuildPlugin → 默认不带 → 必须 `FilterPlugin.ini` |
| 自建 CI 跑 RunUAT BuildPlugin | 同上 |

dev 期间没问题，正式分发就缺。这种"开发 → 分发"行为差异是最坑的形态。

---

## Limitation 2: UBT C# `Save()` 剥 `PythonRequirements` 等扩展字段

### 现象

源 `.uplugin`：

```json
{
    "FileVersion": 3,
    "Version": 0,
    "VersionName": "0.5.5",
    "FriendlyName": "My Plugin",
    "Modules": [...],
    "PythonRequirements": [
        {
            "Platform": "Win64",
            "Requirements": ["openpyxl>=3.1.2"]
        }
    ]
}
```

BuildPlugin 输出的 `.uplugin`：

```json
{
    "FileVersion": 3,
    "Version": 0,
    "VersionName": "0.5.5",
    "FriendlyName": "My Plugin",
    "CreatedBy": "",
    "CreatedByURL": "",
    "DocsURL": "",
    "MarketplaceURL": "",
    "SupportURL": "",
    "EngineVersion": "5.5.0",
    "CanContainContent": false,
    "Installed": true,
    "Modules": [...]
    // ← PythonRequirements 字段消失
}
```

接收方 UE 启动时 `PythonScriptPlugin` 扫不到 `PythonRequirements` → 不触发 PipInstall → plugin 依赖的 pip 包 (如 `openpyxl`) 没装上 → import 失败。

### Root cause（带源码引用）

UE 5.5 有两套独立的 `PluginDescriptor` 实现：

| 实现 | 路径 | 行为 |
|---|---|---|
| **C++ `FPluginDescriptor`** | `Engine/Source/Runtime/Projects/Private/PluginDescriptor.cpp` | `Write()` 通过 `CachedJson` **保留**所有扩展字段（包括 `PythonRequirements`），WITH_EDITOR 下 OK |
| **C# `PluginDescriptor`**（UBT） | `Engine/Source/Programs/UnrealBuildTool/System/PluginDescriptor.cs` | `Save()` 用硬编码字段列表序列化，**剥**所有它不认识的字段 |

C++ 端 line 356-359：

```cpp
#if WITH_EDITOR
    if (CachedJson.IsValid())
    {
        FJsonObject::Duplicate(CachedJson, PluginJsonObject);
    }
#endif
```

C# UBT 端 line 437-540 的 `Write(JsonWriter)` 方法每个字段一行 `Writer.WriteValue("FileVersion", ...)` / `"Version"` / `"FriendlyName"` 硬编码下来——**没有 `PythonRequirements`** 这一行。

同文件 line 422-431 的 `Save2(string)` 方法**会**保留扩展字段（用 `CachedJson.ToJsonString()`），但 Epic 标了 `@TODO`：

```csharp
public void Save2(string fileName)
{
    // @TODO: This should replace all instances of Save() at some point
    // in the future. There's just still a lot of references to test and
    // refactor that needs to be verified.
    ...
}
```

`Engine/Source/Programs/AutomationTool/Scripts/BuildPluginCommand.Automation.cs:420` 调的是**旧的** `Save()`：

```csharp
NewDescriptor.Save(TargetPluginFile.FullName);
```

也就是说**Epic 自己知道这是个问题，标了 TODO 待修，但还没切**。未来 UE 6.x 可能会修，但 UE 5.x 整个版本线都受影响。

### 修法：CI 后处理把字段写回 BuildPlugin 产物

不去 patch UBT 源码（每次 UE 升级要重打补丁），在 CI 的 package stage `RunUAT BuildPlugin` 之后用 PowerShell / 别的脚本把字段写回：

```powershell
$srcPluginJson = Get-Content $sourceUpluginPath -Raw | ConvertFrom-Json
$dstPluginPath = Join-Path $tempPackageDir "MyPlugin.uplugin"
$dstPluginJson = Get-Content $dstPluginPath -Raw | ConvertFrom-Json

if ($srcPluginJson.PSObject.Properties.Name -contains 'PythonRequirements') {
    if ($dstPluginJson.PSObject.Properties.Name -contains 'PythonRequirements') {
        $dstPluginJson.PythonRequirements = $srcPluginJson.PythonRequirements
    } else {
        $dstPluginJson | Add-Member -NotePropertyName 'PythonRequirements' `
            -NotePropertyValue $srcPluginJson.PythonRequirements
    }
    # 写 no-BOM UTF-8
    $jsonOut = $dstPluginJson | ConvertTo-Json -Depth 10
    [System.IO.File]::WriteAllText($dstPluginPath, $jsonOut,
        (New-Object System.Text.UTF8Encoding $false))
}
```

如果 plugin 还用了别的扩展字段（如 `EditorCustomVirtualPath` / 第三方 plugin 系统的字段），同样需要补回去。

### 为什么不能改用 Save2() 解决

`BuildPluginCommand.Automation.cs:420` 是 Epic engine 文件，改它意味着每次 UE 版本升级都要重打补丁。不可持续。

CI 后处理 patch 方案：
- 不动 Epic 文件
- 局部化在 CI yaml 里
- 未来 Epic 修了 BuildPlugin 后**自动 no-op**（写回相同字段没副作用）

---

## 跟 PythonRequirements 联动的 require-hashes 严格模式

Limitation 2 衍生的另一个坑：

UE 5.5 PythonScriptPlugin 默认走 `pip install --require-hashes` **严格模式**。如果 `PythonRequirements` 写：

```json
"Requirements": ["openpyxl>=3.1.2"]
```

pip 报：

```
ERROR: In --require-hashes mode, all requirements must have their versions
pinned with ==.
```

接收方 PipInstall 失败 → 走 fallback engine python → 没 openpyxl → import 失败。

两条修法：

**方案 A**：`Requirements` 用 pin 版本 + sha256：

```json
"Requirements": [
    "openpyxl==3.1.5 --hash=sha256:5282c12b... --hash=sha256:cf0e3cf5...",
    "et-xmlfile==2.0.0 --hash=sha256:..."
]
```

hash 用 `pip-compile --generate-hashes` 生成。**传递依赖必须显式列出**（pip 严格模式不允许隐式解析）。

**方案 B**：plugin 在 `Config/Engine.ini` 关掉严格模式：

```ini
[/Script/PythonScriptPlugin.PythonScriptPluginSettings]
bPipStrictHashCheck=False
```

但**前提是 `Config/Engine.ini` 真的进了 BuildPlugin 产物** —— 看 Limitation 1，必须有 `Config/FilterPlugin.ini` include `Config/...`。

**方案 A vs B 选择**：A 是默认安全模式（pip 校验 hash 防供应链攻击），但版本升级麻烦。B 简单，对内部分发 plugin 足够，配合 `Config/FilterPlugin.ini` 一并 ship。

---

## 项目实例参考

UE 5.5 dialogue plugin（DialogueSystemSample）的 GitLab CI ship 期间踩穿两个 limitation：

- **Limitation 1**: BuildPlugin 输出的 plugin artifact 完全没 `Config/` 和 `Scripts/` 目录。`CoreRedirects` 失效导致 `LegacyNodeClassRedirects` automation test 失败 + plugin 走 subprocess 调 Python 脚本的功能链全断
- **Limitation 2**: `.uplugin` 里 `PythonRequirements: ["openpyxl>=3.1.2"]` 被 BuildPlugin 剥掉，接收方 UE 不触发 PipInstall

修法用上面的方案——加 `Config/FilterPlugin.ini` + CI package stage PowerShell 后处理写回 PythonRequirements。

## 搜索回顾

排查 Limitation 2 时按 "Unreal Engine BuildPlugin PythonRequirements stripped" /
"PluginDescriptor.cs Save Save2" 等 query 搜过，**未找到任何社区帖子 / GitHub issue
直接讨论这个字段剥离**。推测原因：

- 用 `PythonRequirements`（UE 5.0+ 新机制）+ 走 BuildPlugin binary 分发的 plugin 本身极少
- 大多数 Python 相关 plugin 走 source 分发不打 binary

排查 Limitation 1 同样基本搜不到中文 / 英文资料。属于"开发期看不出 / 分发期才暴露"的真冷门坑。

## 相关 Guidelines

- skill `ue-reference-engine-source` （`skills/ue-reference-engine-source/reference-engine-source.md`）—— 强调"写 UE 功能前先找 reference"。这两个 limitation 都是从 engine source 看出来的，符合"读 source 比读 doc 准"原则
- `guidelines/ue/localization-pitfalls.md` —— UE 框架 hidden contracts 集
- `guidelines/ci-windows/powershell-native-command-pitfalls.md` —— CI 后处理用 PowerShell 时撞的相关 pitfall
- `techniques/ci-deploy-to-p4.md` —— BuildPlugin 产物提交到 P4 的完整流程示例
