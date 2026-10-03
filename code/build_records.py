#!/usr/bin/env python3
"""Signature University record builder — machine-readable course structure.

Reads data/chunks/cNNNN.json and writes (deterministic, no content changes):
  data/lessons.idx.json       — every module + lesson with permanent IDs:
                                 {course_id}-M{mm} / {course_id}-M{mm}-L{ll}
  data/course-hashes.json      — sha256 over canonical course JSON per course
  data/ai-teachers-index.json  — JAH-TEACHER-###### per course
  university-schema.json       — JSON Schema for JAH-COURSE-RECORD/1.0 (+degree, +diploma)
  course-record-example.json   — one complete example course record

IDs are derived deterministically from the existing course IDs, so they are
stable across rebuilds. Run after code/generate.py.
"""
import json, os, hashlib

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
CURRICULUM_VERSION = "2026.10"

def canon(obj):
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)

def main():
    lessons_idx = {}
    hashes = {}
    teachers = []
    n = 0
    ci = 1
    while True:
        p = os.path.join(DATA, "chunks", "c%04d.json" % ci)
        if not os.path.exists(p):
            break
        courses = json.load(open(p, encoding="utf-8"))
        for c in courses:
            n += 1
            cid = c["id"]
            num = int(cid.rsplit("-", 1)[1])
            mods = []
            for mi, m in enumerate(c.get("modules", []), 1):
                mid = "%s-M%02d" % (cid, mi)
                lids = []
                for li, lt in enumerate(m.get("lessons", []), 1):
                    lids.append(["%s-L%02d" % (mid, li), lt])
                mods.append([mid, m.get("m", ""), lids])
            lessons_idx[cid] = mods
            hashes[cid] = hashlib.sha256(canon(c).encode("utf-8")).hexdigest()
            t = c.get("teacher", {})
            teachers.append({
                "teacher_id": "JAH-TEACHER-%06d" % num,
                "course_id": cid,
                "course_code": c.get("code"),
                "course_title": c.get("title"),
                "college_key": c.get("college_key"),
                "name": t.get("name"),
                "title": t.get("title"),
                "version": CURRICULUM_VERSION,
                "scope": "course",
            })
        ci += 1

    with open(os.path.join(DATA, "lessons.idx.json"), "w", encoding="utf-8") as f:
        json.dump(lessons_idx, f, separators=(",", ":"))
    with open(os.path.join(DATA, "course-hashes.json"), "w", encoding="utf-8") as f:
        json.dump(hashes, f, separators=(",", ":"))
    with open(os.path.join(DATA, "ai-teachers-index.json"), "w", encoding="utf-8") as f:
        json.dump({"version": CURRICULUM_VERSION, "count": len(teachers),
                   "teachers": teachers}, f, separators=(",", ":"))

    # ---- JSON Schema: JAH-COURSE-RECORD/1.0 ----
    schema = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "$id": "https://justinahiggins614-cmyk.github.io/signature-university/university-schema.json",
        "title": "JAH-COURSE-RECORD/1.0",
        "description": ("Permanent record standard for Signature University courses. "
                        "Independent free learning project; not government-accredited."),
        "version": "1.0",
        "type": "object",
        "required": ["id", "code", "title", "college", "college_key", "level",
                     "desc", "modules", "readings", "labs", "teacher", "version"],
        "properties": {
            "id": {"type": "string", "pattern": "^JAH-COURSE-[0-9]{6}$",
                   "description": "Permanent immutable course ID. Never reused."},
            "code": {"type": "string", "description": "Department code + level, e.g. ENG 101"},
            "title": {"type": "string"},
            "college": {"type": "string"},
            "college_key": {"type": "string"},
            "college_id": {"type": "string", "pattern": "^JAH-COLLEGE-[0-9]{2}$"},
            "level": {"type": "integer", "enum": [101, 201, 301, 401, 501, 601],
                      "description": "Signature University curriculum level (not an accredited credit equivalency)."},
            "credits": {"type": "integer"},
            "desc": {"type": "string"},
            "prereq": {"type": ["string", "null"], "description": "JAH-COURSE-###### or null"},
            "modules": {"type": "array", "minItems": 6, "maxItems": 6, "items": {
                "type": "object",
                "required": ["module_id", "title", "lessons"],
                "properties": {
                    "module_id": {"type": "string", "pattern": "^JAH-COURSE-[0-9]{6}-M[0-9]{2}$"},
                    "title": {"type": "string"},
                    "lessons": {"type": "array", "minItems": 4, "maxItems": 4, "items": {
                        "type": "object",
                        "required": ["lesson_id", "title"],
                        "properties": {
                            "lesson_id": {"type": "string",
                                          "pattern": "^JAH-COURSE-[0-9]{6}-M[0-9]{2}-L[0-9]{2}$"},
                            "title": {"type": "string"},
                        }}}}}},
            "readings": {"type": "array", "items": {
                "type": "object",
                "required": ["t", "label", "url"],
                "properties": {
                    "t": {"type": "string", "enum": ["dict", "wiki", "spec", "patent", "book"],
                          "description": "Source type: dictionary, wiki, Signature spec draft, public patent record, book shelf."},
                    "label": {"type": "string"}, "url": {"type": "string", "format": "uri"}}}},
            "labs": {"type": "array", "items": {
                "type": "object",
                "properties": {
                    "lab_id": {"type": "string"},
                    "t": {"type": "string"}, "d": {"type": "string"},
                    "lab_type": {"type": "string", "enum": ["BROWSER_SIMULATION", "VIRTUAL_LAB", "HOME_PROJECT", "FIELD_ASSIGNMENT", "BUILD_CHALLENGE"]}}}},
            "teacher": {"type": "object",
                        "required": ["teacher_id", "name", "title"],
                        "properties": {
                            "teacher_id": {"type": "string", "pattern": "^JAH-TEACHER-[0-9]{6}$"},
                            "name": {"type": "string"}, "title": {"type": "string"},
                            "scope": {"type": "string", "enum": ["course"]}}},
            "version": {"type": "string", "description": "Curriculum version of this record."},
            "content_hash": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
            "canonical_url": {"type": "string", "format": "uri"},
        },
        "definitions": {
            "degree": {
                "title": "JAH-DEGREE-RECORD/1.0",
                "type": "object",
                "required": ["id", "name", "college", "need", "min_level"],
                "properties": {
                    "id": {"type": "string"}, "name": {"type": "string"},
                    "college": {"type": "string"}, "ckey": {"type": "string"},
                    "need": {"type": "integer", "description": "Required number of courses."},
                    "min_level": {"type": "integer"},
                    "version": {"type": "string"},
                }},
            "diploma": {
                "title": "JAH-DIPLOMA-RECORD/1.0",
                "description": ("Certificate of Completion record. Not government-accredited. "
                                "Verification verifies the record, not the identity of the named learner."),
                "type": "object",
                "required": ["diploma_id", "degree_id", "learner", "awarded",
                             "curriculum_version", "diploma_hash"],
                "properties": {
                    "diploma_id": {"type": "string", "pattern": "^JAH-DIPLOMA-[0-9]{6}$"},
                    "degree_id": {"type": "string"},
                    "learner": {"type": "string", "description": "User-supplied name; not independently verified."},
                    "awarded": {"type": "string"},
                    "official_test_score": {"type": "string"},
                    "curriculum_version": {"type": "string"},
                    "diploma_hash": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
                }},
        },
    }
    with open(os.path.join(ROOT, "university-schema.json"), "w", encoding="utf-8") as f:
        json.dump(schema, f, indent=1)
        f.write("\n")

    # ---- example record ----
    c0 = json.load(open(os.path.join(DATA, "chunks", "c0001.json"), encoding="utf-8"))[0]
    mods = []
    for mi, m in enumerate(c0["modules"], 1):
        mid = "%s-M%02d" % (c0["id"], mi)
        mods.append({
            "module_id": mid, "title": m["m"],
            "lessons": [{"lesson_id": "%s-L%02d" % (mid, li), "title": lt}
                         for li, lt in enumerate(m["lessons"], 1)],
        })
    example = {
        "$schema": "university-schema.json",
        "id": c0["id"], "code": c0["code"], "title": c0["title"],
        "college": c0["college"], "college_key": c0["college_key"],
        "college_id": "JAH-COLLEGE-01",
        "level": c0["level"], "credits": c0["credits"], "desc": c0["desc"],
        "prereq": c0["prereq"],
        "modules": mods,
        "readings": c0["readings"], "labs": c0["labs"],
        "teacher": {"teacher_id": "JAH-TEACHER-000001", **c0["teacher"], "scope": "course"},
        "version": CURRICULUM_VERSION,
        "content_hash": hashes[c0["id"]],
        "canonical_url": "https://justinahiggins614-cmyk.github.io/signature-university/?course=" + c0["id"],
    }
    with open(os.path.join(ROOT, "course-record-example.json"), "w", encoding="utf-8") as f:
        json.dump(example, f, indent=1, ensure_ascii=False)
        f.write("\n")

    print("courses: %d | lessons indexed: %d | hashes: %d | teachers: %d" %
          (n, sum(len(m[2]) for mods in lessons_idx.values() for m in mods),
           len(hashes), len(teachers)))
    print("wrote data/lessons.idx.json, data/course-hashes.json, data/ai-teachers-index.json,")
    print("      university-schema.json, course-record-example.json")

if __name__ == "__main__":
    main()
