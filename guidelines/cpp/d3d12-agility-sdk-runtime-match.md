# 编译期 D3D12 特性版本 vs 运行时 `D3D12Core` 必须匹配 —— vendored 框架用新特性要显式部署 Agility SDK runtime

## 核心规则

Windows 上链一个**用新 D3D12 特性**(enhanced barriers 的 `CreateCommittedResource3` / DXR 加速结构新 flag 组合)的框架——自建 RHI、或 vendored(NVRHI / Donut / 引擎)——**编译期依赖的 D3D12 特性版本(Agility SDK headers)必须跟运行时加载的 `D3D12Core` 版本匹配**。系统自带的 `D3D12Core`(如 Win10 内置 `10.0.19041`)太旧、不支持框架编译时用的新特性时,**不会优雅报错**,而是一连串"神秘" hang / segfault。**修法:vendor 并显式部署 Agility SDK runtime。**

## 症状(极具迷惑性:一个根因,多副面孔)

同一根因会在不同地方冒出各异表象,极易被误判成"多个独立问题":

- validation 层开着时 `createAccelStruct(BLAS)` **hang**
- 非索引三角形 `buildBottomLevelAccelStruct` **段错误**
- 索引三角形 `GetRaytracingAccelerationStructurePrebuildInfo` **hang**
- 真正的底层信号:`CreateCommittedResource3` 返 **`E_INVALIDARG (0x80070057)`** → accel-struct 的 `dataBuffer` 为 null → buildBLAS 解引用 null 段错误

逐个"绕过"(加 index buffer null 检查、禁 enhanced-barriers、换 device 类型)只是把同一根因推到下一个 null 点。

## 根因

运行时 `D3D12Core` 版本 **<** 框架编译所依赖的 Agility 特性版本 → 新特性(enhanced barriers / accel-struct storage flag)在旧 runtime 上不被支持 → `E_INVALIDARG` + 后续 null 解引用。

## 修法

vendor Agility SDK runtime(NuGet `Microsoft.Direct3D.D3D12`,例 1.615 x64):

1. 一个源文件 export 版本 + 路径:
   ```cpp
   extern "C" { __declspec(dllexport) extern const UINT  D3D12SDKVersion = 615; }
   extern "C" { __declspec(dllexport) extern const char* D3D12SDKPath    = u8".\\D3D12\\"; }
   ```
2. build 后把 `D3D12Core.dll`(+ 调试用 `d3d12SDKLayers.dll`)拷到 exe 旁 `D3D12/`(cmake post-build)。
3. **撤销一切"绕过"补丁**——它们在治表象。

**铁律**:每个用新 D3D12 特性的 GPU exe 都要带 Agility export + 部署 runtime,否则又是一串神秘 hang/segfault。

## 诊断纪律

别猜崩点——用程序内 StackWalk 自抓栈 + cdb + RelWithDebInfo 符号栈,定位到 `CreateCommittedResource` 的返回值(`E_INVALIDARG`)与哪个指针 null。表象成串时先怀疑"同一个更底层的根因",见 [`../code/diagnose-before-fixing.md`](../code/diagnose-before-fixing.md)。

## 通用性

任何 Windows + 链新版 D3D12 框架(自建 / vendored)+ 用 enhanced barriers 或 DXR 新特性的项目。是 Windows D3D12 工程的硬 hidden contract,微软文档少讲。

## 项目实例

renderer_test(NVRHI/Donut,RTX 3080)集成期 M4 加速结构一串 hang/segfault,一度误判"问题成串"准备放弃 GPU;重查锁定单根因 = stale `D3D12Core`,部署 Agility SDK 1.615 全解。经 `role-lane-coordination` 那次验证 harvest 出来。

## 相关

- [`../code/diagnose-before-fixing.md`](../code/diagnose-before-fixing.md) —— 单根因误判成"多个独立问题",要能区分竞争假设地取证
- 同目录 crash-hang 取证 / DLL 加载条目(见 `INDEX.md`)
