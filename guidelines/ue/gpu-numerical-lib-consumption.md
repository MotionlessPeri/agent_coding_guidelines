# UE 消费 GPU 数值加速库(如 cuDSS):没有官方等价物,bring-your-own 运行时加载 + 安全回退

在 UE 插件里想给**数值求解**(稀疏直接求解 / 稠密线代 / 自定义 GPU kernel)加 GPU 加速时的一组事实
+ 消费 pattern。以 NVIDIA cuDSS(GPU 稀疏直接求解)接入 curvenet 求解器为例,但结论对「往 UE 插件里塞
一个运行时加载的 GPU/native 数值库」通用。**非该需求可 skip。**

## 核心事实 / 规则

1. **UE 没有官方的 GPU 稀疏直接求解器**——引擎里稀疏/稠密线代**全是 CPU 端 Eigen**
   (GeometryProcessing 的 `MatrixSolver` 走 `Eigen::SparseLU/QR/CG`,且 `SimplicialLDLT`/Cholesky 因
   `EIGEN_MPL2_ONLY` 默认关掉;Chaos 的 `BlockSparseLinearSystem` 是迭代 CG)。**要 GPU 加速数值求解 →
   bring-your-own**(cuDSS / cuSOLVER / 自写 kernel),没有 drop-in 官方替代。
2. **bring-your-own 库用「运行时动态加载 + 安全回退」接**,不要编译期链 CUDA:
   - **编译期零 CUDA 依赖**:不 link 任何 CUDA 头/库;`LoadLibraryA`/`dlopen` + `GetProcAddress`/`dlsym`
     运行时取符号。→ 没装 CUDA / 没 N 卡的机器也能编、能跑(退回 CPU)。
   - **激活即 opt-in**:仅当环境变量开(如 `CA_BACKEND=cudss`)+ 库找得到才启用;任何失败(缺库 / 无 GPU /
     库报错)→ 返回 false → **调用方继续用 CPU 后端,默认行为零变化**。
   - **端到端自证**:激活时跑一个**已知解 sanity**(如 `K·ones` 回代必须还原 `ones`,误差超阈值即拒用回退)
     ——「库加载成功 + GPU 算对」一步到位,不靠盲信。
3. **跟引擎不冲突(实测)**:UE 引擎 + 自带插件**从不加载 `cudart64_*` / `cublas64_*`**——原生 CUDA 只走
   **Driver API(`nvcuda.dll`,显卡驱动自带、单版本向后兼容)**,视频编解码另加 `nvcuvid.dll`/`nvEncodeAPI64.dll`。
   所以你 bring-your-own 的 CUDA 12 runtime DLL(`cudart64_12`/`cublas64_12`/…)**不跟引擎撞同名**。唯一 CUDA 12.x
   同源是 `PythonMLPackages` 的 pip 包,隔离在内嵌 Python 进程(跑 PyTorch 训练才加载)。
4. **有官方可复用的 CUDA↔RHI interop**:`Engine/Source/Runtime/CUDA` 的 `FCUDAModule`(Driver API wrapper +
   按 LUID/UUID 匹配 RHI 选中的 GPU + external-memory/semaphore 导入)。但它只到 Driver API 层;`cudart`/你的库
   仍需自己 delay-load。纯 CPU↔GPU↔CPU 的求解(非 RHI 资源零拷贝)**用不上 interop**,别过度工程。

## 部署(复用既有 guidelines)

运行时 DLL(cuDSS 那套 ~5 个,数百 MB)进 UE 插件的坑跟别的 vendored 运行时 DLL 一样:

- **staging + 显式加载**:`RuntimeDependencies.Add("$(BinaryOutputDir)/x.dll", …)` stage 到插件
  `Binaries/Win64`;`StartupModule` 里 `IPluginManager::FindPlugin(...)->GetBaseDir()` +
  `FPlatformProcess::GetDllHandle` **显式加载**(插件 Binaries 不在默认 DLL 搜索路径)。详
  [`build-plugin-limitations.md`](build-plugin-limitations.md) Limitation 3(`BuildPlugin -Rocket` 交付包
  的 DLL 处理 + 瘦身)。
- **CRT 共享**:若靠环境变量(`_putenv_s`↔`getenv`)在插件启动处配置后端,设值方与读值方(core)须**同一
  CRT 实例**——core 源码编进 UE 模块时天然满足(同 `/MD`);core 若是独立 DLL 且 CRT 不同则跨不过去。
- **大二进制入库**:数百 MB 的 vendored DLL 用 **git-lfs**(先探测远端是否开 LFS)或托管到 P4;`Binaries/`
  是 build 产物应 `.gitignore`。
- **许可**:NVIDIA CUDA redist 可再分发(二进制形式、作为自家产品组件);对外交付需许可条款保护 NVIDIA 权利。

## ⚠️ 先 profile 再上 GPU:求解未必是瓶颈

**GPU 加速「求解」前,先 profile 确认求解真是热点**——否则加速比被非求解段稀释。这是
[`../code/diagnose-before-fixing.md`](../code/diagnose-before-fixing.md) 在 GPU 求解场景的实例:

- 先分段计时,别假设「慢在解方程」。curvenet 实测:per-frame 的瓶颈是 **RHS 侧的稀疏×稠密矩阵乘**
  (~18ms),不是线性 solve(GPU 回代本身只占几 ms)→ GPU 加速 solve 端到端只 ~1.2×,真正的大头要靠
  **矩阵乘并行**(见 [`ue-module-parallelism.md`](ue-module-parallelism.md))。
- **降精度(fp32)只在「求解是瓶颈」时才有意义**:非 solve-bound 的管线上 fp32 无加速(实测每帧几乎不变),
  且精度崩(~1e-5 冲破 1e-9 门槛)→ 死路。消费卡 fp64 弱 ≠ 值得转 fp32,得先确认 solve 占比。

## Anti-Patterns

| 反 pattern | 后果 | 修法 |
|---|---|---|
| 找 UE 官方 GPU 稀疏求解器 | 没有,白找 | bring-your-own 运行时加载库 |
| 编译期 link CUDA 头/库 | 没 CUDA 的机器编不了、无回退 | 运行时 `GetProcAddress`,失败回退 CPU |
| 激活 GPU 后端不做 sanity | 库「加载了但算错」静默出坏结果 | 已知解 sanity(K·1)校验,不过即回退 |
| 担心自带 CUDA DLL 跟引擎冲突 | 其实不撞(引擎只 nvcuda Driver API) | bring-your-own runtime DLL 安全 |
| 没 profile 就 GPU 加速 solve | 求解不是瓶颈时端到端提升有限 | 先分段计时定位真热点 |
| 消费卡 fp64 弱 → 直接转 fp32 | 非 solve-bound 时无加速 + 精度崩 | 先确认 solve 占比;bit-identical 的并行往往更值 |

## 项目实例参考

UE 5.8 curvenet 形变插件接 NVIDIA cuDSS(GPU 稀疏回代)到 curvenet 求解器:

- cuDSS 后端在共享 core 里、编译期零 CUDA 依赖、`CA_BACKEND=cudss` 激活、失败回退 CHOLMOD、`K·1` sanity 自证。
  RTX 3080 上每帧 solve 49→41ms(~1.2×;A800 数据中心卡 fp64 强,同事实测 e2e ~2.6×)。
- 5 个 runtime DLL(cudart/cublas/cublasLt/cudss/mtlayer,~750MB)走 `RuntimeDependencies` + StartupModule
  `GetDllHandle` + git-lfs 入库;跟已在用的 `libopenblas.dll` 同 pattern。
- 引擎源码实测:UE 5.8 无官方 GPU 稀疏求解器;引擎只加载 `nvcuda.dll`,不碰 `cudart/cublas` → 无冲突。
- profile 教训:以为瓶颈在 solve,实测在 RHS 矩阵乘;fp32 spike 无加速 + 精度崩(死路),放弃。

## 相关 Guidelines

- [`build-plugin-limitations.md`](build-plugin-limitations.md) —— vendored 运行时 DLL 进交付包的处理(Limitation 3)。
- [`ue-module-parallelism.md`](ue-module-parallelism.md) —— 真正的 per-frame 大头(矩阵乘)靠并行,不是靠 GPU solve。
- [`../code/diagnose-before-fixing.md`](../code/diagnose-before-fixing.md) —— 「先 profile 再优化」;本条的 fp32 死路是其实例。
- skill `ue-reference-engine-source` —— 「UE 有没有官方 X」「引擎加载哪些 CUDA DLL」都是读 engine source 得到的。
