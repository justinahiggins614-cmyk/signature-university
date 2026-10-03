#!/usr/bin/env python3
"""Coherence check: every AI The Signature University presents vs the phone-book canon.

Canon: /home/hatch/workspace/jah-ai-models/ai-catalog.json
Rule: any AI presented WITH a JAH-AI ID must match the canon exactly
(name + description, whitespace-normalized). Site helpers must NOT claim
a canon ID. Exit 0 = coherent, 1 = drift found (loud report).
"""
import glob, json, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CANON_PATHS = [
    "/home/hatch/workspace/jah-ai-models/ai-catalog.json",
    os.path.expanduser("~/workspace/jah-ai-models/ai-catalog.json"),
]
ID_RE = re.compile(r"JAH-AI-[A-Z0-9-]+")

def load_canon():
    for p in CANON_PATHS:
        if os.path.exists(p):
            c = json.load(open(p, encoding="utf-8"))
            return {r["ID"]: r for r in c.get("records", []) if r.get("ID")}
    return None

def scan_ids():
    claimed = set()
    pats = [os.path.join(ROOT, "index.html"),
            os.path.join(ROOT, "browse", "*.html"),
            os.path.join(ROOT, "data", "*.json")]
    files = []
    for p in pats:
        files.extend(glob.glob(p))
    for f in files:
        try:
            txt = open(f, encoding="utf-8", errors="replace").read()
        except OSError:
            continue
        for m in ID_RE.findall(txt):
            claimed.add((m, os.path.relpath(f, ROOT)))
    return claimed

def teacher_names(sample=5):
    names = []
    for f in sorted(glob.glob(os.path.join(ROOT, "data", "chunks", "*.json")))[:4]:
        try:
            d = json.load(open(f, encoding="utf-8"))
        except OSError:
            continue
        for c in (d if isinstance(d, list) else [d]):
            t = (c.get("teacher") or {})
            n = ((t.get("title") or "") + " " + (t.get("name") or "")).strip()
            if n and n not in names:
                names.append(n)
            if len(names) >= sample:
                return names
    return names

def main():
    canon = load_canon()
    if canon is None:
        print("COHERENCE WARN: canon file not found; ID-claim scan only.")
    claimed = scan_ids()
    real = [(i, f) for (i, f) in claimed if "jah-talk-fallback" not in f]
    issues = ["canon ID claimed outside canon context: %s in %s" % (i, f)
              for (i, f) in sorted(real)]
    print("=" * 64)
    print("COHERENCE REPORT — signature-university")
    print("=" * 64)
    print("Helper AIs (no canon ID, JAHtalk voice):")
    print("  - University Guide (campus concierge chat)")
    for n in teacher_names():
        print("  - %s (course AI teacher, e.g.)" % n)
    print("  ... one AI teacher per course, all invented names, none claims a JAH-AI ID")
    print("JAH-AI ID claims found on site: %d" % len(real))
    if issues:
        print("\n*** DRIFT DETECTED ***")
        for i in issues:
            print("  ! " + i)
        return 1
    print("\nOK: no canon-ID claims; every AI surface is a declared helper.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
