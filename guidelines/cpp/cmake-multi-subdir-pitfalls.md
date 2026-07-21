# 多子目录 CMake 的三个顺序 / 作用域坑

多个 `add_subdirectory` 的工程(库 + 消费方 + 集成 app),子目录之间引用 target / 变量时,三个跟**顺序和作用域**有关的静默坑。

## 1. 子目录 `set` 的变量,从父作用域求值为空

- **症状**:照抄某框架的宏(如 Donut 的 `donut_compile_shaders`),它内部本该带上 `NVRHI_DEFAULT_VK_REGISTER_OFFSETS`,但从**父作用域**(集成 app 的 CMake)调时该选项**没进命令行**(verbose build 实测确认),行为静默不对。
- **根因**:那个变量是在框架**子目录作用域** `set()` 的;CMake 变量默认不向上渗透到父作用域,父作用域调用点求值为**空**。
- **修法**:别依赖"父作用域看得见子目录 set 的变量";在自己的 `CMakeLists.txt` 里**显式写死**需要的值(如显式传 `--tRegShift/--sRegShift/...`)。

## 2. `if(TARGET x)` 依赖 `add_subdirectory` 顺序

- **症状**:root `CMakeLists.txt` 里 `if(TARGET material_core)` 该真却为假,条件分支没进。
- **根因**:root 先 `add_subdirectory(consumer)` 后 `add_subdirectory(material_core)`,处理 consumer 时 `material_core` target **还没定义** → `if(TARGET ...)` 为假(**target 存在性依赖 add_subdirectory 顺序**)。
- **修法**:别用 `if(TARGET ...)` 做交叉引用守卫;用 `target_link_libraries(consumer PRIVATE material_core)` 的 **forward-reference**——CMake 在 **generate 阶段**才解析 target 名,顺序无关。区分 standalone / 集成 build 用 `CMAKE_CURRENT_SOURCE_DIR STREQUAL CMAKE_SOURCE_DIR`(是否 top-level)。

## 3. 可复用库的测试 target 要门控,别拖累消费方

- **症状**:`add_subdirectory(你的库)` 后,消费方被迫构建你的测试 exe。
- **修法**:测试 target 用 `PROJECT_IS_TOP_LEVEL`(cmake ≥ 3.21)或 `option(<LIB>_BUILD_TESTS ...)` 门控,只在独立构建时建。

## 项目实例

renderer_test 集成期(多子目录:RenderCore app + Material 库 + GUI)三条都踩到。经 `role-lane-coordination` 那次验证 harvest。

## 相关

- 同目录其它 cmake / 增量编译条目(见 `INDEX.md`)
