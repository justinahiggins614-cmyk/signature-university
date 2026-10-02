"use strict";
/* Degree-flow logic for Signature University — pure functions, no DOM.
   Browser: window.DegFlow. Node: module.exports (used by the harness test). */
var DegFlow = (function () {
  function numOf(id) { var m = /(\d+)$/.exec(id || ""); return m ? parseInt(m[1], 10) : 0; }

  /* The degree's fixed curriculum: the first `need` index rows for the
     degree's college at/above min_level, ordered by course number.
     Deterministic and stable across drip runs (the generator is append-only). */
  function curriculum(idxRows, deg) {
    var pool = idxRows.filter(function (r) { return r.k === deg.ckey && r.l >= deg.min_level; });
    pool.sort(function (a, b) { return numOf(a.i) - numOf(b.i); });
    return pool.slice(0, deg.need);
  }

  function hash32(s) {
    var h = 5381;
    for (var i = 0; i < s.length; i++) h = ((h << 5) + h + s.charCodeAt(i)) >>> 0;
    return h;
  }
  function mulberry32(a) {
    return function () {
      a |= 0; a = (a + 0x6D2B79F5) | 0;
      var t = Math.imul(a ^ (a >>> 15), 1 | a);
      t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
      return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    };
  }
  function testSeed(degId, attempt) { return hash32(degId + "|attempt|" + attempt); }

  function shuffled(arr, rnd) {
    var a = arr.slice(), i, j, t;
    for (i = a.length - 1; i > 0; i--) { j = Math.floor(rnd() * (i + 1)); t = a[i]; a[i] = a[j]; a[j] = t; }
    return a;
  }
  function pickN(arr, n, rnd) { return shuffled(arr, rnd).slice(0, n); }
  function courseLabel(c) { return c.code + " \u2014 " + c.title; }

  function makeQ(b, courses, rnd) {
    var others = courses.filter(function (x) { return x.id !== b.c.id; });
    if (others.length < 3) return null;
    var distract = pickN(others, 3, rnd), opts, ans, vals, keys;
    if (b.t === "lesson") {
      ans = courseLabel(b.c);
      opts = distract.map(courseLabel).concat([ans]);
      return { q: "Which course teaches the lesson \u201C" + b.text + "\u201D?", opts: shuffled(opts, rnd), answer: ans };
    }
    if (b.t === "module") {
      ans = courseLabel(b.c);
      opts = distract.map(courseLabel).concat([ans]);
      return { q: "Which course has a module called \u201C" + b.text + "\u201D?", opts: shuffled(opts, rnd), answer: ans };
    }
    if (b.t === "reading") {
      ans = courseLabel(b.c);
      opts = distract.map(courseLabel).concat([ans]);
      return { q: "The reading \u201C" + b.text + "\u201D appears in which course?", opts: shuffled(opts, rnd), answer: ans };
    }
    if (b.t === "credits") {
      vals = {}; courses.forEach(function (x) { vals[String(x.credits)] = 1; });
      keys = Object.keys(vals).filter(function (v) { return v !== b.text; });
      if (!keys.length) return null;
      opts = pickN(keys, Math.min(3, keys.length), rnd).concat([b.text]);
      ans = b.text + " credits";
      return {
        q: "How many credits is " + b.c.code + " (" + b.c.title + ")?",
        opts: shuffled(opts, rnd).map(function (v) { return v + " credits"; }),
        answer: ans
      };
    }
    if (b.t === "level") {
      vals = {}; courses.forEach(function (x) { vals[String(x.level)] = 1; });
      keys = Object.keys(vals).filter(function (v) { return v !== b.text; });
      if (!keys.length) return null;
      opts = pickN(keys, Math.min(3, keys.length), rnd).concat([b.text]);
      ans = "Level " + b.text;
      return {
        q: "What level is " + b.c.code + " (" + b.c.title + ")?",
        opts: shuffled(opts, rnd).map(function (v) { return "Level " + v; }),
        answer: ans
      };
    }
    return null;
  }

  /* Build up to n multiple-choice questions from full course records.
     courseRecords: [{id, code, title, level, credits, modules:[{m, lessons:[]}], readings:[{label}]}] */
  function buildTest(courseRecords, seed, n) {
    n = n || 10;
    var rnd = mulberry32(seed), qs = [], used = {}, bank = [], order, i, b, q;
    courseRecords.forEach(function (c) {
      (c.modules || []).forEach(function (m) {
        (m.lessons || []).forEach(function (l) { bank.push({ t: "lesson", c: c, text: l, mod: m.m }); });
        bank.push({ t: "module", c: c, text: m.m });
      });
      (c.readings || []).forEach(function (r) { bank.push({ t: "reading", c: c, text: r.label }); });
      bank.push({ t: "credits", c: c, text: String(c.credits) });
      bank.push({ t: "level", c: c, text: String(c.level) });
    });
    order = shuffled(bank, rnd);
    for (i = 0; i < order.length && qs.length < n; i++) {
      b = order[i];
      var key = b.t + "|" + b.text;
      if (used[key]) continue;
      used[key] = 1;
      q = makeQ(b, courseRecords, rnd);
      if (q) qs.push(q);
    }
    return qs;
  }

  function gradeTest(questions, answers) {
    var score = 0;
    questions.forEach(function (q, i) { if (answers[i] === q.answer) score++; });
    return { score: score, total: questions.length, passed: questions.length > 0 && score / questions.length >= 0.7 };
  }

  /* Official stamped degree ID: JAH-DEGREE-###### (distinct from the
     JAH-DIPLOMA-###### print stamp; the diploma stays as-is). */
  function degreeStamp(name, degId, dateStr) {
    var h = hash32(String(name || "") + "|" + degId + "|" + String(dateStr || ""));
    return "JAH-DEGREE-" + String(h % 900000 + 100000);
  }

  return {
    curriculum: curriculum,
    buildTest: buildTest,
    gradeTest: gradeTest,
    degreeStamp: degreeStamp,
    testSeed: testSeed,
    hash32: hash32
  };
})();
if (typeof module !== "undefined" && module.exports) module.exports = DegFlow;
if (typeof window !== "undefined") window.DegFlow = DegFlow;
