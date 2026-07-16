# 性能测量先确认「测的是优化版二进制」+ 构建 flag 的 cache 粘性

native（C++）性能剖析里最容易出的**系统性错误**：不知不觉在一个**未优化（`/Od` / Debug）**的二进制上测，
热循环慢 5–10×，把真值撑大，据此下的结论（哪里是瓶颈、要优化谁、加速比多少）**全错**。根因往往不是
「手滑编了 Debug」，而是**关优化的开关粘在了构建 cache 里** + **host 从你没料到的目录加载了另一份二进制**。
C++ + MSVC/cmake + IDE、尤其**多 build 目录 / host 插件（DCC / 编辑器 / 服务从部署目录加载）**场景高频。

## 核心规则

1. **perf 测量必须在优化版（Release / `/O2`）二进制上做，并先确认你加载/跑的确实是它**——`/Od` 下矩阵/STL/无内联的库调用循环慢 5–10×。
2. **构建系统里「关优化」的开关是粘的**——cmake cache 变量 / `CMAKE_BUILD_TYPE` / IDE 的 Debug config，一旦设过就留在 cache，`Clean` / 重新生成工程 / 普通 rebuild **都不清**；必须显式覆盖（`-D...` 重配）/ 改 cache 文件 / 删整个 build 目录。
3. **搞清你加载的到底是哪一份二进制**——host（DCC / 编辑器 / 服务）常从多个候选路径（部署包 vs 各 build 目录）加载插件；给插件加一个**启动时打印本模块确切全路径**（Windows `GetModuleFileNameA` + 取本模块 handle）。
4. **区分 core-lib 计时 vs 集成层计时**——scope 到某一 target 的优化 flag **不影响**静态链进来的 core lib（仍 `/O2`）；同一进程里两层的 perf 结论可信度不同。

---

## 1. 症状:同一份源码、同一台机,perf 差 ~5×

热循环（逐元素矩阵运算、STL 容器操作、`MMatrix`/`FVector` 这类无内联的库类型运算）在 `/Od` 下没内联、
没向量化、带边界检查 → 单次慢 5–10×。一个真值 ~9ms 的回写循环，在 `/Od` 二进制上测成 ~49ms，看着就成了
「头号瓶颈」。**判据**:同一 repro、同一机器,perf 数字却差数倍 → **先怀疑「两次测的不是同一优化级的二进制」**,
别急着信那个大数字下结论。

## 2. 为什么「关优化」会粘住

- **cmake cache 变量是持久的**:自定义的「降优化」开关（如某个 `*_NOOPT` BOOL）、`CMAKE_BUILD_TYPE=Debug`
  一旦写进 `CMakeCache.txt` 就**一直生效**,之后 reconfigure / 重新 generate / rebuild 都读旧值,不会自己变回。
- **IDE 操作不清 cache**:VS 的 `Clean`（只删产物）、`ZERO_CHECK`（cmake 生成的重配 target,读旧 cache 不重置）、
  普通 Rebuild **都不改 cache 值**。对 `cmake -G "Visual Studio"` **生成**的 `.sln`,VS 也没有「清 cache」按钮
  （那个只对「以文件夹方式打开的 CMake 原生项目」有效）。
- **改法**（三选一）:reconfigure 传 `-D<FLAG>=<正确值>` 覆盖;直接改 `CMakeCache.txt` 那一行;删整个 build
  目录重 generate（VS generator 下只删 `CMakeCache.txt` 易留 stale `.vcxproj`,要删就删整个目录,见
  [`build-incremental-and-cmake.md`](build-incremental-and-cmake.md)）。

## 3. 「我加载的是哪份二进制」——启动打印

多 build 目录 / 部署包并存时,host 到底加载了哪份**极易搞错**（本条的头号触发场景就是「测了部署目录里那份,
而它恰被另一个开着降优化的 build 目录覆盖过」）。给插件的启动入口加一句打印本模块全路径,一眼看清:

```cpp
// 插件/模块启动入口(DCC 的 initialize、编辑器模块的 StartupModule 等)里:
#ifdef _WIN32
    HMODULE hMod = nullptr;
    if (GetModuleHandleExA(GET_MODULE_HANDLE_EX_FLAG_FROM_ADDRESS |
                           GET_MODULE_HANDLE_EX_FLAG_UNCHANGED_REFCOUNT,
                           reinterpret_cast<LPCSTR>(&someFuncInThisModule), &hMod) && hMod) {
        char buf[MAX_PATH] = {0};
        if (GetModuleFileNameA(hMod, buf, MAX_PATH) > 0)
            LOG("plugin loaded from: %s", buf);   // 用项目日志设施
    }
#endif
```

`&someFuncInThisModule` 取本模块内任意函数地址 → `GET_MODULE_HANDLE_EX_FLAG_FROM_ADDRESS` 拿到本模块 handle
→ `GetModuleFileNameA` 得确切 `.dll`/`.so` 全路径。看路径就知道加载的是部署包还是哪个 build 目录、是不是
优化版。**这一句能省下「为什么 perf 对不上」的几小时**。

## 4. core-lib vs 集成层:降优化的作用域

「降优化」的 flag 常只 scope 到**某一个 target**（如插件集成层那个 TU / 那个 `.dll`）。**静态链进它的 core
计算库不受影响,仍是 `/O2`**。所以同一进程里:

- **core 计算耗时**（求解器 / 算法核心,恒 `/O2`）:即使集成层被降优化,这块数字仍可信、跨平台可比。
- **集成层耗时**（marshal / 数据回写 / 与 host API 交互,受本层 flag 影响）:被降优化时会虚高。

排查时先分清热点落在哪层:若「集成层某循环」突然巨大而「core 求解」正常,**优先怀疑集成层被降优化了**,
而不是那个循环真慢。

## Anti-Patterns

| 反 pattern | 后果 | 修法 |
|-----------|------|------|
| 直接信 perf 大数字下结论,不问优化级 | 在 `/Od` 上把 9ms 测成 49ms,优化任务书写错方向 | 先确认测的是 `/O2` 优化版 |
| 以为 `Clean`/`ZERO_CHECK`/rebuild 会清掉降优化开关 | cache 粘着,一直 `/Od` | `-D` 覆盖 / 改 cache / 删 build 目录 |
| 不确认 host 加载了哪份二进制 | 多 build 目录/部署包并存时测错那份 | 启动打印本模块 `GetModuleFileName` 全路径 |
| 把集成层被降优化的虚高当「该循环真慢」 | 优化错对象 | 分清 core(恒 /O2) vs 集成层(受 flag) |
| 同一 repro 数字差数倍仍各自下结论 | 两次测的不是同一二进制,结论都不可信 | 差数倍先归因到二进制/优化级差异 |

## 项目实例参考

某 C++ DCC 插件的 GPU 后端 perf 剖析:一度测出「某逐顶点数据回写循环 ~49ms、比核心求解还大、是头号瓶颈」
并据此写了优化任务书——**全错**。另一对话同 repro 实测该循环只 ~9ms。查了很久才定位:性能测量时 host 加载的是
**部署目录**里的插件,而那份恰被**另一个开着降优化 cache 开关的 build 目录**以 `/Od` 编出并覆盖过;`/Od` 下
矩阵运算循环慢 ~5× → 9ms 撑成 49ms。核心求解库静态链且恒 `/O2`,所以**求解的 A/B 数字当时仍有效,错的只有
集成层那个回写循环**。定位后:(1) 把降优化 cache 开关显式改回、重编出 `/O2` 部署包(marshal 回落 ~9ms);
(2) 给插件启动入口加了打印 `.dll` 全路径的功能,以后一眼确认加载的是哪份。

## 相关 Guidelines

- [`build-incremental-and-cmake.md`](build-incremental-and-cmake.md) — 同族「构建系统没按你想的来」陷阱(增量漏重编 / stale `.vcxproj` / 删 build 目录);本条是其「优化 flag cache 粘性 + 测错二进制」维度。
- [`hot-path-cpp.md`](hot-path-cpp.md) — 热路径优化(move / dynamic_cast);性能结论要 profiler 证据——但**前提是测的是优化版**,本条是那个前提。
- [`../code/validation.md`](../code/validation.md) — 「看代码/本地看着对 ≠ 验证」;perf 结论要实测数字,而实测必须在正确(优化版、确认加载的)二进制上。
- [`../code/diagnose-before-fixing.md`](../code/diagnose-before-fixing.md) — 本条的失败正是「从一个错误测量下了错结论」;两个竞争假设(循环真慢 vs 测了 /Od)要用「换 /O2 二进制重测」区分,别直接改代码。
