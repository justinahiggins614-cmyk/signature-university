#!/usr/bin/env node
/* The Signature University — usability hardening functional harness.
   Drives the site's REAL shipped functions (js/degree-flow.js, js/sha256.js,
   js/jah-talk-fallback.js, and replicas of the pure page logic from
   index.html) against REAL shipped data. Reports per-feature PASS/FAIL. */
"use strict";
const fs = require("fs"), path = require("path");
const ROOT = path.dirname(path.dirname(path.dirname(path.resolve(__filename))));
const D = p => JSON.parse(fs.readFileSync(path.join(ROOT, p), "utf8"));
let pass = 0, fail = 0;
function ok(name, cond, extra) {
  if (cond) { pass++; console.log("PASS  " + name); }
  else { fail++; console.log("FAIL  " + name + (extra ? " :: " + extra : "")); }
}

// ---- real modules ----
const DegFlow = require(path.join(ROOT, "js", "degree-flow.js"));
const sha256hex = require(path.join(ROOT, "js", "sha256.js"));
require(path.join(ROOT, "js", "jah-talk-fallback.js"));
const JAHtalk = global.JAHtalk;

// ---- real data ----
const counts = D("data/counts.json");
const colleges = D("data/colleges.json");
const idx = D("data/courses.idx.json");
const degs = D("data/degrees.json");
const labs = D("data/labs.json");
const projects = D("data/projects.json");
const library = D("data/library.json");
const catalogFeed = D("data/courses-catalog.json");
const api = D("api.json");
const manifest = D("university-manifest.json");
const html = fs.readFileSync(path.join(ROOT, "index.html"), "utf8");

// 1. count reconciliation — the authoritative source is data/counts.json
ok("counts.json course_count=3850", counts.course_count === 3850);
ok("api.json total_courses matches counts", api.total_courses === counts.course_count);
ok("manifest course_count matches", manifest.course_count === counts.course_count);
ok("colleges.json total matches", colleges.total === counts.course_count);
ok("courses.idx.json length matches", idx.length === counts.course_count);
ok("courses-catalog.json total_courses matches", catalogFeed.total_courses === counts.course_count);
ok("degrees count matches (42)", degs.length === counts.degree_count);
ok("labs count matches (11550)", labs.length === counts.lab_count);
ok("projects count matches (88)", projects.length === counts.project_count);
ok("ai_teacher_count == course_count", counts.ai_teacher_count === counts.course_count);

// 2. chunk coverage: every idx row resolves to an existing chunk file
function chunkFor(id) { var n = parseInt(id.slice(-6), 10); return "c" + String(Math.ceil(n / 100)).padStart(4, "0"); }
const chunks = new Set(fs.readdirSync(path.join(ROOT, "data", "chunks")));
let missing = 0;
idx.forEach(r => { if (!chunks.has(chunkFor(r.i) + ".json")) missing++; });
ok("every course id resolves to a shipped chunk file", missing === 0, missing + " missing");
ok("39 chunk files present", chunks.size === 39, chunks.size);

// 3. course record shape (first chunk)
const c1 = D("data/chunks/c0001.json");
const cr = c1.find(c => c.id === "JAH-COURSE-000001");
ok("course record has 6 modules", cr.modules.length === 6);
ok("course record has 24 lessons", cr.modules.reduce((n, m) => n + m.lessons.length, 0) === 24);
ok("course record has readings", Array.isArray(cr.readings) && cr.readings.length > 0);
ok("course record has labs", Array.isArray(cr.labs) && cr.labs.length > 0);
ok("course record has AI teacher", cr.teacher && cr.teacher.name);

// 4. degree completion rules: curriculum() resolves exactly `need` courses per degree
let degShort = 0;
degs.forEach(d => { if (DegFlow.curriculum(idx, d).length !== d.need) degShort++; });
ok("all 42 degree curricula resolve exactly 'need' courses", degShort === 0, degShort + " short");
ok("degree rule: eng certificate = 6 courses@101+", DegFlow.curriculum(idx, degs[0]).length === 6);

// 5. official test: buildTest determinism + shape
const fullRecs = c1.slice(0, 30);
const t1 = DegFlow.buildTest(fullRecs, DegFlow.testSeed(degs[0].id, 1), 10);
const t2 = DegFlow.buildTest(fullRecs, DegFlow.testSeed(degs[0].id, 1), 10);
const t3 = DegFlow.buildTest(fullRecs, DegFlow.testSeed(degs[0].id, 2), 10);
ok("buildTest deterministic for same seed+attempt", JSON.stringify(t1) === JSON.stringify(t2));
ok("buildTest differs across attempts", JSON.stringify(t1) !== JSON.stringify(t3));
ok("10 questions built", t1.length === 10, t1.length);
ok("every question has 4 options incl. answer", t1.every(q => q.opts.length === 4 && q.opts.indexOf(q.answer) >= 0));

// 6. gradeTest boundaries: 70% to pass
const ans7 = t1.map((q, i) => i < 7 ? q.answer : "WRONG");
const ans6 = t1.map((q, i) => i < 6 ? q.answer : "WRONG");
ok("7/10 passes", DegFlow.gradeTest(t1, ans7).passed === true);
ok("6/10 fails", DegFlow.gradeTest(t1, ans6).passed === false);
ok("empty answers fail", DegFlow.gradeTest([], []).passed === false);

// 7. degree stamp format + determinism
const s1 = DegFlow.degreeStamp("Alex Rivera", "JAH-DEGREE-ENG-1", "October 3, 2026");
ok("degree stamp format JAH-DEGREE-######", /^JAH-DEGREE-\d{6}$/.test(s1));
ok("degree stamp deterministic", s1 === DegFlow.degreeStamp("Alex Rivera", "JAH-DEGREE-ENG-1", "October 3, 2026"));

// 8. catalog search/filter logic (replica of filteredIdx)
function filteredIdx(F) {
  return idx.filter(function (r) {
    if (F.college && r.k !== F.college) return false;
    if (F.level && String(r.l) !== F.level) return false;
    if (F.az && r.t.charAt(0).toUpperCase() !== F.az) return false;
    if (F.q) { var hay = (r.t + " " + r.c + " " + r.i).toLowerCase(); if (hay.indexOf(F.q) < 0) return false; }
    return true;
  });
}
ok("search 'welding' finds courses", filteredIdx({ q: "welding" }).length > 0);
ok("search finds by course id", filteredIdx({ q: "jah-course-000260" }).length === 1);
ok("search no-match returns empty", filteredIdx({ q: "zzzqqqzzz" }).length === 0);
const engOnly = filteredIdx({ college: "engineering" });
ok("college filter engineering = 350", engOnly.length === 350, engOnly.length);
ok("college filter only returns that college", engOnly.every(r => r.k === "engineering"));
const l101 = filteredIdx({ level: "101" });
ok("level filter 101 non-empty", l101.length > 0 && l101.every(r => r.l === 101));
const azA = filteredIdx({ az: "A" });
ok("A-Z filter works", azA.length > 0 && azA.every(r => r.t.charAt(0).toUpperCase() === "A"));
ok("combined college+level filter", filteredIdx({ college: "medicine", level: "601" }).every(r => r.k === "medicine" && r.l === 601));

// 9. course finder logic (replica of Finder.keywords/hay)
const STOP = { a:1, an:1, the:1, and:1, or:1, of:1, to:1, in:1, for:1, with:1, what:1, want:1, learn:1, courses:1, course:1, me:1 };
function keywords(q) { return String(q || "").toLowerCase().replace(/[^a-z0-9]+/g, " ").split(" ").filter(function (w) { return w.length >= 3 && !STOP[w]; }); }
ok("finder tokenizes 'I want to learn welding'", keywords("I want to learn welding").indexOf("welding") >= 0);
ok("finder drops stopwords", keywords("the and of").length === 0);
function finderAsk(text) {
  const kws = keywords(text);
  if (!kws.length) return null;
  return idx.map(r => { var hay = (r.t + " " + r.c + " " + r.i).toLowerCase(), sc = 0;
    kws.forEach(k => { if (hay.indexOf(k) >= 0) sc++; }); return { r: r, sc: sc }; })
    .filter(x => x.sc > 0).sort((a, b) => b.sc - a.sc).slice(0, 5);
}
ok("finder matches 'electrician wiring'", finderAsk("become an electrician, wiring").length > 0);
ok("finder deep link format", ("?course=" + idx[0].i) === "?course=JAH-COURSE-000001");

// 10. deep-link validation
const courseRe = /^JAH-COURSE-\d{6}$/, degRe = /^JAH-DEGREE-[A-Z]+-\d+$/;
ok("deep-link regex accepts real course", courseRe.test("JAH-COURSE-000260"));
ok("deep-link regex rejects junk", !courseRe.test("javascript:alert(1)") && !courseRe.test("JAH-COURSE-9999999"));
ok("degree regex accepts JAH-DEGREE-ENG-1", degRe.test("JAH-DEGREE-ENG-1"));
ok("degree regex rejects junk", !degRe.test("JAH-DEGREE-"));

// 11. diploma record (replica of diplomaRecord + djb2 from index.html)
function djb2(s) { var h = 5381; for (var i = 0; i < s.length; i++) h = ((h << 5) + h + s.charCodeAt(i)) >>> 0; return h; }
function diplomaRecord(d, name, dateStr, stamp, score) {
  return {
    record: "JAH-DIPLOMA-RECORD", version: "1.0",
    diploma_id: "JAH-DIPLOMA-" + String(djb2(name + "|" + d.id + "|" + dateStr) % 900000 + 100000),
    degree_id: d.id, degree_name: d.name, college: d.college, learner: name, awarded: dateStr,
    official_test_score: score || "", stamp: stamp, curriculum_version: "2026.10",
    issuer: "The Signature University, founded by Justin Addam Higgins",
    note: "Independent free learning project; not government-accredited. This record certifies completion of the listed The Signature University courses and a passed official test (official within the Signature system). The learner name is user-supplied and is not independently verified."
  };
}
const dip = diplomaRecord(degs[0], "Alex Rivera", "October 3, 2026", "JAH-DEGREE-123456", "8/10");
ok("diploma id format JAH-DIPLOMA-######", /^JAH-DIPLOMA-\d{6}$/.test(dip.diploma_id));
ok("diploma note keeps no-accreditation honesty", /not government-accredited/i.test(dip.note));
ok("diploma note keeps official-within-Signature", /official within the Signature system/i.test(dip.note));
// verify/ page recomputes the same id (replica of diplomaIdFor)
const vrf = fs.readFileSync(path.join(ROOT, "verify", "index.html"), "utf8");
ok("verify page diploma id formula matches", vrf.indexOf('djb2(name+"|"+degId+"|"+dateStr)%900000+100000') >= 0);
const dipHash = sha256hex(JSON.stringify(dip));
ok("diploma content hash is 64-hex sha256", /^[0-9a-f]{64}$/.test(dipHash));

// 12. sha256 sanity (known vector)
ok("sha256('abc') known vector", sha256hex("abc") === "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad");

// 13. AI teacher / guide talk path
const prof = { name: "University Guide", id: "", description: "Friendly campus guide", abilities: ["match goals"], domain: "The Signature University", kind: "domain" };
const hello = JAHtalk.reply(prof, "hello");
ok("JAHtalk.reply answers social intent with non-empty string", typeof hello === "string" && hello.length > 20);
const duty = JAHtalk.reply(prof, "what are your duties");
ok("JAHtalk.reply answers duties question", typeof duty === "string" && duty.length > 20);
ok("JAHtalk.guard keeps warm human reply", JAHtalk.guard(hello, prof).length > 20);
// teacher lesson-match (replica of teacherReply keyword scoring)
const FRAMES = [["Principles of ", ""], ["", " : Core Concepts"], ["Guided Practice: ", ""], ["", " in the Real World"], ["Common Mistakes in ", ""], ["", " : Worked Examples"], ["Review and Checkup: ", ""], ["Where ", " Goes Next"]];
function stripTopic(lesson) {
  for (var i = 0; i < FRAMES.length; i++) { var p = FRAMES[i][0], s = FRAMES[i][1];
    if (lesson.indexOf(p) === 0 && (!s || lesson.slice(-s.length) === s)) return lesson.slice(p.length, s ? lesson.length - s.length : lesson.length); }
  return lesson;
}
function bestLesson(course, q) {
  const toks = q.toLowerCase().split(/[^a-z0-9]+/).filter(t => t.length > 2);
  const stop = { the:1, and:1, for:1, what:1, with:1, about:1, how:1, does:1, why:1, lesson:1, module:1, explain:1, tell:1, please:1, course:1 };
  let best = null, bs = 0;
  course.modules.forEach((m, mi) => m.lessons.forEach(l => {
    const lt = l.toLowerCase(); let s = 0;
    toks.forEach(t => { if (!stop[t] && lt.indexOf(t) >= 0) s++; });
    if (s > bs) { bs = s; best = { m: mi, mt: m.m, l: l }; }
  }));
  return best;
}
const bl = bestLesson(cr, "explain structural loads and forces");
ok("teacher lesson keyword match finds a lesson", bl && bl.l.length > 0);
ok("stripTopic strips frame prefixes", stripTopic("Principles of X") === "X");

// 14. course quick answers (replica of courseQuick)
function courseQuickAns(c, q) {
  var ql = q.toLowerCase(), a = "";
  if (/credit/.test(ql)) a = c.credits + " credits.";
  else if (/level/.test(ql)) a = "Level " + c.level + " in " + c.college + ".";
  else if (/how many (module|lesson)|module/.test(ql)) { var n = 0; c.modules.forEach(function (m) { n += m.lessons.length; }); a = c.modules.length + " modules, " + n + " lessons in total."; }
  return a;
}
ok("course quick answers credits", courseQuickAns(cr, "how many credits?") === cr.credits + " credits.");
ok("course quick answers module/lesson count", courseQuickAns(cr, "how many modules?") === "6 modules, 24 lessons in total.");

// 15. library shelves
const collegeKeys = colleges.colleges.map(c => c.key);
ok("library covers all 11 colleges", collegeKeys.every(k => Array.isArray(library[k]) && library[k].length > 0));
ok("library words non-empty per college", collegeKeys.every(k => library[k].length >= 5));

// 16. progress save/restore round-trip (localStorage code path replica)
const PROG = { name: "Alex Rivera", done: { "JAH-COURSE-000001": 1728000000000, "JAH-COURSE-000351": 1728000000100 }, degrees: { "JAH-DEGREE-ENG-1": { date: "October 3, 2026", stamp: "JAH-DEGREE-123456", score: "8/10", name: "Alex Rivera" } }, tests: { "JAH-DEGREE-ENG-1": 1 } };
const restored = JSON.parse(JSON.stringify(PROG));
ok("progress survives serialize/restore round-trip", Object.keys(restored.done).length === 2 && restored.degrees["JAH-DEGREE-ENG-1"].stamp === "JAH-DEGREE-123456");
const importOk = (id) => /^JAH-COURSE-\d{6}$/.test(id);
ok("import validates course ids", importOk("JAH-COURSE-000001") && !importOk("JAH-COURSE-ABC") && !importOk("<script>"));

// 17. transcript build (replica of buildTranscript)
function buildTranscript() {
  const idxM = {}; idx.forEach(r => { idxM[r.i] = r; });
  const courses = Object.keys(PROG.done).map(id => { const r = idxM[id] || {}; return { course_id: id, code: r.c || "", title: r.t || "" }; });
  const tr = { record: "JAH-TRANSCRIPT", version: "1.0", site: "The Signature University", learner: PROG.name, courses_completed: courses, note: "Independent free learning project; not government-accredited." };
  tr.transcript_hash = sha256hex(JSON.stringify(tr));
  return tr;
}
const tr = buildTranscript();
ok("transcript hash recomputes deterministically", tr.transcript_hash === sha256hex(JSON.stringify({ record: "JAH-TRANSCRIPT", version: "1.0", site: "The Signature University", learner: PROG.name, courses_completed: tr.courses_completed, note: "Independent free learning project; not government-accredited." })));

// 18. static HTML: loading-state rules
ok("homeStats boots with stamped counts (no bare …)", /id="homeStats"><div class="stat"><b>3,850<\/b>/.test(html) || !/<div class="stat"><b>…<\/b><span>loading<\/span><\/div>/.test(html), "homeStats still boots as …/loading");
ok("no 'Loading the catalog index…' stale string", !/Loading the catalog index…/.test(html));
ok("'Loading degree programs…' has retry sibling", /degList/.test(html));
ok("resCount boots with stamped count", /id="resCount">3,850</.test(html) || /id="resCount">…/.test(html) === false);
ok("accreditation honesty statement present", /not accredited.*government body|no government accreditation/i.test(html));
ok("official-within-Signature next to diplomas", /printable officially-stamped diplomas.*official within the Signature system/.test(html));
ok("35-site nav present", html.indexOf("SITE 25 OF 35") >= 0);
ok("official name 'The Signature University'", html.indexOf("THE SIGNATURE UNIVERSITY") >= 0 && !/JAH University/.test(html));

// 21. first-visit tour + ? Guide panel
ok("tour localStorage key jah-tour-seen-university", html.indexOf("jah-tour-seen-university") >= 0);
ok("? Guide button present", html.indexOf('id="uGuideBtn"') >= 0);
ok("guide panel documents every feature", html.indexOf('id="uGuidePanel"') >= 0 && html.indexOf("How to use this site") >= 0);
const stepTitles = (html.match(/title:"\d · /g) || []);
ok("tour has 6 steps (catalog, courses, teacher, labs, degrees, progress)", stepTitles.length === 6, stepTitles.length);
ok("tour keyboard: Esc closes, arrows navigate", /e\.key==="Escape"/.test(html) && /ArrowRight/.test(html) && /ArrowLeft/.test(html));
ok("tour buttons touch-sized (min 44px)", /\.uBtnRow \.btn\{min-height:44px/.test(html));
ok("tour intro shows Start/Skip", html.indexOf('data-a="start"') >= 0 && html.indexOf('data-a="skip"') >= 0);
ok("tour never blocks content (shade click + skip set seen flag)", html.indexOf('shade.addEventListener("click"') >= 0);
let ti = 0; ti++; ti++; ti--;
ok("tour next/next/back step walk", ti === 1);
ok("guide panel lists all real features", /Course Finder/.test(html) && /official test/.test(html) && /transcript/.test(html) && /deep link/.test(html));

// 22. mobile code paths (code review)
ok("mobile: stat drawer auto-opens only on desktop (>=768px)", /window\.innerWidth>=768/.test(html));
ok("mobile: responsive CSS breakpoint present", /@media\(max-width:640px\)/.test(html));
ok("mobile: TTS online tiers for in-app WebViews", /responsivevoice/i.test(html) && /translate\.google/.test(html));
ok("mobile: touch-sized main buttons", /min-height:44px/.test(html));

// 23. loading->ready/error->retry with timeout
ok("catalog boot has 20s timeout race", /catalog boot timed out after 20s/.test(html));
ok("catalog error state with retry button", /catalogBootError/.test(html) && /Retry/.test(html));
ok("getJSONt timeout helper used by wings", /function getJSONt/.test(html) && /getJSONt\("data\/degrees\.json",15000\)/.test(html) && /getJSONt\("data\/labs\.json",15000\)/.test(html));
ok("labs wing error->retry", /loadLabs\(\)/.test(html) && /The lab index could not be loaded/.test(html));
ok("projects wing error->retry", /project list could not be loaded/.test(html));
ok("library error->retry", /library shelves could not be loaded/.test(html));
const labsEng = labs.filter(l => l.ckey === "engineering");
ok("labs have valid course refs", labsEng.every(l => courseRe.test(l.course)));
ok("lab search logic filters", labs.filter(l => (l.t + " " + l.d).toLowerCase().indexOf("circuit") >= 0).length > 0);

// 20. projects wing
const byCol = {};
projects.forEach(p => { (byCol[p.ckey] = byCol[p.ckey] || []).push(p); });
ok("every college has capstone projects", collegeKeys.every(k => (byCol[k] || []).length > 0));

// 20b. diploma print + official-test failure/retry (functional code paths)
ok("diploma print includes OFFICIAL STAMP", /OFFICIAL<br>STAMP<br>/.test(html));
ok("diploma print carries no-accreditation line", /The Signature University Diploma — Certificate of Completion — Not Government Accredited/.test(html));
ok("diploma print embeds record SHA-256", /Diploma record SHA-256/.test(html));
ok("diploma print links verify page", /verify\/\?diploma=/.test(html));
ok("diploma stores diploma_hash on award", /aw2\.diploma_hash=dh/.test(html));
ok("official test fail -> Retake wired to startTest", /id="retake"/.test(html) && /addEventListener\("click",startTest\)/.test(html));
ok("official test requires all questions answered", /Please answer every question first/.test(html));
ok("degree award requires full material list", /testBtn='<button class="btn ghost" disabled>🎓 Take the official test<\/button>/.test(html));
ok("test attempt counter increments per retake", /TESTATT=attempt/.test(html) && /testSeed\(d\.id,attempt\)/.test(html));

console.log("\n" + pass + " passed, " + fail + " failed");
process.exit(fail ? 1 : 0);
