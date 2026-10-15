#!/usr/bin/env python3
"""kb.py: 语料库维护工具，零依赖（Python 3.10+）。在仓库根运行。

  python scripts/kb/kb.py lint              检查断链、frontmatter 字段、经验页与事故的双向引用、复测是否过期
  python scripts/kb/kb.py index             生成 evidence/INDEX.md 与 guidelines/CATALOG.md
  python scripts/kb/kb.py query 词 [词...]  按章节检索，返回命中的章节而不是整份文件（-n 条数，--full 全文）

lint 的退出码：有错误为 1，只有警告为 0。
"""
from __future__ import annotations

import argparse
import datetime as dt
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCAN = ["AGENTS.md", "README.md", "guidelines", "techniques", "skills", "references", "evidence"]
INCIDENT_DIR = ROOT / "evidence" / "incidents"
EVIDENCE_INDEX = ROOT / "evidence" / "INDEX.md"
CATALOG = ROOT / "guidelines" / "CATALOG.md"
KINDS = {"命中", "生效", "提议"}
CAUGHT = {"自查", "用户", "外部追问", "第三方复核", "实验", "事后复盘"}
CLASSES = {"knowledge", "norm", "experience", "procedure"}
RETEST_STALE_DAYS = 180

FM_RE = re.compile(r"\A---\n(.*?)\n---\n", re.S)
LINK_RE = re.compile(r"\]\(([^)\s]+)\)")
HEADING_RE = re.compile(r"^(#{1,6})\s+(.*\S)\s*$")
DATE_RE = re.compile(r"\d{4}-\d{2}-\d{2}")


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8").replace("\r\n", "\n")


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def md_files():
    for name in SCAN:
        p = ROOT / name
        if p.is_file():
            yield p
        elif p.is_dir():
            yield from sorted(p.rglob("*.md"))


def unquote(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
        return value[1:-1]
    return value


def split_inline_list(inner: str) -> list[str]:
    items, buf, quote = [], "", None
    for ch in inner:
        if quote:
            buf += ch
            if ch == quote:
                quote = None
        elif ch in "\"'":
            quote = ch
            buf += ch
        elif ch == ",":
            items.append(buf)
            buf = ""
        else:
            buf += ch
    items.append(buf)
    return [unquote(x) for x in items if x.strip()]


def parse_frontmatter(text: str):
    """返回 (字段字典或 None, 正文)。支持 key: value / key: [a, b] / 块列表 key:\\n  - a。"""
    m = FM_RE.match(text)
    if not m:
        return None, text
    data: dict[str, object] = {}
    key = None
    for line in m.group(1).split("\n"):
        if not line.strip():
            continue
        if line.startswith("  - ") and key is not None:
            cur = data.get(key)
            if not isinstance(cur, list):
                cur = [] if cur in ("", None, []) else [cur]
            cur.append(unquote(line[4:]))
            data[key] = cur
            continue
        if ":" not in line:
            continue
        k, v = line.split(":", 1)
        key, v = k.strip(), v.strip()
        if v.startswith("[") and v.endswith("]"):
            inner = v[1:-1].strip()
            data[key] = split_inline_list(inner) if inner else []
        elif v == "":
            data[key] = []
        else:
            data[key] = unquote(v)
    return data, text[m.end():]


def iter_sections(text: str):
    """按标题切章节，跳过围栏代码块里的 # 行。返回 (标题, 正文) 列表，首个标题前的内容标题为空。"""
    sections, heading, buf, fenced = [], "", [], False
    for line in text.split("\n"):
        if line.startswith("```"):
            fenced = not fenced
        hm = None if fenced else HEADING_RE.match(line)
        if hm:
            sections.append((heading, "\n".join(buf)))
            heading, buf = hm.group(2), []
        else:
            buf.append(line)
    sections.append((heading, "\n".join(buf)))
    return sections


def first_phenomenon(body: str) -> str:
    m = re.search(r"\*\*现象\*\*[:：]\s*(.+)", body)
    if not m:
        return ""
    s = m.group(1).strip()
    return s if len(s) <= 70 else s[:69] + "…"


def load_incidents():
    out = {}
    if not INCIDENT_DIR.is_dir():
        return out
    for p in sorted(INCIDENT_DIR.glob("*.md")):
        fm, body = parse_frontmatter(read(p))
        out[p.stem] = (p, fm, body)
    return out


def load_pages():
    """有 frontmatter 且带 class 的页面。"""
    out = {}
    for p in md_files():
        if p.is_relative_to(INCIDENT_DIR):
            continue
        fm, body = parse_frontmatter(read(p))
        if fm and "class" in fm:
            out[rel(p)] = (p, fm, body)
    return out


# ---------------------------------------------------------------- lint
def cmd_lint(_args) -> int:
    errors, warnings = [], []

    for p in md_files():
        text = read(p)
        fenced = False
        for ln, line in enumerate(text.split("\n"), 1):
            if line.startswith("```"):
                fenced = not fenced
            if fenced:
                continue
            # 行内代码里的 `[$i](n/2)` 之类不是链接，先剥掉再找
            for target in LINK_RE.findall(re.sub(r"`[^`]*`", "", line)):
                if target.startswith(("http://", "https://", "mailto:", "#")):
                    continue
                target = target.split("#", 1)[0]
                if not target:
                    continue
                if not (p.parent / target).exists():
                    errors.append(f"{rel(p)}:{ln}: 断链 {target}")

    incidents = load_incidents()
    pages = load_pages()
    today = dt.date.today()

    for page_rel, (p, fm, _body) in pages.items():
        cls = fm.get("class")
        if cls not in CLASSES:
            errors.append(f"{page_rel}: class 取值 {cls!r} 不在 {sorted(CLASSES)}")
        if cls != "experience":
            continue
        if not fm.get("triggers"):
            errors.append(f"{page_rel}: 经验页缺 triggers")
        if not fm.get("born"):
            errors.append(f"{page_rel}: 经验页缺 born")
        ids = fm.get("incidents") or []
        if not ids:
            errors.append(f"{page_rel}: 经验页没有任何事故记录")
        for iid in ids:
            if iid not in incidents:
                errors.append(f"{page_rel}: 事故 {iid} 不存在于 evidence/incidents/")
                continue
            inc_pages = incidents[iid][1].get("pages") or []
            if page_rel not in inc_pages:
                errors.append(f"{page_rel}: 事故 {iid} 的 pages 没有回指本页")
        retested = fm.get("retested") or []
        if not retested:
            warnings.append(f"{page_rel}: 未复测（retested 为空）")
        else:
            dates = DATE_RE.findall(" ".join(retested))
            if not dates:
                warnings.append(f"{page_rel}: retested 条目里没有日期")
            else:
                last = dt.date.fromisoformat(max(dates))
                if (today - last).days > RETEST_STALE_DAYS:
                    warnings.append(f"{page_rel}: 上次复测 {last}，超过 {RETEST_STALE_DAYS} 天")

    for iid, (p, fm, _body) in incidents.items():
        here = rel(p)
        if fm is None:
            errors.append(f"{here}: 缺 frontmatter")
            continue
        if fm.get("id") != iid:
            errors.append(f"{here}: id 与文件名不一致")
        if not re.fullmatch(r"\d{4}-\d{2}", str(fm.get("date", ""))):
            errors.append(f"{here}: date 应为 YYYY-MM")
        if fm.get("kind") not in KINDS:
            errors.append(f"{here}: kind 取值 {fm.get('kind')!r} 不在 {sorted(KINDS)}")
        if fm.get("caught_by") not in CAUGHT:
            errors.append(f"{here}: caught_by 取值 {fm.get('caught_by')!r} 不在 {sorted(CAUGHT)}")
        for key in ("model", "project"):
            if not fm.get(key):
                errors.append(f"{here}: 缺 {key}（不知道就写 unknown）")
        inc_pages = fm.get("pages") or []
        if not inc_pages:
            warnings.append(f"{here}: 没有页面引用（待归类）")
        for page_rel in inc_pages:
            if not (ROOT / page_rel).exists():
                errors.append(f"{here}: pages 里的 {page_rel} 不存在")
            elif page_rel in pages and iid not in (pages[page_rel][1].get("incidents") or []):
                errors.append(f"{here}: 页面 {page_rel} 的 incidents 没有列出本事故")

    for w in warnings:
        print("WARN ", w)
    for e in errors:
        print("ERROR", e)
    print(f"lint: 页面 {len(pages)}，事故 {len(incidents)}，错误 {len(errors)}，警告 {len(warnings)}")
    return 1 if errors else 0


# ---------------------------------------------------------------- index
def write_lf(path: Path, text: str) -> None:
    path.write_bytes(text.encode("utf-8"))
    print("written:", rel(path))


def cmd_index(_args) -> int:
    incidents = load_incidents()
    pages = load_pages()
    by_page: dict[str, list[str]] = {}
    orphans = []
    for iid, (_p, fm, _b) in incidents.items():
        targets = fm.get("pages") or []
        if not targets:
            orphans.append(iid)
        for t in targets:
            by_page.setdefault(t, []).append(iid)

    lines = ["# 事故索引（生成文件，勿手改）", "",
             "由 `python scripts/kb/kb.py index` 从 `evidence/incidents/` 生成。按引用页面分组；统计只是计数，不是规则的权重。", ""]
    for page_rel in sorted(by_page):
        ids = sorted(by_page[page_rel])
        lines += [f"## {page_rel}", "", f"引用本页的事故 {len(ids)} 条。", "",
                  "| 事故 | 时间 | 类型 | 发现方式 | 标签 | 现象 |", "|---|---|---|---|---|---|"]
        kinds, caught, tags = {}, {}, {}
        for iid in ids:
            _p, fm, body = incidents[iid]
            kinds[fm.get("kind")] = kinds.get(fm.get("kind"), 0) + 1
            caught[fm.get("caught_by")] = caught.get(fm.get("caught_by"), 0) + 1
            for t in fm.get("tags") or []:
                tags[t] = tags.get(t, 0) + 1
            lines.append(f"| [{iid}](incidents/{iid}.md) | {fm.get('date')} | {fm.get('kind')} | {fm.get('caught_by')} | "
                         f"{', '.join(fm.get('tags') or [])} | {first_phenomenon(body)} |")
        fmt = lambda d: "、".join(f"{k} {v}" for k, v in sorted(d.items(), key=lambda kv: (-kv[1], str(kv[0]))))
        lines += ["", f"- 类型：{fmt(kinds)}", f"- 发现方式：{fmt(caught)}", f"- 标签：{fmt(tags)}", ""]
    if orphans:
        lines += ["## 未归类", ""] + [f"- [{i}](incidents/{i}.md)" for i in orphans] + [""]
    write_lf(EVIDENCE_INDEX, "\n".join(lines))

    groups: dict[str, list[str]] = {}
    for page_rel, (_p, fm, _b) in sorted(pages.items()):
        groups.setdefault(str(fm.get("class")), []).append(page_rel)
    lines = ["# 页面目录（生成文件，勿手改）", "",
             "由 `python scripts/kb/kb.py index` 从各页面的 frontmatter 生成。只列出已标 `class` 的页面；未标的页面仍按 [INDEX.md](INDEX.md) 按任务查。", ""]
    for cls in sorted(groups):
        lines += [f"## {cls}", "", "| 页面 | 作用域 | 触发词 | 诞生 | 最近复测 | 事故数 |", "|---|---|---|---|---|---|"]
        for page_rel in groups[cls]:
            fm = pages[page_rel][1]
            retested = fm.get("retested") or []
            last = retested[-1] if retested else "未复测"
            link = Path(page_rel).relative_to("guidelines").as_posix() if page_rel.startswith("guidelines/") else f"../{page_rel}"
            lines.append(f"| [{page_rel}]({link}) | {fm.get('scope', '')} | {', '.join(fm.get('triggers') or [])} | "
                         f"{fm.get('born', '')} | {last} | {len(fm.get('incidents') or [])} |")
        lines.append("")
    write_lf(CATALOG, "\n".join(lines))
    return 0


# ---------------------------------------------------------------- query
def cmd_query(args) -> int:
    terms = [t.lower() for t in args.terms]
    boosts: dict[str, int] = {}
    for page_rel, (_p, fm, _b) in load_pages().items():
        for trig in fm.get("triggers") or []:
            tl = trig.lower()
            if any(t in tl or tl in t for t in terms):
                boosts[page_rel] = boosts.get(page_rel, 0) + 3
    hits = []
    for p in md_files():
        page_rel = rel(p)
        if page_rel in {rel(EVIDENCE_INDEX), rel(CATALOG)}:
            continue
        text = read(p)
        _fm, body = parse_frontmatter(text)
        for heading, sec in iter_sections(body):
            hl, sl = heading.lower(), sec.lower()
            score = sum(3 * hl.count(t) + sl.count(t) for t in terms)
            if score:
                hits.append((score + boosts.get(page_rel, 0), page_rel, heading, sec.strip()))
    hits.sort(key=lambda h: (-h[0], h[1]))
    if not hits:
        print("没有命中。换个说法，或看 guidelines/INDEX.md 按任务找。")
        return 0
    for score, page_rel, heading, sec in hits[: args.n]:
        print(f"== {page_rel} :: {heading or '(开头)'}  (score {score})")
        print(sec if args.full or len(sec) <= args.width else sec[: args.width].rstrip() + " …")
        print()
    return 0


def main(argv=None) -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("lint").set_defaults(fn=cmd_lint)
    sub.add_parser("index").set_defaults(fn=cmd_index)
    q = sub.add_parser("query")
    q.add_argument("terms", nargs="+")
    q.add_argument("-n", type=int, default=8)
    q.add_argument("--full", action="store_true")
    q.add_argument("--width", type=int, default=600)
    q.set_defaults(fn=cmd_query)
    args = ap.parse_args(argv)
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
