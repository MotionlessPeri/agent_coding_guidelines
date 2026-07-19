# `std::make_format_args` 新版 MSVC STL 只接受左值（本地旧工具链编得过、CI 新工具链 FAIL）

写 `std::format` / `std::vformat` 的可变参包装模板（典型：日志 / 计时设施的统一格式化入口）时，一个
**「本地编译通过、CI 编译失败」**的高迷惑 bug：`std::make_format_args` 在**新版 MSVC STL**
（VS 2022 17.10+ / MSVC toolset 14.40+）改成**只接受左值引用**（`Args&...`），传右值
（典型写法 `std::forward<Args>(args)...`）触发 `C2664` + `C2672`。旧工具链的旧签名 `const Args&...`
接受右值 → 开发机编得过，只在**升级过工具链的机器（最常见 = CI runner）**暴露。跨框架通用——
任何 `std::format` 的转发包装都可能命中。

## 核心规则

1. **`std::make_format_args` 传具名形参 `args...`，不要 `std::forward<Args>(args)...`**——具名
   forwarding-reference 形参「按名字用」就是左值，新旧 STL 都能绑（`Args&` / `const Args&`）。
2. **「本地编得过」≠「所有工具链编得过」**——本地旧工具链编过 ≠ CI 新工具链编过，构建类结论以 CI（或同版本工具链）为准。本条是通用「标准 LEVEL vs toolchain VERSION」框架的具体实例（新 STL 收紧 API 让旧写法 FAIL），general 框架见 [`modern-cpp-by-standard.md`](modern-cpp-by-standard.md)。

## 机制

```cpp
template <typename... Args>
std::string fmt_wrap(std::string_view fmt, Args&&... args) {
    // ❌ 新版 MSVC STL：make_format_args(_Args&...) 要左值；std::forward 对「调用方传右值」的 Args
    //    产出右值 → 绑不上 _Args& → C2664，随即 vformat 找不到匹配重载 → C2672
    return std::vformat(fmt, std::make_format_args(std::forward<Args>(args)...));

    // ✅ 具名形参按名字用即左值，绑 _Args&（新）/ const _Args&（旧）都行；
    //    vformat 在同一表达式即时消费，无悬垂
    return std::vformat(fmt, std::make_format_args(args...));
}
```

- 标准演进（LWG 3810 / P2905，MSVC 约 VS 2022 17.10 落地）把 `make_format_args` 参数从
  `const Args&...` 收紧为 `Args&...`（非 const 左值引用），**为防止把临时量的引用存进 format-args
  store 造成悬垂**。
- 后果：任何给 `make_format_args` 传**右值 / 临时量**的写法在新 STL 上 ill-formed。
  `std::forward<Args>(args)...` 正是把具名形参对「rvalue-deduced 的 Args」恢复成右值，于是命中。
- 修法本质 = **传左值**：具名形参 `args`（哪怕声明类型是 `T&&`）用名字引用时是左值，直接 `args...`
  即可，不需要（也不应该）`forward`。格式化只读取实参、不移动，左值语义完全正确。
- 注意区分：`make_format_args(obj.x, obj.y)` 这类**成员访问 / 具名变量**本来就是左值，不受影响，
  别顺手改。真正要改的只是 `std::forward<...>(...)` 那种把左值转回右值的写法。

## 症状 / 怎么定位

| 现象 | 说明 |
|---|---|
| `error C2664: make_format_args(...): 无法将参数 N 从 '_Ty' 转换为 '_Ty &'` | 传了右值给「要左值」的新重载 |
| 紧随 `error C2672: 'vformat': 未找到匹配的重载函数` | make_format_args 没产出合法 store，vformat 连锁失败 |
| **本地编译通过、CI（或同事新机）编译失败** | 本地 MSVC toolset < 14.40（旧签名容右值），CI ≥ 14.40（新签名拒右值）——**先比对两边 `cl.exe` / MSVC toolset 版本**，别怀疑代码逻辑 |
| 一个公共日志 / 格式化头，报错在**同一行**、跨大量 TU 重复（几十上百条） | 该模板被多处实例化；改一处（头文件那行）全消 |

## Anti-Patterns

| 反 pattern | 后果 | 修法 |
|---|---|---|
| `make_format_args(std::forward<Args>(args)...)` | 新 MSVC STL `C2664`/`C2672` | `make_format_args(args...)`（传左值） |
| 「本地编过就以为能发 / 能过 CI」 | CI / 新机工具链更严 → 编译 FAIL，发版链断在 build 阶段 | 构建结论以 CI 同版本工具链为准（见 `validation.md`） |
| 撞 `C2664` 去猜类型 / 加 `cast` / 换 `format_context` | 改错方向、越绕越乱 | 认准 `make_format_args` 左值契约，去掉 `forward` |
| 只修 CI 报的那一处，漏同头其它同款写法 | 下一个 TU / 开启某 `#if` 后再挂一轮 CI | grep 全库 `make_format_args(std::forward` 一次修净 |

## 项目实例参考

某 Maya C++ 插件发版：日志设施的 `FormatWithFunc` / `LogTiming` + 计时 `ScopedTimer::format` 三处用
`std::vformat(fmt, std::make_format_args(std::forward<Args>(args)...))`。开发机 MSVC 旧，编译通过、
headless 单测 51/51 全绿；打 tag 触发 CI（runner MSVC **14.44.35207**）→ build 阶段公共头
`CALog.h` 同一行 `C2664 ×98 + C2672 ×7`（公共头跨大量 TU 实例化重复报）。三处统一改
`make_format_args(args...)` 后 CI 编译通过、发版成功。教训双份：(1) `make_format_args` 左值契约；
(2) 本地旧工具链是「假绿」，真 gate 是 CI 的新工具链——同一份代码本地编过不代表 CI 编得过。

## 相关 Guidelines

- [`modern-cpp-by-standard.md`](modern-cpp-by-standard.md) — 通用的「标准 LEVEL vs toolchain VERSION、本地旧 toolset ≠ CI 新 toolset」框架（general 家）；本条是其「新 STL 收紧 API 契约让旧写法 FAIL」的具体实例。
- [`build-incremental-and-cmake.md`](build-incremental-and-cmake.md) — 同属「构建环境 / 工具链差异导致的编译问题」族；那条管增量漏重编 / stale `.vcxproj`，本条管**工具链版本间 STL API 契约收紧**。
- [`../code/validation.md`](../code/validation.md) — 「看代码 / 本地编过 ≠ 验证」；构建类结论必须在目标工具链（CI）实测。本条是其在「local 旧 toolset vs CI 新 toolset」上的具体实例。
- [`../code/diagnose-before-fixing.md`](../code/diagnose-before-fixing.md) — 撞 `C2664` 别猜：先读报错 API 的签名（`make_format_args` 要左值）+ 比对本地/CI 工具链版本，区分「代码错」还是「工具链版本差异」两个竞争假设。
