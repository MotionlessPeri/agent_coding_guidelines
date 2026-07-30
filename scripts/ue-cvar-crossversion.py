#!/usr/bin/env python3
"""比对知识库里引用的 CVar 在多个引擎版本中的存在情况，产出版本适用性表。

为什么需要：做技术支持时客户常在旧版本上，而 CVar 名跨版本改动频繁。手写「这条在 5.3
成不成立」只能靠猜；本机有几个版本的源码时，这件事可以机械判定。

用法：
    python scripts/ue-cvar-crossversion.py --ue "H:/Epic Games/UE_5.8" \
        --ue "C:/Program Files/Epic Games/UE_5.7" --ue "D:/UnrealEngine" \
        --cache-dir <缓存目录> --md <输出的 markdown 表>

每个引擎的 CVar 索引会缓存，第二次跑就快。
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

DOC_DIR = Path(__file__).resolve().parent.parent / "references" / "ue-rendering"
SKIP_DIRS = {"Binaries", "Intermediate", "DerivedDataCache", "Saved", "Content", ".git"}
CVAR_LITERAL_RE = re.compile(r'TEXT\(\s*"([A-Za-z][A-Za-z0-9_.]*\.[A-Za-z0-9_.]+)"')
CVAR_RE = re.compile(
    r"`((?:r|D3D12|vk|vr|sg|fx|au|p|net|Slate|Nanite|Lumen|renderdoc|xr)"
    r"\.[A-Za-z0-9_.]*[A-Za-z0-9_])`(?<!\.cpp`)(?<!\.h`)(?<!\.inl`)(?<!\.ush`)(?<!\.usf`)(?<!\.cs`)"
)
IGNORE_RE = re.compile(
    r"<!--\s*verify:ignore-start\s*-->.*?<!--\s*verify:ignore-end\s*-->", re.S)


def version_of(root: Path) -> str:
    f = root / "Engine" / "Build" / "Build.version"
    if not f.exists():
        return root.name
    v = json.loads(f.read_text(encoding="utf-8"))
    return f"{v.get('MajorVersion')}.{v.get('MinorVersion')}.{v.get('PatchVersion')}"


def cvar_index(root: Path, cache_dir: Path | None) -> set[str]:
    cache = None
    if cache_dir:
        cache_dir.mkdir(parents=True, exist_ok=True)
        cache = cache_dir / f"cvars-{version_of(root)}.json"
        if cache.exists():
            data = json.loads(cache.read_text(encoding="utf-8"))
            if data.get("root") == str(root):
                print(f"  {version_of(root)}: 复用缓存（{len(data['names'])} 个）")
                return set(data["names"])
    names: set[str] = set()
    for dirpath, dirs, files in os.walk(root / "Engine"):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for fn in files:
            if not fn.endswith((".h", ".cpp", ".inl")):
                continue
            try:
                names.update(CVAR_LITERAL_RE.findall(
                    Path(dirpath, fn).read_text(encoding="utf-8", errors="ignore")))
            except OSError:
                pass
    print(f"  {version_of(root)}: 扫出 {len(names)} 个")
    if cache:
        cache.write_text(json.dumps({"root": str(root), "names": sorted(names)},
                                    ensure_ascii=False), encoding="utf-8")
    return names


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--ue", action="append", required=True, help="引擎根，可给多个（第一个作基准）")
    ap.add_argument("--cache-dir", help="索引缓存目录")
    ap.add_argument("--md", help="把结果写成 markdown 表")
    args = ap.parse_args()

    roots = [Path(u) for u in args.ue]
    for r in roots:
        if not (r / "Engine").is_dir():
            sys.exit(f"不是引擎根: {r}")

    print("正在建各版本的 CVar 索引…")
    cache_dir = Path(args.cache_dir) if args.cache_dir else None
    idx = {version_of(r): cvar_index(r, cache_dir) for r in roots}
    versions = list(idx)

    used: dict[str, set[str]] = {}
    for md in sorted(DOC_DIR.glob("*.md")):
        text = IGNORE_RE.sub("", md.read_text(encoding="utf-8"))
        for n in CVAR_RE.findall(text):
            used.setdefault(n, set()).add(md.name)

    base = versions[0]
    rows = []
    for name in sorted(used):
        presence = {v: (name in idx[v]) for v in versions}
        if not presence[base]:
            continue  # 基准版本没有的不在这里报，交给 verify 脚本
        if all(presence.values()):
            continue  # 全版本都有的最稳，不占表
        rows.append((name, presence, sorted(used[name])))

    print(f"\n知识库引用的 CVar 共 {len(used)} 条（{base} 中存在的）")
    print(f"其中在旧版本缺失的：{len(rows)} 条\n")
    header = "| CVar | " + " | ".join(versions) + " | 出现于 |"
    sep = "|---" * (len(versions) + 2) + "|"
    lines = [header, sep]
    for name, presence, docs in rows:
        marks = " | ".join("✓" if presence[v] else "✗" for v in versions)
        lines.append(f"| `{name}` | {marks} | {', '.join(d.replace('.md', '') for d in docs)} |")
    out = "\n".join(lines)
    print(out)
    if args.md:
        Path(args.md).write_text(out + "\n", encoding="utf-8")
        print(f"\n已写入 {args.md}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
