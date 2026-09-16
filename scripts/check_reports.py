"""Structural check for the cross-linked report format.

Run: python3 scripts/check_reports.py [source/2026-09-16.md ...]
Exits non-zero and names the file if anything fails, so a bad report is never
published. Reports without a `developments` list are skipped, not failed.
"""
import pathlib
import re
import sys

import yaml

ROOT = pathlib.Path(__file__).resolve().parent.parent
ANCHOR_PATTERNS = (
    r"^###\s+{gid}\s*·",           # GELİŞMELER heading
    r"^-\s+\*\*{gid}\s*·",         # RAKİP / İZLEME item
)


def check(path):
    text = path.read_text(encoding="utf-8")
    problems = []
    try:
        _, fm, body = text.split("---", 2)
        meta = yaml.safe_load(fm) or {}
    except Exception as exc:
        return [f"front matter parse failed: {exc}"]

    developments = meta.get("developments")
    if not developments:
        return []
    if not isinstance(developments, list):
        return ["developments is not a list"]

    for dev in developments:
        gid = str(dev.get("id", "")).strip()
        if not gid:
            problems.append("a development has no id")
            continue
        hits = sum(
            len(re.findall(p.format(gid=re.escape(gid)), body, re.M))
            for p in ANCHOR_PATTERNS
        )
        if hits != 1:
            problems.append(f"{gid}: expected exactly one anchor in the body, found {hits}")

    sources = set(re.findall(r"^-\s+\[K(\d+)\]", body, re.M))
    for cited in set(re.findall(r"\[K(\d+)\]", body)):
        if cited not in sources:
            problems.append(f"[K{cited}] cited but missing from KAYNAKLAR")

    return problems


def main(argv):
    paths = [pathlib.Path(a) for a in argv] or sorted((ROOT / "source").glob("*.md"))
    failed = False
    for path in paths:
        problems = check(path)
        status = "ok" if not problems else "FAIL"
        print(f"{path.name}: {status}")
        for p in problems:
            print(f"    - {p}")
            failed = True
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
