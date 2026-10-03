#!/usr/bin/env python3
"""Static crawlable browse pages for The Signature University (AI/crawler accessibility).

Generates browse/courses-NNN.html (1,000 courses per shard, plain <a href> deep
links, prev/next) + browse/colleges.html (11 colleges) + browse/index.html.
Re-run any time the catalog changes; then add the pages to sitemap.xml.
Purely additive — does not touch index.html's look or behavior.
"""
import json, os, html, math

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE = "https://justinahiggins614-cmyk.github.io/signature-university/"
OUT = os.path.join(ROOT, "browse")
PER = 1000

CSS = """body{font-family:Georgia,'Times New Roman',serif;background:#0a0e1c;color:#f0e9d6;margin:0;line-height:1.6}
.wrap{max-width:900px;margin:0 auto;padding:28px 18px}
h1{color:#f2d47e;font-size:1.5em}h2{color:#d9a441}
a{color:#9fc2ff}.meta{color:#a9b0c7;font-size:.9em}
.nav{display:flex;justify-content:space-between;margin:18px 0;flex-wrap:wrap;gap:8px}
ul{list-style:none;padding:0}li{margin:.35em 0}
.top{border-bottom:1px solid #2b3560;padding-bottom:10px;margin-bottom:16px}"""

def page(title, desc, body, canon):
    return ("<!DOCTYPE html>\n<html lang=\"en\">\n<head>\n<meta charset=\"utf-8\">\n"
            "<meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">\n"
            f"<title>{html.escape(title)}</title>\n"
            f"<meta name=\"description\" content=\"{html.escape(desc)}\">\n"
            f"<link rel=\"canonical\" href=\"{canon}\">\n"
            f"<style>{CSS}</style>\n</head>\n<body>\n<div class=\"wrap\">\n{body}\n</div>\n</body>\n</html>\n")

def main():
    os.makedirs(OUT, exist_ok=True)
    idx = json.load(open(os.path.join(ROOT, "data", "courses.idx.json")))
    cols = json.load(open(os.path.join(ROOT, "data", "colleges.json")))["colleges"]
    n = len(idx)
    shards = math.ceil(n / PER)

    # course shard pages
    for s in range(shards):
        chunk = idx[s*PER:(s+1)*PER]
        first, last = chunk[0]["i"], chunk[-1]["i"]
        items = "\n".join(
            f'<li><a href="../?course={r["i"]}">{html.escape(r["c"])} \u2014 {html.escape(r["t"])}</a> '
            f'<span class="meta">{r["i"]}</span></li>' for r in chunk)
        prev_ = (f'<a href="courses-{s:03d}.html">&larr; Previous 1,000</a>' if s > 0
                 else '<span class="meta">First page</span>')
        next_ = (f'<a href="courses-{s+2:03d}.html">Next 1,000 &rarr;</a>' if s < shards-1
                 else '<span class="meta">Last page</span>')
        body = (f'<div class="top"><p class="meta"><a href="../">The Signature University</a> &middot; '
                f'<a href="index.html">Browse index</a> &middot; <a href="colleges.html">Colleges</a></p>\n'
                f"<h1>Course catalog \u2014 page {s+1} of {shards}</h1>\n"
                f"<p>{first} through {last}: every course below opens its full individual course page "
                f"(overview, modules, readings, AI teacher) at its permanent link.</p></div>\n"
                f'<div class="nav">{prev_}{next_}</div>\n<ul>\n{items}\n</ul>\n'
                f'<div class="nav">{prev_}{next_}</div>')
        t = f"The Signature University courses {first}\u2013{last}"
        with open(os.path.join(OUT, f"courses-{s+1:03d}.html"), "w") as f:
            f.write(page(t, f"{len(chunk)} The Signature University courses, {first} to {last}, each with a permanent course page.", body, BASE+f"browse/courses-{s+1:03d}.html"))

    # colleges page
    citems = "\n".join(
        f'<li><a href="college-{c["key"]}.html">{html.escape(c["name"])}</a> '
        f'<span class="meta">{c["courses"]} courses &middot; {c["first_id"]}\u2013{c["last_id"]} &middot; {html.escape(c["tagline"])}</span></li>'
        for c in cols)
    cbody = (f'<div class="top"><p class="meta"><a href="../">The Signature University</a> &middot; '
             f'<a href="index.html">Browse index</a></p>\n'
             f"<h1>The 11 colleges</h1>\n<p>Every college opens the live catalog pre-filtered to its courses.</p></div>\n"
             f"<ul>\n{citems}\n</ul>")
    with open(os.path.join(OUT, "colleges.html"), "w") as f:
        f.write(page("The Signature University \u2014 the 11 colleges",
                     "The 11 colleges of The Signature University: 3,850 free courses with AI teachers.",
                     cbody, BASE+"browse/colleges.html"))

    # browse index
    shards_links = " ".join(f'<a href="courses-{s+1:03d}.html">{s+1}</a>' for s in range(shards))
    coll_links = " ".join(f'<a href="college-{c["key"]}.html">{html.escape(c["name"])}</a>' for c in cols)
    ibody = (f'<div class="top"><p class="meta"><a href="../">The Signature University</a></p>\n'
             f"<h1>Browse the catalog</h1>\n"
             f"<p>Static, crawler-friendly index of all {n:,} courses. Every link is a permanent course URL.</p></div>\n"
             f"<h2>Course pages</h2><p>{shards_links}</p>\n"
             f"<h2>By college</h2><p>{coll_links}</p>\n"
             f'<h2>Departments</h2><p><a href="colleges.html">The 11 colleges</a></p>')
    with open(os.path.join(OUT, "index.html"), "w") as f:
        f.write(page("The Signature University \u2014 browse index",
                     f"Static browse index: all {n:,} The Signature University courses and the 11 colleges.",
                     ibody, BASE+"browse/"))

    # per-college static department pages (pre-rendered fallback for crawlers)
    byk = {}
    for r in idx:
        byk.setdefault(r["k"], []).append(r)
    for c in cols:
        rows = byk.get(c["key"], [])
        items = "\n".join(
            f'<li><a href="../?course={r["i"]}">{html.escape(r["c"])} \u2014 {html.escape(r["t"])}</a> '
            f'<span class="meta">{r["i"]} &middot; level {r["l"]}</span></li>' for r in rows)
        colbody = (f'<div class="top"><p class="meta"><a href="../">The Signature University</a> &middot; '
                   f'<a href="index.html">Browse index</a> &middot; <a href="colleges.html">Colleges</a></p>\n'
                   f"<h1>{html.escape(c['name'])}</h1>\n"
                   f"<p>{html.escape(c['tagline'])} {len(rows)} courses, each with a permanent course page.</p></div>\n"
                   f"<ul>\n{items}\n</ul>")
        with open(os.path.join(OUT, f"college-{c['key']}.html"), "w") as f:
            f.write(page(f"The Signature University \u2014 {c['name']}",
                         f"{len(rows)} free {c['name']} courses with full syllabi and AI teachers.",
                         colbody, BASE+f"browse/college-{c['key']}.html"))

    # machine-readable curriculum feed
    feed = {"generated": __import__("datetime").date.today().isoformat(),
            "site": "The Signature University",
            "base": BASE,
            "total_courses": n,
            "courses": [{"id": r["i"], "code": r["c"], "title": r["t"],
                         "college": r["k"], "level": r["l"],
                         "url": BASE + "?course=" + r["i"]} for r in idx]}
    with open(os.path.join(ROOT, "data", "courses-catalog.json"), "w") as f:
        json.dump(feed, f, separators=(",", ":"))
    print(f"wrote {shards} course shards + colleges + {len(cols)} college pages + index + courses-catalog.json ({n} courses)")

if __name__ == "__main__":
    main()
