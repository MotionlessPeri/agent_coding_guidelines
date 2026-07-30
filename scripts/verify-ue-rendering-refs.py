#!/usr/bin/env python3
"""校验 references/ue-rendering/ 里的源码路径与 CVar 断言是否真的存在于 UE 引擎源码。

为什么需要这个：知识库里的路径和 CVar 名读起来都很合理，但模型会生成"看着像真的"
的假文件名（实测 239 条路径断言里约 60 条在 5.8 里根本不存在）。靠人读发现不了，
靠脚本一跑就现形。

判官是引擎源码本身，不是写文档的人——所以同一个 agent 既写文档又写这个脚本也糊弄不过去。

用法：
    python scripts/verify-ue-rendering-refs.py                 # 用自动探测的引擎根
    python scripts/verify-ue-rendering-refs.py --ue <引擎根>    # 指定引擎根
    python scripts/verify-ue-rendering-refs.py --paths-only    # 跳过较慢的 CVar 扫描

引擎根 = 含 `Engine/` 子目录的那一层，例如 `H:/Epic Games/UE_5.8`。
也可通过环境变量 `UE_ROOT` 指定。

退出码：0 = 无 MISSING；1 = 存在 MISSING（供 CI / 提交前 gate 用）。
"""

from __future__ import annotations

import argparse
import collections
import json
import os
import re
import sys
from pathlib import Path

DOC_DIR = Path(__file__).resolve().parent.parent / "references" / "ue-rendering"

# 引擎根候选——按新版本优先。找不到时用 --ue 或 UE_ROOT 指定。
UE_ROOT_CANDIDATES = [
    r"H:/Epic Games/UE_5.8",
    r"C:/Program Files/Epic Games/UE_5.8",
    r"C:/Program Files/Epic Games/UE_5.7",
    r"D:/UnrealEngine",
]

SOURCE_EXTS = (".h", ".cpp", ".inl", ".ush", ".usf", ".cs")

# 扫描引擎树时跳过的目录——只含产物，不含源码。
SKIP_DIRS = {
    "Binaries", "Intermediate", "DerivedDataCache", "Saved",
    "Content", "DerivedDataBackendGraph", ".git",
}

# 反引号里带目录分隔符的源码文件路径。
PATH_RE = re.compile(r"`([A-Za-z][A-Za-z0-9_./+-]*\.(?:h|cpp|inl|ush|usf|cs))`")

# `Lumen.cpp/.h` 这种合写形态——要拆成两条再查，否则会被误判成不存在。
COMBINED_RE = re.compile(r"^(?P<stem>.+?)\.(?P<first>[a-z]+)/\.(?P<second>[a-z]+)$")

# 反引号里的 CVar 名。UE 的渲染 CVar 前缀不止 `r.`。
# 末尾的负向断言排掉源码文件名——`Nanite.cpp` / `Lumen.h` 这类会被点分模式误匹配成 CVar。
CVAR_RE = re.compile(
    r"`((?:r|D3D12|vk|vr|sg|fx|au|p|net|Slate|Nanite|Lumen|renderdoc)"
    r"\.[A-Za-z0-9_.]*[A-Za-z0-9_])`(?<!\.cpp`)(?<!\.h`)(?<!\.inl`)(?<!\.ush`)(?<!\.usf`)(?<!\.cs`)"
)

# 引擎源码里 CVar 名的字面量出现形式。
CVAR_LITERAL_RE = re.compile(r'TEXT\(\s*"([A-Za-z][A-Za-z0-9_.]*\.[A-Za-z0-9_.]+)"')

# 反引号里的 C++ 符号：UE 命名法的类型（F/U/I/E/S/T 前缀 + 驼峰）、全大写宏、Foo::Bar。
# 加这一轴是因为实测「文件真、符号假」的组合确实存在——card-11 的源码导航表抽查 9 个符号
# 有 6 个不在引擎里，跟路径、CVar 是三条独立的编造轴。
SYMBOL_RE = re.compile(
    r"`((?:[FUIEST][A-Za-z0-9_]{3,}(?:::[A-Za-z_][A-Za-z0-9_]*)?"
    r"|[A-Z][A-Z0-9_]{5,}))`"
)

# 这些是通用词或本仓库自造的说明性标识，不是引擎符号，不参与判定。
SYMBOL_IGNORE = {
    "TODO", "FIXME", "README", "AGENTS", "MEMORY", "SKILL",
}

# 引擎源码里的标识符 token。判定标准是"作为 token 出现过"——比只认声明处更保守，
# 宁可漏报也不误报，因为误报会让人去改本来正确的内容。
SYMBOL_TOKEN_RE = re.compile(r"\b((?:[FUIEST][A-Za-z0-9_]{3,})|(?:[A-Z][A-Z0-9_]{5,}))\b")


def resolve_ue_root(explicit: str | None) -> Path:
    """定位引擎根目录。显式参数 > 环境变量 > 候选列表。"""
    for cand in filter(None, [explicit, os.environ.get("UE_ROOT"), *UE_ROOT_CANDIDATES]):
        p = Path(cand)
        if (p / "Engine").is_dir():
            return p
    sys.exit(
        "找不到 UE 引擎根目录。用 --ue <路径> 指定，或设环境变量 UE_ROOT。\n"
        "引擎根 = 含 Engine/ 子目录的那一层。"
    )


def build_source_index(ue_root: Path) -> dict[str, list[str]]:
    """建 basename -> [相对引擎根的路径] 索引。

    用于把"文件存在但路径写错"和"文件根本不存在"区分开——这是全脚本最关键的一刀，
    没有它就只能报"62% 对不上"，分不清是锚点不一致还是幻觉。
    """
    index: dict[str, list[str]] = collections.defaultdict(list)
    engine_dir = ue_root / "Engine"
    for root, dirs, files in os.walk(engine_dir):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        rel_root = os.path.relpath(root, ue_root).replace("\\", "/")
        for fn in files:
            if fn.endswith(SOURCE_EXTS):
                index[fn].append(f"{rel_root}/{fn}")
    return index


def build_cvar_index(ue_root: Path, cache: Path | None = None) -> set[str]:
    """收集引擎源码里所有 `TEXT("...")` 形式的点分名字面量。

    只要文档里的 CVar 名在引擎源码里作为字面量出现过就算存在——不追究它是
    TAutoConsoleVariable 还是别的注册方式，因为我们要答的问题只是"这个名字是不是真的"。

    扫全量引擎源码要几分钟，所以结果落盘缓存。引擎换版本时删掉缓存文件即可。
    """
    if cache and cache.exists():
        data = json.loads(cache.read_text(encoding="utf-8"))
        if data.get("ue_root") == str(ue_root):
            print(f"  复用缓存 {cache.name}（{len(data['names'])} 个名字）")
            return set(data["names"])

    names: set[str] = set()
    # 必须扫整个 Engine/ 而不只是 Engine/Source/——大量 CVar 声明在
    # Engine/Plugins/*/Source/ 下（XR、各种 Runtime 插件）。只扫 Source 会把它们
    # 全判成"不存在"，制造一批假阳性。
    engine_dir = ue_root / "Engine"
    scanned = 0
    for root, dirs, files in os.walk(engine_dir):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for fn in files:
            if not fn.endswith((".h", ".cpp", ".inl")):
                continue
            try:
                text = Path(root, fn).read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            names.update(CVAR_LITERAL_RE.findall(text))
            scanned += 1
    print(f"  扫了 {scanned} 个源码文件")
    if cache:
        cache.write_text(
            json.dumps({"ue_root": str(ue_root), "names": sorted(names)}, ensure_ascii=False),
            encoding="utf-8",
        )
    return names


def build_symbol_index(ue_root: Path, cache: Path | None = None) -> set[str]:
    """收集引擎源码里出现过的 UE 命名法标识符。

    跟 CVar 索引一样落盘缓存——扫全量源码要几分钟。引擎换版本时删缓存。
    """
    if cache and cache.exists():
        data = json.loads(cache.read_text(encoding="utf-8"))
        if data.get("ue_root") == str(ue_root):
            print(f"  复用缓存 {cache.name}（{len(data['symbols'])} 个标识符）")
            return set(data["symbols"])

    symbols: set[str] = set()
    scanned = 0
    for root, dirs, files in os.walk(ue_root / "Engine"):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for fn in files:
            if not fn.endswith((".h", ".cpp", ".inl", ".ush", ".usf")):
                continue
            try:
                text = Path(root, fn).read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            symbols.update(SYMBOL_TOKEN_RE.findall(text))
            scanned += 1
    print(f"  扫了 {scanned} 个源码文件，得到 {len(symbols)} 个标识符")
    if cache:
        cache.write_text(
            json.dumps({"ue_root": str(ue_root), "symbols": sorted(symbols)}, ensure_ascii=False),
            encoding="utf-8",
        )
    return symbols


def expand_combined(path: str) -> list[str]:
    """把 `Lumen.cpp/.h` 展开成 [`Lumen.cpp`, `Lumen.h`]，其余原样返回。"""
    m = COMBINED_RE.match(path)
    if not m:
        return [path]
    stem, first, second = m.group("stem"), m.group("first"), m.group("second")
    return [f"{stem}.{first}", f"{stem}.{second}"]


def strip_ignored(text: str) -> str:
    """去掉 `<!-- verify:ignore-start -->` … `<!-- verify:ignore-end -->` 之间的内容。

    文档里有时**故意**写出不存在的名字——比如「这些名字在调研稿里出现过但引擎里没有」
    的对照表。这类段落不是断言而是反面教材，不该被当成缺陷统计。
    """
    return re.sub(
        r"<!--\s*verify:ignore-start\s*-->.*?<!--\s*verify:ignore-end\s*-->",
        "", text, flags=re.S,
    )


def collect_assertions(doc_dir: Path):
    """从文档里收集路径 / CVar / 符号三类断言，各自附带出现的文件名。"""
    paths: dict[str, set[str]] = collections.defaultdict(set)
    cvars: dict[str, set[str]] = collections.defaultdict(set)
    symbols: dict[str, set[str]] = collections.defaultdict(set)
    for md in sorted(doc_dir.glob("*.md")):
        text = strip_ignored(md.read_text(encoding="utf-8"))
        for raw in PATH_RE.findall(text):
            if "/" not in raw:
                continue  # 裸文件名无法校验路径，跳过
            for expanded in expand_combined(raw):
                if "/" in expanded:
                    paths[expanded].add(md.name)
                else:
                    # `Lumen.cpp/.h` 展开后变成裸名，改用原串登记以便报告指回原文
                    paths[raw].add(md.name)
        for raw in CVAR_RE.findall(text):
            cvars[raw].add(md.name)
        for raw in SYMBOL_RE.findall(text):
            if raw not in SYMBOL_IGNORE:
                symbols[raw].add(md.name)
    return paths, cvars, symbols


def classify_path(path: str, ue_root: Path, index: dict[str, list[str]]) -> tuple[str, list[str]]:
    """把一条路径断言分类成 OK / FIX / MISSING。

    OK      —— 从引擎根直接可解析（规范写法）
    FIX     —— 文件存在但断言的路径不规范，返回建议的规范路径
    MISSING —— 引擎树里没有这个 basename 的文件
    """
    # 合写形态本身不是有效路径，逐个展开判定，全部存在才算 OK
    parts = expand_combined(path)
    if len(parts) > 1:
        results = [classify_path(p, ue_root, index) for p in parts]
        if all(r[0] == "OK" for r in results):
            return "FIX", [p for r in results for p in (r[1] or [])] or parts
        suggestions = [s for r in results for s in r[1]]
        return ("MISSING" if any(r[0] == "MISSING" for r in results) else "FIX"), suggestions

    if (ue_root / path).exists():
        return "OK", []

    # 非规范锚点：相对 Engine/ 或相对 Engine/Source/
    for prefix in ("Engine/", "Engine/Source/"):
        if (ue_root / (prefix + path)).exists():
            return "FIX", [prefix + path]

    basename = path.rsplit("/", 1)[-1]
    if basename in index:
        return "FIX", index[basename]
    return "MISSING", []


# 子 agent 把过程性输出（修订工单 / 改动汇总 / 对话式收尾）留在交付文档里的特征串。
# 这类内容指向一次已经消失的修复动作，半年后是悬空引用，比没注释更糟。
LEAK_MARKERS = [
    "```markdown",
    "修复总结",
    "本次修复",
    "以下是完整的修复版",
    "文件已写入",
    "如需深入某个具体主题",
    "紧急修复：",
    "以下是本次",
]


def check_structure(doc_dir: Path) -> list[str]:
    """markdown 结构 lint —— 抓渲染层面的损坏，不看内容对不对。

    加这层是因为围栏奇偶反转这种损坏在文本 diff 里几乎看不出来（每行都还在），
    但渲染出来散文变代码、表格散架。只有机械查围栏配平才能稳定抓到。
    """
    problems: list[str] = []
    for md in sorted(doc_dir.glob("*.md")):
        lines = md.read_text(encoding="utf-8").split("\n")

        if not lines or not lines[0].startswith("# "):
            problems.append(f"{md.name}: 首行不是 H1 标题（拿到的是 {lines[0][:40]!r}）")

        fences = [(i + 1, l) for i, l in enumerate(lines) if l.startswith("```")]
        if len(fences) % 2:
            problems.append(f"{md.name}: 代码围栏 {len(fences)} 个，奇数——未配平，渲染会错位")

        # mermaid 块首行必须是有效的图类型声明，否则渲染器直接放弃
        valid_directives = ("flowchart", "graph", "sequenceDiagram", "classDiagram",
                           "stateDiagram", "erDiagram", "journey", "gantt", "pie")
        for idx, (lineno, fence) in enumerate(fences):
            if fence.strip() != "```mermaid":
                continue
            if lineno >= len(lines):
                problems.append(f"{md.name}:{lineno}: mermaid 块没有内容")
                continue
            first = lines[lineno].strip()
            if not first.startswith(valid_directives):
                problems.append(f"{md.name}:{lineno + 1}: mermaid 首行不是有效图类型：{first[:40]!r}")

        for marker in LEAK_MARKERS:
            for i, l in enumerate(lines, 1):
                if marker in l:
                    problems.append(f"{md.name}:{i}: 残留过程性输出标记 {marker!r}")

        # 表格列数不一致会让整表散架；只比表头和分隔行，正文行允许含转义竖线
        for i in range(len(lines) - 1):
            if lines[i].startswith("|") and re.match(r"^\|[\s:|-]+\|\s*$", lines[i + 1]):
                head_cols = lines[i].count("|")
                sep_cols = lines[i + 1].count("|")
                if head_cols != sep_cols:
                    problems.append(
                        f"{md.name}:{i + 1}: 表头 {head_cols - 1} 列但分隔行 {sep_cols - 1} 列"
                    )

    return problems


def check_readme_links(doc_dir: Path) -> list[str]:
    """README 里指向本目录文件的链接必须可达。上一轮 12 条全是死链。"""
    problems: list[str] = []
    readme = doc_dir / "README.md"
    if not readme.exists():
        return ["README.md 不存在"]
    for target in re.findall(r"\]\(([^)]+)\)", readme.read_text(encoding="utf-8")):
        if target.startswith(("http://", "https://", "#")):
            continue
        if not (doc_dir / target.split("#")[0]).exists():
            problems.append(f"README.md: 死链 -> {target}")
    return problems


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--ue", help="引擎根目录（含 Engine/ 的那一层）")
    ap.add_argument("--paths-only", action="store_true", help="跳过较慢的 CVar 扫描")
    ap.add_argument("--structure-only", action="store_true", help="只跑 markdown 结构 lint，不碰引擎源码")
    ap.add_argument("--cvar-cache", help="CVar 名索引的缓存文件（扫全量引擎源码要几分钟，换引擎版本时删掉）")
    ap.add_argument("--symbol-cache", help="标识符索引的缓存文件，同上")
    ap.add_argument("--json", help="把完整结果写到指定 JSON 文件")
    args = ap.parse_args()

    struct_problems = check_structure(DOC_DIR) + check_readme_links(DOC_DIR)
    print("=" * 72)
    print(f"结构 lint：{'通过' if not struct_problems else f'{len(struct_problems)} 个问题'}")
    print("=" * 72)
    for p in struct_problems:
        print(f"  {p}")
    print()

    if args.structure_only:
        print("通过——结构无问题" if not struct_problems else f"失败——{len(struct_problems)} 个结构问题")
        return 0 if not struct_problems else 1

    ue_root = resolve_ue_root(args.ue)
    version_file = ue_root / "Engine" / "Build" / "Build.version"
    version = "未知"
    if version_file.exists():
        v = json.loads(version_file.read_text(encoding="utf-8"))
        version = f"{v.get('MajorVersion')}.{v.get('MinorVersion')}.{v.get('PatchVersion')}"

    print(f"引擎根     : {ue_root}")
    print(f"引擎版本   : {version}")
    print(f"文档目录   : {DOC_DIR}\n")

    paths, cvars, symbols = collect_assertions(DOC_DIR)
    print("正在建立引擎源码索引…")
    index = build_source_index(ue_root)
    print(f"  已索引 {sum(len(v) for v in index.values())} 个源码文件\n")

    buckets: dict[str, list[tuple[str, list[str], set[str]]]] = collections.defaultdict(list)
    for path in sorted(paths):
        verdict, suggestions = classify_path(path, ue_root, index)
        buckets[verdict].append((path, suggestions, paths[path]))

    print("=" * 72)
    print(f"路径断言：共 {len(paths)} 条")
    print(f"  OK      规范且存在      : {len(buckets['OK'])}")
    print(f"  FIX     存在但写法不规范: {len(buckets['FIX'])}")
    print(f"  MISSING 引擎里找不到    : {len(buckets['MISSING'])}")
    print("=" * 72)

    if buckets["MISSING"]:
        print("\n--- MISSING（需删除或改正）---")
        for path, _, files in buckets["MISSING"]:
            print(f"  {path}\n      出现于: {', '.join(sorted(files))}")

    if buckets["FIX"]:
        print("\n--- FIX（改成规范写法）---")
        for path, suggestions, files in buckets["FIX"]:
            hint = suggestions[0] if len(suggestions) == 1 else f"{len(suggestions)} 个候选: {suggestions[:3]}"
            print(f"  {path}\n      -> {hint}\n      出现于: {', '.join(sorted(files))}")

    allow_file = Path(__file__).with_name("verify-ue-rendering-allow.txt")
    allowed: set[str] = set()
    if allow_file.exists():
        for line in allow_file.read_text(encoding="utf-8").splitlines():
            token = line.split("#", 1)[0].strip()
            if token:
                allowed.add(token)

    cvar_missing: list[tuple[str, set[str]]] = []
    if not args.paths_only:
        print("\n正在扫描引擎源码里的 CVar 字面量（较慢）…")
        known = build_cvar_index(ue_root, Path(args.cvar_cache) if args.cvar_cache else None)
        print(f"  已收集 {len(known)} 个点分名字面量\n")
        if allowed:
            print(f"  允许清单放行 {len(allowed)} 个名字（见 {allow_file.name}）")
        for name in sorted(cvars):
            if name not in known and name not in allowed:
                cvar_missing.append((name, cvars[name]))
        print("=" * 72)
        print(f"CVar 断言：共 {len(cvars)} 条")
        print(f"  存在  : {len(cvars) - len(cvar_missing)}")
        print(f"  找不到: {len(cvar_missing)}")
        print("=" * 72)
        if cvar_missing:
            print("\n--- CVar 在引擎源码里找不到 ---")
            for name, files in cvar_missing:
                print(f"  {name}\n      出现于: {', '.join(sorted(files))}")

    sym_missing: list[tuple[str, set[str]]] = []
    if not args.paths_only:
        print("\n正在扫描引擎源码里的标识符（较慢）…")
        known_syms = build_symbol_index(
            ue_root, Path(args.symbol_cache) if args.symbol_cache else None)
        for name in sorted(symbols):
            bare = name.split("::")[0]
            if name not in known_syms and bare not in known_syms and name not in allowed:
                sym_missing.append((name, symbols[name]))
        print("=" * 72)
        print(f"符号断言：共 {len(symbols)} 条")
        print(f"  存在  : {len(symbols) - len(sym_missing)}")
        print(f"  找不到: {len(sym_missing)}")
        print("=" * 72)
        if sym_missing:
            print("\n--- 符号在引擎源码里找不到 ---")
            for name, files in sym_missing:
                print(f"  {name}\n      出现于: {', '.join(sorted(files))}")

    if args.json:
        payload = {
            "ue_root": str(ue_root),
            "ue_version": version,
            "paths": {
                verdict: [
                    {"path": p, "suggestions": s, "docs": sorted(f)}
                    for p, s, f in items
                ]
                for verdict, items in buckets.items()
            },
            "cvars_missing": [{"name": n, "docs": sorted(f)} for n, f in cvar_missing],
            "symbols_missing": [{"name": n, "docs": sorted(f)} for n, f in sym_missing],
        }
        Path(args.json).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"\n完整结果已写入 {args.json}")

    failures = len(buckets["MISSING"]) + len(cvar_missing) + len(sym_missing)
    print(f"\n{'通过——无 MISSING' if failures == 0 else f'失败——{failures} 条断言无法在引擎源码中证实'}")
    return 0 if failures == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
