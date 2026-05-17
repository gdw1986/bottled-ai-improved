#!/usr/bin/env python3
"""统计 run_history.log 中的胜率，按 commit 分组。"""

import re
import sys
from collections import defaultdict

LOG_FILE = "logs/run_history.log"


def parse_line(line: str) -> dict | None:
    """从一行日志中提取 commit, strategy, floor, win。"""
    m = re.search(r'Commit:([^,\s]+)', line)
    commit = m.group(1) if m else "unknown"

    m = re.search(r'Strat:\s*(\w+)', line)
    strat = m.group(1) if m else None

    m = re.search(r'Floor:(\d+)', line)
    floor = int(m.group(1)) if m else None

    m = re.search(r'DiedTo:\s*(.*?),\s*Bosses:', line)
    died_to = m.group(1).strip() if m else None

    if strat is None or floor is None:
        return None

    return {
        "commit": commit,
        "strat": strat,
        "floor": floor,
        "died_to": died_to,
        "win": died_to == "N/A",
    }


def main():
    try:
        lines = open(LOG_FILE, encoding="utf-8").readlines()
    except FileNotFoundError:
        print(f"文件不存在: {LOG_FILE}")
        sys.exit(1)

    records = [r for line in lines if (r := parse_line(line.strip()))]

    if not records:
        print("未找到有效记录")
        return

    # 按 commit 统计
    by_commit: dict[str, dict] = defaultdict(lambda: {"wins": 0, "total": 0, "strats": defaultdict(lambda: {"wins": 0, "total": 0})})

    for r in records:
        c = r["commit"]
        s = r["strat"]
        by_commit[c]["total"] += 1
        by_commit[c]["strats"][s]["total"] += 1
        if r["win"]:
            by_commit[c]["wins"] += 1
            by_commit[c]["strats"][s]["wins"] += 1

    print(f"\n{'='*60}")
    print(f"  统计来源: {LOG_FILE}  |  共 {len(records)} 局")
    print(f"{'='*60}\n")

    # 按 commit 总胜率排序（胜率高的在前）
    for commit, data in sorted(by_commit.items(), key=lambda x: x[1]["wins"] / max(x[1]["total"], 1), reverse=True):
        wr = data["wins"] / data["total"] * 100
        print(f"  [{commit}]  {data['wins']:>2}胜 / {data['total']}局  =  {wr:5.1f}%  (总)")
        for strat, sd in sorted(data["strats"].items()):
            swr = sd["wins"] / sd["total"] * 100 if sd["total"] > 0 else 0
            print(f"    └── {strat:<22} {sd['wins']:>2}胜 / {sd['total']}局 = {swr:5.1f}%")
        print()

    # 聚焦 PEACEFUL_PUMMELING 的跨 commit 对比
    pp = {c: d["strats"]["PEACEFUL_PUMMELING"] for c, d in by_commit.items() if "PEACEFUL_PUMMELING" in d["strats"]}
    if len(pp) > 1:
        print(f"{'='*60}")
        print("  PEACEFUL_PUMMELING 跨版本对比")
        print(f"{'='*60}")
        for commit, sd in sorted(pp.items(), key=lambda x: x[1]["wins"] / max(x[1]["total"], 1), reverse=True):
            swr = sd["wins"] / sd["total"] * 100 if sd["total"] > 0 else 0
            bar = "█" * sd["wins"] + "░" * (sd["total"] - sd["wins"])
            print(f"  [{commit}]  {bar}  {sd['wins']}/{sd['total']}  ({swr:.0f}%)")
        print()


if __name__ == "__main__":
    main()
