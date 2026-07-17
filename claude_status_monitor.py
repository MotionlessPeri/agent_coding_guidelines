#!/usr/bin/env python
"""Live cache/token status monitor for a Claude Code session.

Tails the session transcript JSONL that Claude Code writes (shared by the CLI and
the VS Code extension) and prints per-turn cache/token stats as they arrive.

  cache hit   = cache_read_input_tokens      (context reused from the cache)
  cache miss  = cache_creation_input_tokens  (context written to the cache)
  new input   = input_tokens                 (fresh, uncached input)

By default it follows the *newest* transcript under the project that matches the
current working directory, and re-checks for a newer session each poll, so if you
start a fresh chat in the extension it hops to it automatically.

WARNING: the JSONL entry format is internal to Claude Code and may change between
releases. If the columns go blank after an update, the schema moved.

Usage:
  python claude_status_monitor.py                 # follow newest session for CWD
  python claude_status_monitor.py --session <id>  # pin one session id
  python claude_status_monitor.py --project <dir> # a different project path
  python claude_status_monitor.py --all           # newest session across all projects
  python claude_status_monitor.py --once          # print current totals and exit
"""
import argparse
import json
import os
import re
import sys
import time

PROJECTS_ROOT = os.path.join(os.path.expanduser("~"), ".claude", "projects")


def encode_project(path):
    """Claude Code encodes a project dir by replacing each non-alphanumeric char
    with '-'.  e:\\GitRepository\\MoCapApp\\dev -> e--GitRepository-MoCapApp-dev"""
    return re.sub(r"[^A-Za-z0-9]", "-", os.path.abspath(path))


def project_dir(args):
    if args.all:
        return None  # search everything
    base = args.project if args.project else os.getcwd()
    d = os.path.join(PROJECTS_ROOT, encode_project(base))
    return d if os.path.isdir(d) else None


def newest_transcript(pdir):
    """Newest .jsonl under pdir, or across all project dirs when pdir is None."""
    roots = [pdir] if pdir else [
        os.path.join(PROJECTS_ROOT, e) for e in os.listdir(PROJECTS_ROOT)
    ] if os.path.isdir(PROJECTS_ROOT) else []
    best, best_mtime = None, -1.0
    for r in roots:
        if not r or not os.path.isdir(r):
            continue
        for name in os.listdir(r):
            if not name.endswith(".jsonl"):
                continue
            fp = os.path.join(r, name)
            try:
                m = os.path.getmtime(fp)
            except OSError:
                continue
            if m > best_mtime:
                best, best_mtime = fp, m
    return best


def resolve_target(args):
    if args.session:
        pdir = project_dir(args)
        roots = [pdir] if pdir else (
            [os.path.join(PROJECTS_ROOT, e) for e in os.listdir(PROJECTS_ROOT)]
            if os.path.isdir(PROJECTS_ROOT) else []
        )
        for r in roots:
            fp = os.path.join(r or "", args.session + ".jsonl")
            if os.path.isfile(fp):
                return fp
        return None
    return newest_transcript(project_dir(args))


def extract_usage(line):
    """Return (usage_dict, timestamp, model) for an assistant turn, else None."""
    try:
        o = json.loads(line)
    except (ValueError, TypeError):
        return None
    if o.get("type") != "assistant":
        return None
    msg = o.get("message") or {}
    u = msg.get("usage")
    if not isinstance(u, dict):
        return None
    return u, o.get("timestamp", ""), msg.get("model", "")


def fmt_row(usage, ts, model):
    hit = usage.get("cache_read_input_tokens", 0) or 0
    miss = usage.get("cache_creation_input_tokens", 0) or 0
    new = usage.get("input_tokens", 0) or 0
    out = usage.get("output_tokens", 0) or 0
    total_in = hit + miss + new
    rate = (100.0 * hit / total_in) if total_in else 0.0
    clock = ts[11:19] if len(ts) >= 19 else ts  # HH:MM:SS from ISO stamp
    short_model = (model or "").replace("claude-", "")
    return ("{clock}  hit {hit:>7}  miss {miss:>6}  new {new:>6}  "
            "out {out:>6}  hit% {rate:5.1f}  {model}").format(
        clock=clock, hit=hit, miss=miss, new=new, out=out, rate=rate,
        model=short_model)


HEADER = ("TIME       CACHE-HIT      CACHE-MISS   NEW-IN    OUT     HIT%   MODEL")


def read_new_rows(fp, offset):
    """Read from byte offset to EOF; yield parsed usage rows; return new offset."""
    rows = []
    with open(fp, "rb") as f:
        f.seek(offset)
        data = f.read()
        offset = f.tell()
    for raw in data.splitlines():
        if not raw.strip():
            continue
        r = extract_usage(raw.decode("utf-8", "replace"))
        if r:
            rows.append(r)
    return rows, offset


def run_once(fp):
    rows, _ = read_new_rows(fp, 0)
    print(HEADER)
    for usage, ts, model in rows:
        print(fmt_row(usage, ts, model))


def follow(args):
    current = None
    offset = 0
    printed_header = False
    print("Monitoring Claude Code session status.  Ctrl+C to stop.\n")
    while True:
        target = resolve_target(args)
        if target is None:
            sys.stdout.write("\r(waiting for a session transcript...) ")
            sys.stdout.flush()
            time.sleep(args.interval)
            continue
        if target != current:
            # switched to a new (or newer) session file
            current = target
            offset = 0
            printed_header = False
            print("\n>> session: {}".format(os.path.basename(current)[:-6]))
        rows, offset = read_new_rows(current, offset)
        for usage, ts, model in rows:
            if not printed_header:
                print(HEADER)
                printed_header = True
            print(fmt_row(usage, ts, model))
        time.sleep(args.interval)


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--session", help="pin a specific session id (filename w/o .jsonl)")
    ap.add_argument("--project", help="project dir to resolve (default: CWD)")
    ap.add_argument("--all", action="store_true",
                    help="follow newest session across ALL projects")
    ap.add_argument("--once", action="store_true",
                    help="print the current session's turns and exit")
    ap.add_argument("--interval", type=float, default=0.5,
                    help="poll interval seconds (default 0.5)")
    args = ap.parse_args()

    # Line-buffer stdout so rows appear promptly even when piped/redirected.
    try:
        sys.stdout.reconfigure(line_buffering=True)
    except (AttributeError, ValueError):
        pass

    if args.once:
        target = resolve_target(args)
        if not target:
            print("No transcript found.", file=sys.stderr)
            sys.exit(1)
        print(">> session: {}".format(os.path.basename(target)[:-6]))
        run_once(target)
        return
    try:
        follow(args)
    except KeyboardInterrupt:
        print("\nstopped.")


if __name__ == "__main__":
    main()
