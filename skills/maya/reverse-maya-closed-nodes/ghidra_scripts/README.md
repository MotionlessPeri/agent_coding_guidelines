# ghidra_scripts —— headless post-scripts(逆向 native DLL 复用)

配合 `analyzeHeadless.bat -process <dll> -noanalysis -scriptPath <这里> -postScript <脚本> <args>` 用。
换关键词即可复用到任何带符号的 native DLL;全部把结果导成**文本文件**供 agent Read + grep 消费,不点 GUI。

| 脚本 | 参数 | 作用 |
|---|---|---|
| `ExportByKeywords.java` | `<outDir> <kw1,kw2,...>` | 关键词宽召回(函数名/符号/字符串三路)+ 一层调用邻域 → `decompiled/NNN_<addr>_<name>.c` + `target_index.txt` |
| `ExportFunctionsByAddress.java` | `<outDir> <addr>...` | 按入口地址精确导反编译(每个带 `// address/name/prototype` 头) |
| `DumpVtables.java` | `<outFile> <kw1,kw2,...>` | MSVC `vftable` 每槽函数指针(恢复虚表/类结构) |
| `ExportXrefs.java` | `<outFile> <kw1,kw2,...>` | 关键字符串/符号的引用点 + 所在函数(定位无导出符号的内部实现) |
| `DumpInstructions.java` | `<outFile> <start> <end>` | 地址区间反汇编(核对「C 反编译漏参数」,见 SKILL.md §3) |

关键词大小写不敏感、逗号分隔(如 `baryCoord,influence,smooth`)。地址统一用 `module + RVA` 记录(防 ASLR)。
完整调用模板与 agent 消费方式见上级 `SKILL.md` 的「Ghidra headless 驱动」节。

来源:泛化自 `curve_articulation_maya` / `maya_reverse` 项目实测用过的脚本(原版按 proximityWrap 硬编码关键词)。
