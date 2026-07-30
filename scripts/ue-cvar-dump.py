#!/usr/bin/env python3
"""从 UE 引擎源码里抽出 CVar 的真实名称、默认值、帮助文本和声明位置。

为什么需要它：手写或调研生成的 CVar 表里有大量「读起来完全合理但并不存在」的名字
（实测某批渲染文档 431 条 CVar 断言里 163 条在 5.8 中不存在）。与其逐条核对再修，
不如直接从源码生成——生成出来的表天然正确，且带引擎自己写的帮助文本。

跟 `verify-ue-rendering-refs.py` 的分工：那个**校验**文档里已有的断言，这个**生成**
可信内容。前者是 gate，后者是产线。

用法：
    python scripts/ue-cvar-dump.py r.Nanite                    # 按前缀列出
    python scripts/ue-cvar-dump.py r.Lumen.Reflections --md    # 输出 markdown 表
    python scripts/ue-cvar-dump.py r.RDG --md --with-source    # 表里带声明位置
    python scripts/ue-cvar-dump.py --check r.VisualizeBuffer   # 只判断某个名字存不存在
    python scripts/ue-cvar-dump.py r.Nanite --json out.json    # 结构化输出

引擎根用 --ue 或环境变量 UE_ROOT 指定。首次扫描要几分钟，结果落盘缓存。
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

UE_ROOT_CANDIDATES = [
    r"H:/Epic Games/UE_5.8",
    r"C:/Program Files/Epic Games/UE_5.8",
    r"C:/Program Files/Epic Games/UE_5.7",
]

SKIP_DIRS = {"Binaries", "Intermediate", "DerivedDataCache", "Saved", "Content", ".git"}

# CVar 声明的起始标记。变体很多，统一按「标记 → 第一个 TEXT("名字") → 后续 TEXT 拼成帮助」解析。
DECL_START = re.compile(
    r"\b(?:TAutoConsoleVariable\s*<|FAutoConsoleVariableRef|FAutoConsoleVariable\b"
    r"|IConsoleManager::Get\(\)\.Register(?:Console)?Variable|FAutoConsoleCommand)"
)
TEXT_LIT = re.compile(r'TEXT\(\s*"((?:[^"\\]|\\.)*)"\s*\)')


def resolve_ue_root(explicit: str | None) -> Path:
    for cand in filter(None, [explicit, os.environ.get("UE_ROOT"), *UE_ROOT_CANDIDATES]):
        p = Path(cand)
        if (p / "Engine").is_dir():
            return p
    sys.exit("找不到引擎根目录。用 --ue <路径> 或设 UE_ROOT。")


def parse_file(path: Path, rel: str) -> list[dict]:
    """从一个源码文件里解析出所有 CVar 声明。"""
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return []
    if "TEXT(\"" not in text:
        return []

    out: list[dict] = []
    for m in DECL_START.finditer(text):
        # 声明语句到配平的 `);` 为止；给个上限避免正则跑飞
        chunk = text[m.start(): m.start() + 4000]
        end = chunk.find(");")
        if end == -1:
            continue
        chunk = chunk[: end + 2]

        lits = TEXT_LIT.findall(chunk)
        if not lits:
            continue
        name = lits[0]
        # CVar 名的形态：点分、无空格。过滤掉把普通字符串当首个 TEXT 的情况
        if " " in name or "." not in name or len(name) > 90:
            continue

        help_text = " ".join(lits[1:]).replace("\\n", " ").strip()
        help_text = re.sub(r"\s+", " ", help_text)

        # 默认值：名字之后、帮助文本之前的那个 token
        after_name = chunk[chunk.find(f'"{name}"') + len(name) + 2:]
        dm = re.match(r"\s*\)?\s*,\s*([^,\n]+?)\s*,", after_name)
        default = dm.group(1).strip() if dm else ""
        if default.startswith("TEXT("):
            default = ""

        line = text[: m.start()].count("\n") + 1
        out.append({
            "name": name,
            "default": default,
            "help": help_text,
            "source": f"{rel}:{line}",
        })
    return out


def build_db(ue_root: Path, cache: Path | None) -> list[dict]:
    if cache and cache.exists():
        data = json.loads(cache.read_text(encoding="utf-8"))
        if data.get("ue_root") == str(ue_root):
            return data["cvars"]

    entries: list[dict] = []
    for root, dirs, files in os.walk(ue_root / "Engine"):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        rel_root = os.path.relpath(root, ue_root).replace("\\", "/")
        for fn in files:
            if fn.endswith((".cpp", ".inl")):
                entries.extend(parse_file(Path(root, fn), f"{rel_root}/{fn}"))

    # 同名多处声明（平台分支等）只留第一处，但优先留有帮助文本的
    best: dict[str, dict] = {}
    for e in entries:
        cur = best.get(e["name"])
        if cur is None or (not cur["help"] and e["help"]):
            best[e["name"]] = e
    result = sorted(best.values(), key=lambda x: x["name"])

    if cache:
        cache.write_text(
            json.dumps({"ue_root": str(ue_root), "cvars": result}, ensure_ascii=False),
            encoding="utf-8",
        )
    return result


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("prefix", nargs="*", help="CVar 名前缀，可给多个")
    ap.add_argument("--ue", help="引擎根目录")
    ap.add_argument("--cache", default=None, help="解析结果缓存文件")
    ap.add_argument("--md", action="store_true", help="输出 markdown 表")
    ap.add_argument("--with-source", action="store_true", help="markdown 表里带声明位置")
    ap.add_argument("--check", nargs="+", metavar="NAME", help="只判断这些名字是否存在")
    ap.add_argument("--json", help="结构化结果写到文件")
    args = ap.parse_args()

    ue_root = resolve_ue_root(args.ue)
    db = build_db(ue_root, Path(args.cache) if args.cache else None)
    index = {e["name"]: e for e in db}

    if args.check:
        for name in args.check:
            e = index.get(name)
            if e:
                print(f"  ✓ {name}\n      {e['source']}\n      {e['help'][:120]}")
            else:
                near = [n for n in index if name.rsplit(".", 1)[-1].lower() in n.lower()][:5]
                print(f"  ✗ {name}  不存在" + (f"\n      近亲: {near}" if near else ""))
        return 0

    if not args.prefix:
        print(f"引擎 {ue_root} 共解析出 {len(db)} 个 CVar。给一个前缀来筛选。")
        return 0

    hits = [e for e in db if any(e["name"].startswith(p) for p in args.prefix)]
    print(f"# {' / '.join(args.prefix)} —— {len(hits)} 个（引擎 {ue_root.name}）\n")

    if args.md:
        cols = "| CVar | 默认 | 作用 |" + (" 声明位置 |" if args.with_source else "")
        sep = "|---|---|---|" + ("---|" if args.with_source else "")
        print(cols)
        print(sep)
        for e in hits:
            help_ = e["help"].replace("|", "\\|") or "—"
            row = f"| `{e['name']}` | {e['default'] or '—'} | {help_} |"
            if args.with_source:
                row += f" `{e['source']}` |"
            print(row)
    else:
        for e in hits:
            print(f"{e['name']}\n    默认: {e['default'] or '—'}\n    {e['help'][:160]}\n    {e['source']}")

    if args.json:
        Path(args.json).write_text(json.dumps(hits, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"\n已写入 {args.json}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
