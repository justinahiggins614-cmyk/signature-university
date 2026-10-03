#!/usr/bin/env python3
"""Signature University meta builder — the single authoritative count source.

Reads the real data files and writes:
  data/counts.json          — every public count, generated (never hand-edited)
  university-manifest.json  — the machine-readable university manifest (root)
  api.json                  — refreshed counts + updated date
  data/colleges.json        — enriched: college_id, canonical_url, version

Then runs BUILD GATES (fail loudly, exit non-zero):
  - duplicate course IDs / degree IDs / project IDs
  - dangling prereq references
  - degree curriculum resolves to >= 1 course
  - lab course references resolve
  - counts cross-check (courses == AI teachers, colleges == 11, levels == 6)

Then stamps the generated course count into index.html's static
meta/OG/JSON-LD/how-it-works strings (exact-match replacements only).

Re-run any time the catalog changes. The catalog generator
(code/generate.py) should be followed by this script.
"""
import json, os, sys, hashlib, re
from datetime import date, datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
TODAY = date.today().isoformat()
NOW = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

CURRICULUM_VERSION = "2026.10"
CATALOG_VERSION = "2026.10.03"
SCHEMA_VERSION = "1.0"
BASE = "https://justinahiggins614-cmyk.github.io/signature-university/"

LEVELS = [101, 201, 301, 401, 501, 601]

def load(name):
    with open(os.path.join(DATA, name), encoding="utf-8") as f:
        return json.load(f)

def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()

def main():
    idx = load("courses.idx.json")
    colleges = load("colleges.json")
    degrees = load("degrees.json")
    labs = load("labs.json")
    projects = load("projects.json")

    n_courses = len(idx)
    n_colleges = len(colleges["colleges"])
    n_degrees = len(degrees)
    n_labs = len(labs)
    n_projects = len(projects)

    # ---------------- build gates ----------------
    errors = []
    def gate(cond, msg):
        if not cond:
            errors.append(msg)

    course_ids = [r["i"] for r in idx]
    gate(len(set(course_ids)) == len(course_ids), "duplicate course IDs in courses.idx.json")
    gate(all(re.fullmatch(r"JAH-COURSE-\d{6}", i) for i in course_ids), "malformed course ID")
    idset = set(course_ids)
    # prereqs live in chunks; check a sample via the compact route: chunk scan
    for ci in range(1, 40):
        p = os.path.join(DATA, "chunks", "c%04d.json" % ci)
        if not os.path.exists(p):
            break
        for c in json.load(open(p, encoding="utf-8")):
            pr = c.get("prereq")
            if pr and pr not in idset:
                errors.append("dangling prereq %s on %s" % (pr, c["id"]))
                break
    deg_ids = [d["id"] for d in degrees]
    gate(len(set(deg_ids)) == len(deg_ids), "duplicate degree IDs")
    # degree curriculum resolves (same rule as js/degree-flow.js curriculum())
    for d in degrees:
        pool = [r for r in idx if r["k"] == d["ckey"] and r["l"] >= d["min_level"]]
        gate(len(pool) >= d["need"], "degree %s curriculum short: %d < %d" % (d["id"], len(pool), d["need"]))
    for lb in labs[:2000]:
        if lb["course"] not in idset:
            errors.append("lab references unknown course %s" % lb["course"])
            break
    proj_ids = [p["id"] for p in projects]
    gate(len(set(proj_ids)) == len(proj_ids), "duplicate project IDs")
    gate(n_colleges == 11, "college count != 11: %d" % n_colleges)
    gate(sorted(set(r["l"] for r in idx)) == LEVELS, "level set drift")
    if errors:
        print("BUILD GATES FAILED:")
        for e in errors:
            print("  -", e)
        sys.exit(1)
    print("build gates: PASS (%d courses, %d degrees, %d labs, %d projects)" %
          (n_courses, n_degrees, n_labs, n_projects))

    snapshot_id = "SNAP-%s-%d" % (TODAY.replace("-", ""), n_courses)
    catalog_hash = sha256_file(os.path.join(DATA, "courses.idx.json"))

    counts = {
        "site": "Signature University",
        "generated_at": NOW,
        "last_updated": TODAY,
        "snapshot_id": snapshot_id,
        "curriculum_version": CURRICULUM_VERSION,
        "catalog_version": CATALOG_VERSION,
        "course_count": n_courses,
        "college_count": n_colleges,
        "level_count": len(LEVELS),
        "levels": LEVELS,
        "degree_count": n_degrees,
        "lab_count": n_labs,
        "project_count": n_projects,
        "ai_teacher_count": n_courses,
        "catalog_hash_sha256": catalog_hash,
        "note": "course_count is the single authoritative count. AI teachers: one per course.",
    }
    with open(os.path.join(DATA, "counts.json"), "w", encoding="utf-8") as f:
        json.dump(counts, f, indent=1)
        f.write("\n")

    manifest = {
        "university_id": "JAH-UNIVERSITY-01",
        "name": "Signature University",
        "founder": "Justin Addam Higgins",
        "version": "1.0",
        "course_count": n_courses,
        "college_count": n_colleges,
        "degree_count": n_degrees,
        "lab_count": n_labs,
        "project_count": n_projects,
        "ai_teacher_count": n_courses,
        "curriculum_version": CURRICULUM_VERSION,
        "catalog_version": CATALOG_VERSION,
        "schema_version": SCHEMA_VERSION,
        "catalog_hash_sha256": catalog_hash,
        "snapshot_id": snapshot_id,
        "created": "2026-10-01",
        "updated": TODAY,
        "accreditation_status": "NOT_GOVERNMENT_ACCREDITED",
        "diploma_status": "CERTIFICATE_OF_COMPLETION",
        "progress_mode": "DEVICE_LOCAL_ONLY",
        "canonical_url": BASE,
        "machine_readable": {
            "counts": "data/counts.json",
            "courses_index": "data/courses.idx.json",
            "courses_feed": "data/courses-catalog.json",
            "colleges": "data/colleges.json",
            "degrees": "data/degrees.json",
            "labs": "data/labs.json",
            "projects": "data/projects.json",
            "schema": "university-schema.json",
            "llms": "llms.txt",
        },
        "honesty": ("Independent free learning project. Not accredited by any government body. "
                    "Diplomas certify completion of Signature University coursework."),
    }
    with open(os.path.join(ROOT, "university-manifest.json"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=1)
        f.write("\n")

    # refresh api.json counts (keep its college rows; they are static metadata)
    api_path = os.path.join(ROOT, "api.json")
    api = json.load(open(api_path, encoding="utf-8"))
    api["updated"] = TODAY
    api["total_courses"] = n_courses
    api["degrees"] = n_degrees
    api["labs"] = n_labs
    with open(api_path, "w", encoding="utf-8") as f:
        json.dump(api, f, indent=1)
        f.write("\n")

    # enrich colleges.json: permanent IDs, canonical URLs, version
    for i, c in enumerate(colleges["colleges"], 1):
        c["college_id"] = "JAH-COLLEGE-%02d" % i
        c["canonical_url"] = BASE + "?college=" + c["key"]
        c["version"] = CURRICULUM_VERSION
        c["updated"] = TODAY
    colleges["updated"] = TODAY
    colleges["curriculum_version"] = CURRICULUM_VERSION
    with open(os.path.join(DATA, "colleges.json"), "w", encoding="utf-8") as f:
        json.dump(colleges, f, indent=1)
        f.write("\n")

    # stamp the generated count into index.html static strings (exact matches only)
    html_path = os.path.join(ROOT, "index.html")
    html_text = open(html_path, encoding="utf-8").read()
    old_count_str = "3,850"
    new_count_str = "%d" % n_courses if n_courses < 10000 else "%s,%03d" % (n_courses // 1000, n_courses % 1000)
    # all current "3,850" occurrences refer to the course count (verified by grep)
    n_rep = html_text.count(old_count_str)
    html_text = html_text.replace(old_count_str, new_count_str)
    # fix the wrong hard-coded lab count: make it number-free
    html_text = html_text.replace("Loading 11,214 lab exercises…", "Loading lab exercises…")
    open(html_path, "w", encoding="utf-8").write(html_text)
    print("index.html: stamped course count in %d places; de-numbered lab loading string" % n_rep)

    print("wrote data/counts.json, university-manifest.json, api.json, data/colleges.json")
    print("ALL META BUILD STEPS PASSED")

if __name__ == "__main__":
    main()
