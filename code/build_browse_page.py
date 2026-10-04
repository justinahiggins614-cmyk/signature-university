#!/usr/bin/env python3
"""Product-forward A-Z browse page for The Signature University.

Builds browse.html (repo root) carrying the full course catalog as
A-Z collapsible <details> lists: 11 colleges -> letter -> courses.

LAZY LOADING (phone-friendly): browse.html ships with ZERO course rows.
Each letter's courses live in data/browse/<college>-<letter>.json and are
fetched only when that letter's <details> is first opened. The search box
fetches the compact courses.idx.json once, on first use.

COUNTS: read from data/counts.json (the single authoritative count source)
and written into browse.html's header, hero and meta description at build
time. This builder is called at the END of code/build_meta.py, AFTER the
data flushes, so the stamped count can never be one run behind.

Re-run any time the catalog changes (via build_meta.py, or directly).
Purely additive to the site's look: reuses the static browse-page theme.
"""
import json, os, html, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
BROWSE_DATA = os.path.join(DATA, "browse")
BASE = "https://justinahiggins614-cmyk.github.io/signature-university/"

CSS = """body{font-family:Georgia,'Times New Roman',serif;background:#0a0e1c;color:#f0e9d6;margin:0;line-height:1.6}
.wrap{max-width:960px;margin:0 auto;padding:26px 18px 60px}
a{color:#9fc2ff}
.hero{border:1px solid #2b3560;border-radius:16px;padding:26px 22px;margin:0 0 22px;
 background:radial-gradient(ellipse at 20% 0%,#16204a 0%,#0a0e1c 70%)}
.hero h1{color:#f2d47e;font-size:1.9em;margin:.1em 0 .3em;line-height:1.25}
.hero .big{font-size:1.15em;color:#f0e9d6}
.hero .countline{font-size:1.35em;margin:.5em 0}
.hero .countline b{color:#f2d47e;font-size:1.5em}
.meta{color:#a9b0c7;font-size:.92em}
.searchbox{margin:18px 0;padding:14px;border:1px solid #2b3560;border-radius:12px;background:#0b0f1c}
.searchbox input{width:100%;box-sizing:border-box;font-size:1.05em;padding:12px 14px;border-radius:10px;
 border:1px solid #3a4670;background:#10162c;color:#f0e9d6;font-family:inherit}
.searchbox input::placeholder{color:#8a93b3}
.results{list-style:none;padding:0;margin:10px 0 0;max-height:60vh;overflow:auto}
.results li{margin:.4em 0;padding:.35em .5em;border-bottom:1px dotted #2b3560}
details.college{border:1px solid #2b3560;border-radius:12px;margin:12px 0;background:#0d1226}
details.college>summary{cursor:pointer;padding:15px 16px;font-size:1.12em;color:#f2d47e;list-style:none}
details.college>summary::-webkit-details-marker{display:none}
details.college>summary:before{content:"\\25B6  ";color:#d9a441;font-size:.8em}
details.college[open]>summary:before{content:"\\25BC  "}
details.college>summary .n{color:#a9b0c7;font-size:.85em;font-weight:normal}
.letters{padding:4px 16px 18px}
details.letter{display:inline-block;vertical-align:top;width:100%;max-width:430px;margin:6px 8px 6px 0;
 border:1px solid #232c52;border-radius:10px;background:#0b0f1c}
details.letter>summary{cursor:pointer;padding:11px 13px;color:#9fc2ff;font-weight:bold;list-style:none}
details.letter>summary::-webkit-details-marker{display:none}
details.letter>summary .n{color:#a9b0c7;font-weight:normal;font-size:.88em}
.courselist{list-style:none;padding:2px 13px 12px;margin:0;max-height:320px;overflow:auto}
.courselist li{margin:.32em 0;font-size:.95em}
.courselist .code{color:#d9a441}
.courselist .lvl{color:#a9b0c7;font-size:.85em}
.honest{border:1px dashed #6b5a2e;border-radius:12px;padding:14px 16px;margin:26px 0;color:#d8cfae;background:#141021}
.honest b{color:#f2d47e}
.wings{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:12px;margin:18px 0}
.wing{border:1px solid #2b3560;border-radius:12px;padding:16px;background:#0d1226}
.wing h3{color:#f2d47e;margin:.1em 0 .4em;font-size:1.05em}
.topnav{margin:0 0 18px;font-size:.95em}
footer{margin-top:34px;padding-top:16px;border-top:1px solid #2b3560;color:#a9b0c7;font-size:.88em}
.loadmsg{color:#8a93b3;font-size:.9em;padding:6px 2px}
@media(max-width:520px){.hero h1{font-size:1.45em}details.letter{max-width:100%}}"""

HONEST_TOP = ("<b>Official within the Signature system.</b> Every diploma and transcript here is "
    "officially stamped by The Signature University — the independent free learning project of "
    "Justin Addam Higgins. <b>No government accreditation is claimed;</b> diplomas certify course "
    "completion. AI teachers are AI study assistants, not licensed professionals.")


def letter_of(title):
    m = re.match(r"[A-Za-z]", title.strip())
    return m.group(0).upper() if m else "#"


def main():
    os.makedirs(BROWSE_DATA, exist_ok=True)
    idx = json.load(open(os.path.join(DATA, "courses.idx.json"), encoding="utf-8"))
    cols = json.load(open(os.path.join(DATA, "colleges.json"), encoding="utf-8"))["colleges"]
    counts = json.load(open(os.path.join(DATA, "counts.json"), encoding="utf-8"))
    n = counts["course_count"]
    assert len(idx) == n, "idx rows %d != counts.json course_count %d" % (len(idx), n)
    n_fmt = "{:,}".format(n)

    projects = json.load(open(os.path.join(DATA, "projects.json"), encoding="utf-8"))
    library = json.load(open(os.path.join(DATA, "library.json"), encoding="utf-8"))

    # ---- write per-college-letter lazy shards ----
    buckets = {}
    for r in idx:
        L = letter_of(r["t"])
        buckets.setdefault((r["k"], L), []).append(r)
    shard_total = 0
    for (k, L), rows in sorted(buckets.items()):
        rows.sort(key=lambda r: (r["t"].lower(), r["i"]))
        shard = [{"i": r["i"], "c": r["c"], "t": r["t"], "l": r["l"]} for r in rows]
        with open(os.path.join(BROWSE_DATA, "%s-%s.json" % (k, L)), "w", encoding="utf-8") as f:
            json.dump(shard, f, separators=(",", ":"))
        shard_total += len(rows)
    assert shard_total == n, "shard rows %d != %d" % (shard_total, n)

    # ---- build browse.html ----
    college_names = {c["key"]: c for c in cols}
    college_html = []
    for c in cols:
        k = c["key"]
        letters = sorted(L for (kk, L) in buckets if kk == k)
        letter_html = []
        for L in letters:
            cnt = len(buckets[(k, L)])
            letter_html.append(
                '<details class="letter" data-k="%s" data-l="%s">'
                '<summary><span class="lt">%s</span> <span class="n">%d course%s</span></summary>'
                '<div class="lbody"><p class="loadmsg">Loading…</p></div></details>'
                % (k, L, html.escape(L), cnt, "" if cnt == 1 else "s"))
        college_html.append(
            '<details class="college"><summary>%s <span class="n">— %d courses · %s</span></summary>'
            '<div class="letters">%s<p class="meta" style="margin-top:10px">'
            'Crawler-friendly static copy: <a href="browse/college-%s.html">%s course list</a></p></div></details>'
            % (html.escape(c["name"]), c["courses"], html.escape(c["tagline"]),
               "\n".join(letter_html), k, html.escape(c["name"])))

    wings_html = (
        '<div class="wings">'
        '<div class="wing"><h3>🏗 Capstone Projects Wing</h3><p class="meta">%d hands-on capstone '
        'projects — plan it, build it, document it, present it.</p>'
        '<p><a href="./#projects">Enter the Projects Wing →</a></p></div>'
        '<div class="wing"><h3>📖 Library Wing</h3><p class="meta">%d curated shelves of cross-linked '
        'readings for every course.</p><p><a href="./#library">Enter the Library Wing →</a></p></div>'
        '<div class="wing"><h3>🎓 Degrees &amp; Diplomas</h3><p class="meta">%d degree tracks across the '
        '11 colleges, with printable officially-stamped diplomas.</p>'
        '<p><a href="./#degrees">See the Degrees →</a></p></div></div>'
        % (len(projects), len(library.get("shelves", library)) if isinstance(library, dict) else 0,
           counts.get("degree_count", 42)))

    desc = ("Browse all %s free courses at The Signature University — 11 colleges, A-Z, "
            "every course with full syllabus, labs, and its own AI teacher." % n_fmt)
    body = (
        '<div class="wrap">\n'
        '<p class="topnav"><a href="./">🏛 The Signature University</a> · <b>Browse A–Z</b> · '
        '<a href="browse/">Static browse index</a></p>\n'
        '<div class="hero">\n'
        f'<h1>The Course Catalog, A–Z</h1>\n'
        f'<p class="countline">Browse <b id="browseCount">{n_fmt}</b> free courses</p>\n'
        f'<p class="big">All {n_fmt} courses, across the 11 colleges — every course with a full '
        'syllabus, hands-on labs, readings, and its own personal <b>AI teacher</b>. Open a college, '
        'pick a letter, pick a course — its permanent course page opens with everything.</p>\n'
        f'<p class="meta">Free forever. Learn at your own pace, on your phone or computer.</p>\n'
        '</div>\n'
        '<div class="searchbox" role="search">\n'
        '<label class="meta" for="bq" style="display:block;margin-bottom:8px">Search the catalog '
        '(loads the compact index once, on first search)</label>\n'
        '<input id="bq" type="search" placeholder="Try “welding”, “calculus”, “contracts”, “JAH-COURSE-000260”…">\n'
        '<ul class="results" id="bqr" aria-live="polite"></ul></div>\n'
        '<div class="honest">%s</div>\n'
        '%s\n'
        '<h2 style="color:#f2d47e">By college, then A–Z</h2>\n'
        '<p class="meta">Tap a college to open it, then tap a letter — that letter’s courses load '
        'only when you ask for them.</p>\n'
        '%s\n'
        '<h2 style="color:#f2d47e">Also explore the wings</h2>\n'
        '%s\n'
        '<div class="honest"><b>Honest notes:</b> All course material is original, written for The '
        'Signature University by Justin Addam Higgins. The Signature University is an independent '
        'free learning project — it claims no government accreditation; diplomas certify course '
        'completion (official within the Signature system). AI teachers are AI study assistants — '
        'encouraging guides, not licensed professionals. For medical, legal, or financial decisions, '
        'always consult a licensed professional.</div>\n'
        '<footer><p><a href="./">🏛 The Signature University</a> · '
        '<a href="https://justinahiggins614-cmyk.github.io/signature-math/">THE JAH NETWORK</a></p>\n'
        '<p>Catalog version %s · snapshot %s · machine-readable counts: '
        '<a href="data/counts.json">data/counts.json</a></p></footer>\n'
        '</div>'
        % (HONEST_TOP, "", "\n".join(college_html), wings_html,
           counts.get("catalog_version", "?"), counts.get("snapshot_id", "?")))

    js = """
(function(){
"use strict";
var idxCache=null,idxLoading=null;
function esc(s){return s.replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;");}
function courseLink(r){return '<li><a href="?course='+encodeURIComponent(r.i)+'"><span class="code">'+esc(r.c)+'</span> — '+esc(r.t)+'</a> <span class="lvl">'+esc(r.i)+' · level '+r.l+'</span></li>';}
// lazy letter shards: fetch on first open
document.querySelectorAll('details.letter').forEach(function(d){
  var loaded=false;
  d.addEventListener('toggle',function(){
    if(!d.open||loaded)return;loaded=true;
    var body=d.querySelector('.lbody');
    fetch('data/browse/'+d.getAttribute('data-k')+'-'+d.getAttribute('data-l')+'.json')
      .then(function(r){if(!r.ok)throw new Error('HTTP '+r.status);return r.json();})
      .then(function(rows){
        body.innerHTML='<ul class="courselist">'+rows.map(courseLink).join('')+'</ul>';})
      .catch(function(e){
        loaded=false;
        body.innerHTML='<p class="loadmsg">Could not load these courses ('+esc(e.message)+'). <a href="#" class="retry">Retry</a></p>';
        body.querySelector('.retry').addEventListener('click',function(ev){ev.preventDefault();loaded=false;d.dispatchEvent(new Event('toggle'));});
      });
  });
});
// search: fetch compact index once, on first use
var q=document.getElementById('bq'),qr=document.getElementById('bqr'),t=null;
function loadIdx(){
  if(idxCache)return Promise.resolve(idxCache);
  if(idxLoading)return idxLoading;
  idxLoading=fetch('data/courses.idx.json').then(function(r){if(!r.ok)throw new Error('HTTP '+r.status);return r.json();})
    .then(function(j){idxCache=j;return j;});
  return idxLoading;
}
q.addEventListener('input',function(){
  clearTimeout(t);
  t=setTimeout(function(){
    var s=q.value.trim().toLowerCase();
    if(s.length<2){qr.innerHTML='';return;}
    qr.innerHTML='<li class="loadmsg">Searching…</li>';
    loadIdx().then(function(rows){
      var out=[],i,r,hay;
      for(i=0;i<rows.length&&out.length<50;i++){r=rows[i];
        hay=(r.t+' '+r.c+' '+r.i).toLowerCase();
        if(hay.indexOf(s)>=0)out.push(courseLink(r));}
      qr.innerHTML=out.length?out.join(''):'<li class="loadmsg">No courses matched “'+esc(q.value)+'”. Try fewer words.</li>';
    }).catch(function(e){qr.innerHTML='<li class="loadmsg">Search failed to load ('+esc(e.message)+'). Check your connection and try again.</li>';});
  },250);
});
})();"""

    page = ("<!DOCTYPE html>\n<html lang=\"en\">\n<head>\n<meta charset=\"utf-8\">\n"
            "<meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">\n"
            "<title>The Signature University — Browse the Course Catalog A–Z</title>\n"
            '<meta name="description" content="%s">\n'
            '<meta property="og:title" content="The Signature University — Browse the Course Catalog A–Z">\n'
            '<meta property="og:description" content="%s">\n'
            '<link rel="canonical" href="%sbrowse.html">\n'
            '<script type="application/ld+json">{"@context":"https://schema.org","@type":"WebPage",'
            '"name":"The Signature University — Browse the Course Catalog A–Z",'
            '"description":"%s","url":"%sbrowse.html"}</script>\n'
            "<style>%s</style>\n</head>\n<body>\n%s\n<script>%s</script>\n</body>\n</html>\n"
            % (html.escape(desc), html.escape(desc), BASE, html.escape(desc), BASE, CSS, body, js))
    with open(os.path.join(ROOT, "browse.html"), "w", encoding="utf-8") as f:
        f.write(page)
    print("wrote browse.html + %d lazy shards (%s courses)" % (len(buckets), n_fmt))


if __name__ == "__main__":
    main()
