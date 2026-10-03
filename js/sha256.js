"use strict";
/* SHA-256 for Signature University — compact public-domain-style implementation.
   UTF-8 safe (input is UTF-8 encoded first). Exposes window.sha256hex(str).
   Used for diploma content hashes and transcript hashes. */
(function () {
  function rr(v, a) { return (v >>> a) | (v << (32 - a)); }

  function sha256(ascii) {
    var maxWord = Math.pow(2, 32), result = "";
    var words = [], asciiBitLength = ascii.length * 8;
    var hash = sha256.h = sha256.h || [], k = sha256.k = sha256.k || [];
    var primeCounter = k.length, isComposite = {};
    for (var candidate = 2; primeCounter < 64; candidate++) {
      if (!isComposite[candidate]) {
        for (var i = 0; i < 313; i += candidate) isComposite[i] = candidate;
        hash[primeCounter] = (Math.pow(candidate, 0.5) * maxWord) | 0;
        k[primeCounter++] = (Math.pow(candidate, 1 / 3) * maxWord) | 0;
      }
    }
    ascii += "\x80";
    while (ascii.length % 64 - 56) ascii += "\x00";
    for (var i = 0; i < ascii.length; i++) {
      var j = ascii.charCodeAt(i);
      if (j >> 8) return "";
      words[i >> 2] |= j << ((3 - i) % 4) * 8;
    }
    words[words.length] = (asciiBitLength / maxWord) | 0;
    words[words.length] = asciiBitLength;
    for (var j = 0; j < words.length;) {
      var w = words.slice(j, j += 16), oldHash = hash;
      hash = hash.slice(0, 8);
      for (var i = 0; i < 64; i++) {
        var w15 = w[i - 15], w2 = w[i - 2];
        var a = hash[0], e = hash[4];
        var temp1 = hash[7]
          + (rr(e, 6) ^ rr(e, 11) ^ rr(e, 25))
          + ((e & hash[5]) ^ ((~e) & hash[6]))
          + k[i]
          + (w[i] = (i < 16) ? w[i] : (
            w[i - 16]
            + (rr(w15, 7) ^ rr(w15, 18) ^ (w15 >>> 3))
            + w[i - 7]
            + (rr(w2, 17) ^ rr(w2, 19) ^ (w2 >>> 10))
          ) | 0);
        var temp2 = (rr(a, 2) ^ rr(a, 13) ^ rr(a, 22))
          + ((a & hash[1]) ^ (a & hash[2]) ^ (hash[1] & hash[2]));
        hash = [(temp1 + temp2) | 0].concat(hash);
        hash[4] = (hash[4] + temp1) | 0;
      }
      for (var i = 0; i < 8; i++) hash[i] = (hash[i] + oldHash[i]) | 0;
    }
    for (var i = 0; i < 8; i++) {
      for (var j = 3; j + 1; j--) {
        var b = (hash[i] >> (j * 8)) & 255;
        result += ((b < 16) ? "0" : "") + b.toString(16);
      }
    }
    return result;
  }

  function sha256hex(str) {
    // Encode to UTF-8 bytes presented as a binary string, then hash as ASCII.
    var utf8 = unescape(encodeURIComponent(str));
    return sha256(utf8);
  }

  if (typeof window !== "undefined") window.sha256hex = sha256hex;
  if (typeof module !== "undefined" && module.exports) module.exports = sha256hex;
})();
