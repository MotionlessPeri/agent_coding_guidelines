# native binding 的「可达面」:lib 里有 ≠ 消费方能调

给 C++ 库做语言绑定(pybind11 / nanobind / Cython / SWIG / 裸 C FFI,乃至 Maya/UE 插件导出)
供别的语言/进程消费时,一条反复被忽略的事实:**消费方能调的 = 绑定模块显式导出的那一小面,
不是底层 lib 里实现了什么**。把「lib 里有某功能」当成「消费方能用」是常见误判。框架无关。

## 核心规则

1. **可达 API = 绑定导出面,不是 lib 内容**。判断消费方能调什么,**看绑定模块**(pybind `PYBIND11_MODULE`
   的 `.def` 列表 / `.pyi` / 导出符号表),不是看 lib 源码里有多少类和方法。
2. **以运行期 introspection 为准,不靠读源码猜**。加载真实产物,`dir(obj)` / `inspect` / `dumpbin /exports`
   看**实际**导出了什么——绑定源码可能跟已构建产物不一致(改了没重建),运行期才是真相。
3. **暴露一个 lib 功能 = 三步缺一不可**:(a) 该功能的源**编进绑定所链接的 lib**;(b) 绑定模块里**显式绑定**
   (加 `.def` / 包一层);(c) **重建**绑定产物。少任何一步,消费方都调不到——即便 lib 里测试全绿。
4. **别在绑定里悄悄降级/换后端**:消费方发现某功能够不着时,先确认是「没绑定」而非「实现有 bug」,
   按需扩绑定,而不是在绑定层塞个假实现。

## 常踩的 build 陷阱:源进了 lib,test/别的 target 还在直接编它 → 重复符号

把一个 `.cpp` 从「只编进各 test exe / 某 target」**提升进 lib** 时,任何**既直接编该 `.cpp`、又链接该 lib**
的 target 会**重复符号**(MSVC `LNK2005` + `LNK1169`;gcc/clang multiple definition)。修法:该 `.cpp` 进 lib 后,
把仍直接编它的 target 改成**只链 lib、不再直接编该源**。

```cmake
# ❌ PBIKBody.cpp 已进 lib 后,test 还直接编它 + 链 lib → LNK2005
add_executable(foo_test foo_test.cpp ../src/PBIKBody.cpp)
target_link_libraries(foo_test PRIVATE mylib gtest_main)   # mylib 也含 PBIKBody → 重复
# ✅ 只链 lib
add_executable(foo_test foo_test.cpp)
target_link_libraries(foo_test PRIVATE mylib gtest_main)
```

## Anti-Patterns

| 反 pattern | 后果 | 修法 |
|---|---|---|
| 「lib 里实现了 X」就以为消费方能调 X | 消费方 import 后根本没这方法 | 看绑定导出面;运行期 `dir()` 确认 |
| 读绑定源码判断可达面 | 源跟已构建产物不一致(没重建) | 加载真实产物 introspect |
| 暴露功能只改了绑定源,没重建产物 | 消费方拿的还是旧产物 | 改绑定后重建,再 introspect 验证 |
| 把 lib 源提进 lib 却没撤 test 的直接编译 | LNK2005 重复符号 | 进 lib 后 target 只链 lib |
| 绑定层塞假实现掩盖「没绑定」 | 消费方拿到错结果 | 确认是缺绑定 → 扩绑定,别造假 |

## 跟其它条目的关系

- [`multi-dll-plugin.md`](multi-dll-plugin.md) —— 跨 DLL 符号导出/单例;本条是「导出面 = 消费契约」在**语言绑定**
  维度的推广。
- [`build-incremental-and-cmake.md`](build-incremental-and-cmake.md) —— 构建系统没跟上代码改动的一族坑;「进 lib 后
  重复符号」是其近亲(改了源列表要重配 + 撤重复编译)。
- [`../code/validation.md`](../code/validation.md) —— 「看代码 ≠ 验证」;可达面也要**实测**(introspect 产物 +
  跑一次调用),不靠读源断言。

## 项目实例参考

RetargetStudy:一个 pybind 的 C++ retarget 库(`retarget_core`)+ 消费它的 Python GUI。
- 排查「GUI 能接入哪些算子」时,**运行期 `dir(retarget_core.Retargeter)`** 发现 `.pyd` 只导出 11 个方法 / 3 种算子;
  而 lib 里其实还实现了 PBIK 全身 IK + 7 个增强算子(有完整 C++ 测试)——**只是没进 pybind**,消费方够不着。
  若只读绑定源(或 lib 源)会误判。
- 暴露 PBIK/增强算子时严格走三步:把 `PBIK*.cpp` 等**加进 lib 的 CMake `add_library`** + 在 `retarget_module.cpp`
  加 `add_*_op` 绑定 + **重建 cp310 `.pyd`**,再 `dir()` + 实调确认可达。
- 提 PBIK 源进 lib 时,原本各 PBIK test exe 还直接编 `../solvers/PBIK*.cpp` + 链 lib → **LNK2005**;把这些 test
  改成只链 lib(不再直接编那些 `.cpp`)后 ctest 全绿。
