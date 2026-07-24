# 测 C++ per-function 覆盖率 / CRAP：lizard + gcov/gcovr + OpenCppCoverage

C++ 项目想拿 **per-function 覆盖率**（或据此算 CRAP）做 review triage 时的完整操作流。C++ 分 g++（gcov）和 MSVC（OpenCppCoverage）两套覆盖率工具，同一项目常两套都要用。**非 C++ 项目跳过。** 指标本身怎么理解、怎么用，见 [`../guidelines/code/complexity-coverage-metrics.md`](../guidelines/code/complexity-coverage-metrics.md)。

## 工具速览

| 阶段 | 工具 | 说明 |
|---|---|---|
| 圈复杂度 CC | `lizard`（pip 装） | `lizard <dirs> --csv` 出 per-function CC。CSV 列序：NLOC, CCN, token, params, length, location, file, name, long_name, start, end |
| 覆盖率 · g++ 层 | `gcov` + `gcovr`（pip 装 gcovr） | gcov 需 `--coverage` 插桩重编译；gcovr 聚合 per-function（`blocks_percent` + `execution_count`） |
| 覆盖率 · MSVC 层 | `OpenCppCoverage` | MSVC native 二进制没有 gcov 数据。OpenCppCoverage 不重编译，运行时靠调试器 API + PDB 把指令地址映射回源码行采集覆盖。输出 cobertura XML / HTML |

## 流程

1. **CC**：`lizard <src dirs> -x "*/tests/*" -x "*/extern/*" --csv > cc.csv`。
2. **覆盖率 · g++ 层**：`cmake -DCMAKE_CXX_COMPILER=g++ -DCMAKE_CXX_FLAGS="--coverage -O0 -g -fno-inline" -DCMAKE_EXE_LINKER_FLAGS="--coverage"` 重编译 oracle 测试 → 跑通 → `gcovr --gcov-executable <gcov> -r <src root> --json out.json <build>`。
3. **覆盖率 · MSVC 层**：`cmake -G "Visual Studio 17 2022" -DCMAKE_TOOLCHAIN_FILE=<vcpkg>` 构建 **Debug**（要 PDB）→ `OpenCppCoverage --modules <exe名> --export_type cobertura:out.xml -- <测试exe>` → 解析 cobertura 的 per-line hits，用 lizard 的函数行范围聚合成 per-function line coverage。
4. **join + CRAP**：按 `(文件, 函数起始行)` 把 CC 与覆盖率配对（gcovr 的 lineno / cobertura 行号 vs lizard start，容忍几行偏差）；逐函数算 `CRAP = CC²·(1−cov)³ + CC`。

## Pitfall（都踩过，按撞见频率排）

| pitfall | 现象 | 规避 |
|---|---|---|
| **OpenCppCoverage 盘符解析 bug** | 在 H: / 网络盘 / 异常卷上构建 → 覆盖报告**空**（`lines-valid="0"`，空 `<packages/>`），日志里盘符被渲染成怪样（如 `H:` → `"D:2"`） | **源码 + 构建 + PDB 全放 C: 这类常规盘再跑**。根因：OpenCppCoverage 经卷映射（`QueryDosDevice` / volume GUID）解析盘符时对某些卷出错，官方 [issue #96](https://github.com/OpenCppCoverage/OpenCppCoverage/issues/96)（"network drive"）家族。**PDB 里存的路径本身是对的**（`strings <pdb>` 可验证），是 OpenCppCoverage 读取时搞错——所以别去查 PDB/编译器，直接换盘 |
| **OpenCppCoverage `--sources` 是正则** | `--sources 'Foo\bar'` 里的 `\b` `\c` 被当正则转义 → 匹配失败 → 空报告（但 module 显示已 selected，迷惑） | 用不含反斜杠的路径片段（如 `Foo`），或**干脆不传 `--sources`**、在解析脚本里按 basename 过滤 |
| **gcovr 跨盘符相对路径** | build 在 C:、源码在别的盘 → gcovr 报 `invalid relative_path` | 覆盖率构建放到与源码**同盘** |
| **gcovr `--filter` 易静默清空** | 短 filter（如 `'cpp'`）静默过滤掉全部 → 空 JSON | 出**全** JSON，在解析脚本里按路径过滤，别依赖 gcovr filter 正则 |
| **header-only inline 未调用即不 emit** | 从未被任何测试调用的 `inline` 函数在 gcovr 里**没有记录**（不是 0%，是不存在）；文件级覆盖率分母里也没有它的行 | 视作"测试构建里从未执行"，与真 0% 同等对待；别误判文件级 100% = 全测了 |
| **MinGW 运行时 DLL** | 覆盖率 exe 跑起来报 `0xc0000139`（ENTRYPOINT_NOT_FOUND） | PATH 前置对应 MinGW 的 `bin`，或链接 `-static -static-libgcc -static-libstdc++` |
| **失败构建留 stale 测试二进制** | 重编译失败但测试仍跑到旧 exe → 假绿覆盖率 | 看构建输出确认无编译/链接错，别只看测试结果（见 [`../guidelines/code/validation.md`](../guidelines/code/validation.md)） |

## 相关 Guidelines / Techniques

- [`../guidelines/code/complexity-coverage-metrics.md`](../guidelines/code/complexity-coverage-metrics.md) —— 这些数怎么理解、怎么用来 triage（作线索别当 KPI；CRAP 分层 + 真覆盖率前提）
- [`../guidelines/code/validation.md`](../guidelines/code/validation.md) —— stale test binary 等验证纪律
- [`../guidelines/cpp/INDEX.md`](../guidelines/cpp/INDEX.md) —— C++ 工程底座其它 hidden contract

## 项目实例参考

某跨图形 API 光追渲染器（C++，三层 RenderCore/Material/GUI）：g++ 层（RenderCore/cpu、GUI/core）用 gcov+gcovr、MSVC 层（Material，链 vcpkg MaterialX）用 OpenCppCoverage，join lizard CC 算 CRAP 做 review triage。一次性撞齐上表大半 pitfall——尤其 OpenCppCoverage 在 H: 盘的 `D:2` 空报告，改到 C: 盘构建后 586/679 行覆盖正常产出。评测结论见 [`../guidelines/code/complexity-coverage-metrics.md`](../guidelines/code/complexity-coverage-metrics.md) 的项目实例。
