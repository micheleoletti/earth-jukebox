// HARMONY LAYER (Nature mode only): a soft, low four-voice chord on top of the recordings.
// "Harmony expresses balance. Dissonance reveals change."
//   root    = D2, always.
//   main    = a chord tone (D3, the third, or A3) picked by where the main signal sits in its lane (main 0..1).
//   partner = a consonant interval above the main voice (fifth if in the scale, else third, else octave). As the rolling
//             link between the two signals falls from 0.7 to 0.3 (the chart thread's range) it crossfades into a
//             half-step rub against the main voice, detuned 8 to 15 cents; it slides back as the link returns.
//   tension = the scale's unstable note, a half-step from a chord tone; its loudness follows how far the main signal is
//             from normal (tension 0..1). null = this story has no normal band: the voice stays silent.
// Every voice is two detuned saws plus a triangle through a lowpass (about 700 to 1200 Hz); all pitches D2..D4 (MIDI 38..62).
// Nothing jumps: every change is a setTargetAtTime ramp with a time constant of at least 0.8 s.
//
// API (window.Harmony):
//   start(ctx, dest)  create the voices (silent) and connect to dest. Safe to call twice.
//   setScale(scale)   semitone offsets from D, e.g. [0,1,3,5,7,8,10]. Pitches glide to the new chord.
//   set({main, links, tension})  main 0..1; links = array of link strengths 0..1, one per chart connection (each one is
//                     its own voice in the mid-high range: 1st a fifth, 2nd a third, 3rd a ninth or sixth, 4th an octave
//                     above the main voice, each sliding into a half-step rub when its link is weak); `link` (one number)
//                     still works; tension 0..1 or null. Non-finite main/link hold the last value;
//                     non-finite tension eases to 0. Call every ~120 ms.
//   swell()           lock-in moment: the chord swells slightly and opens a little, then settles back (about 6 s).
//   setOn(on)         fade the whole layer in or out (about 3 s). Starts off.
(function(){
  const D2 = 38, D3 = 50, TOP = 62;
  const OUT = .32;                  // output level when on (raised: the chord was too quiet under the nature sounds)
  const TC_PITCH = 1.6, TC_GAIN = 1.5, TC_TENSION = 2, TC_ON = 1, TC_FILTER = 2;
  const TC_LINK = .22;   // connection voices snap into (and out of) tune fast: quick audible feedback (about 0.6 s to settle)
  const LEVEL = {root:.17, main:.18, partner:.24, tension:.2};   // base (root + main) lowered: the connection voices lead
  const MAXL = 4, LINK_LO = 62, LINK_HI = 81;   // link voices live in D4..A5
  const CUT = {root:700, main:1000, partner:1000, tension:850};
  const clamp01 = x => Math.max(0, Math.min(1, x));
  const hz = m => 440 * Math.pow(2, (m - 69) / 12);
  const pc = m => ((m % 12) + 12) % 12;

  const H = {ctx:null, out:null, on:false, scale:[0, 2, 4, 7, 9], v:{},
    main:.5, link:1, links:[1], tension:0, mainIdx:1, swellUntil:0, lv:[]};

  // one voice: osc bank(s) -> lowpass -> gain. A bank = 2 detuned saws + 1 triangle at one pitch.
  function bank(ctx, into, m){
    const g = ctx.createGain(); g.gain.value = 0; g.connect(into);
    const oscs = [['triangle', 0, .9]].map(([type, cents, lv]) => {   // one clean note per bank (no detuned ensemble)
      const o = ctx.createOscillator(), og = ctx.createGain();
      o.type = type; o.frequency.value = hz(m); o.detune.value = cents; og.gain.value = lv;
      o.connect(og); og.connect(g); o.start(); return o;
    });
    return {g, oscs, base:[0]};
  }
  function voice(ctx, into, m, cut, banks = 1){
    const lp = ctx.createBiquadFilter(), g = ctx.createGain();
    lp.type = 'lowpass'; lp.frequency.value = cut; lp.Q.value = .4; g.gain.value = 0;
    lp.connect(g); g.connect(into);
    // very slow breathing of the level so the pad is never static (depth 12 %)
    const lfo = ctx.createOscillator(), lg = ctx.createGain(); lfo.frequency.value = .05 + Math.random() * .04; lg.gain.value = 0;
    lfo.connect(lg); lg.connect(g.gain); lfo.start();
    const bs = []; for (let i = 0; i < banks; i++) bs.push(bank(ctx, lp, m));
    return {lp, g, lg, banks:bs, cut};
  }
  const glide = (b, m, now, tc = TC_PITCH) => b.oscs.forEach(o => o.frequency.setTargetAtTime(hz(m), now, tc));
  const detune = (b, extra, now, tc = TC_PITCH) => b.oscs.forEach((o, i) => o.detune.setTargetAtTime(b.base[i] + extra, now, tc));
  const level = (v, x, now, tc = TC_GAIN) => { v.g.gain.setTargetAtTime(x, now, tc); v.lg.gain.setTargetAtTime(x * .12, now, tc); };

  // chord tones from the scale: root, third (minor or major if present, else the scale's next colour note), fifth
  // every chord note is a tone of the D major triad, counted from the ROOT (never from another voice): 1st, 3rd, 5th
  H.chord = function(){ return [0, 4, 7]; };
  // the three main-voice pitches, D3..A3 region
  H.mainNotes = function(){ return this.chord().map(x => D3 + x); };
  // consonant partner above the main voice, kept at or below D4 (inverted an octave down if it would go above)
  H.partnerFor = function(m){
    const s = this.scale, r = pc(m - D2);
    const iv = [7, ...[4, 3].filter(i => s.includes(pc(r + i))), 12].find(i => i === 12 || s.includes(pc(r + i)));
    let p = m + iv; if (p > TOP) p -= 12; if (p === m) p = m + 12 > TOP ? m - 12 : m + 12;
    return p;
  };
  // tension: a scale note a half-step from a chord tone (prefer near the main voice, then above the fifth);
  // if the scale has none (pentatonic scales), the chromatic half-step above the fifth: a soft rub, not a cluster
  // the k-th connection's voice: a chord colour above the main voice (fifth, third, ninth or sixth, octave), in D4..A5
  H.linkFor = function(m, k){
    const s = this.scale, r = pc(m - D2);
    // in tune (correlated) = only pure, positive intervals above the main voice: 1st connection a fifth, 2nd a major third, 3rd an
    // octave, 4th the fifth above; not correlated = unchanged, the voice slides into its half-step rub (apply())
    const p = [66, 69, 74, 78][k % 4];   // F#4 (3rd), A4 (5th), D5 (octave), F#5 (10th): chord tones of D, from the root
    return p;
  };
  H.tensionFor = function(m){
    const s = this.scale, ch = this.chord(), mr = pc(m - D2);
    const cands = s.filter(x => !ch.includes(x) && ch.some(c => Math.abs(x - c) === 1 || Math.abs(x - c) === 11));
    const near = c => cands.find(x => Math.abs(x - c) === 1 || Math.abs(x - c) === 11);
    let t = near(mr) ?? near(ch[2]) ?? cands[0];
    if (t === undefined) t = pc(ch[2] + 1);
    // place it in D3..D4, close to the main voice
    let p = D3 + t; if (Math.abs(p - m) > 6) p += p < m ? 12 : -12; if (p > TOP) p -= 12; if (p < D3) p += 12;
    return p;
  };

  H.start = function(ctx, dest){
    if (this.ctx) return;
    this.ctx = ctx;
    this.out = ctx.createGain(); this.out.gain.value = 0; this.out.connect(dest);
    const ns = this.mainNotes(), m = ns[this.mainIdx];
    this.v.root = voice(ctx, this.out, D2, CUT.root);
    this.v.main = voice(ctx, this.out, ns[0], CUT.main, 3); this.v.main.banks.forEach((b, i) => { b.oscs.forEach(o => o.frequency.value = hz(ns[i])); b.g.gain.value = i === this.mainIdx ? 1 : 0; });
    this.v.partner = voice(ctx, this.out, this.partnerFor(m), CUT.partner, 2);   // bank 0 consonant, bank 1 rub
    glide(this.v.partner.banks[1], m + 1, ctx.currentTime, .01);
    this.v.tension = voice(ctx, this.out, this.tensionFor(m), CUT.tension);
    for (let k = 0; k < MAXL; k++){ const lv = voice(ctx, this.out, this.linkFor(m, k), 1400, 1); lv.banks[0].g.gain.value = 0; this.lv.push(lv); }
    this.v.root.banks[0].g.gain.value = 1; this.v.tension.banks[0].g.gain.value = 1;
    this.v.partner.banks[0].g.gain.value = 1;
    this.apply(true);
    this.setOn(this.on);
  };

  H.setScale = function(scale){
    if (Array.isArray(scale) && scale.length >= 3) this.scale = scale.map(x => pc(Math.round(x))).filter((x, i, a) => a.indexOf(x) === i).sort((a, b) => a - b);
    if (!this.scale.includes(0)) this.scale.unshift(0);
    this.apply();
  };

  H.set = function(o){
    o = o || {};
    if (Number.isFinite(o.main)) this.main = clamp01(o.main);
    if (Array.isArray(o.links)) this.links = o.links.slice(0, MAXL).map((x, i) => Number.isFinite(x) ? clamp01(x) : (this.links[i] ?? 1));
    else if (Number.isFinite(o.link)) this.links = [clamp01(o.link)];
    // moves: per connection, how much the two lines move together right now (0..1); the voice's volume breathes with it
    this.moves = Array.isArray(o.moves) ? o.moves.slice(0, MAXL).map(x => Number.isFinite(x) ? clamp01(x) : 0) : this.moves || [];
    this.link = this.links.length ? this.links[0] : 1;
    this.tension = Number.isFinite(o.tension) ? clamp01(o.tension) : 0;   // null / gap: ease to silence
    this.apply();
  };

  H.apply = function(init){
    const ctx = this.ctx; if (!ctx) return;
    const now = ctx.currentTime, v = this.v, ns = this.mainNotes();
    // main voice index with hysteresis so it does not flip between two notes on a noisy signal
    const n = ns.length, pos = this.main * (n - 1), cur = this.mainIdx;
    if (init || Math.abs(pos - cur) > .62) this.mainIdx = Math.max(0, Math.min(n - 1, Math.round(pos)));
    const m = ns[this.mainIdx];
    v.main.banks.forEach((b, i) => b.g.gain.setTargetAtTime(i === this.mainIdx ? 1 : 0, now, .35));   // fade between fixed notes, no glide
    // one voice per chart connection: consonant bank vs half-step rub bank, crossfaded by how weak that link is (0.7 -> 0.3)
    const nl = this.links.length;
    this.lv.forEach((lv, k) => {
      // correlated = this voice sounds (stacked consonant note); not correlated = it fades out. Always pleasant, no rub.
      const on = k < nl, w = on ? clamp01((this.links[k] - .3) / .4) : 0, p = this.linkFor(m, k), b = lv.banks;
      const mv = this.moves && this.moves[k] != null ? this.moves[k] : 1, breathe = .35 + .65 * mv;   // soft floor, swells while moving together
      const tgt = w * w * (3 - 2 * w) * breathe, rising = tgt > b[0].g.gain.value + .01;
      b[0].g.gain.setTargetAtTime(tgt, now, rising ? .08 : .5);   // fast entry on a correlation, decay unchanged
      { const lvl = on ? .6 / Math.sqrt(Math.max(1, nl)) * (now < this.swellUntil ? 1.3 : 1) : 0; level(lv, lvl, now, lvl > lv.g.gain.value + .005 ? .12 : TC_GAIN); }   // louder connection voices, fast entry
      lv.lp.frequency.setTargetAtTime(2200, now, TC_FILTER);   // a bit brighter so the connection notes stand out
    });
    // tension voice
    { const tf = hz(this.tensionFor(ns[0])); v.tension.banks[0].oscs.forEach(o => { if (Math.abs(o.frequency.value - tf) > .5) o.frequency.setValueAtTime(tf, now); }); }   // fixed per story scale: jumps (it is silent unless tense), never glides
    const swelling = now < this.swellUntil ? 1.3 : 1;
    // the base (root + main) sits low while nothing is correlated and the whole ensemble lifts when a connection comes in
    const corr = this.links.length ? Math.max(...this.links.map(x => clamp01((x - .3) / .4))) : 0, lift = .4 + .6 * corr;
    const up = x => x > v.root.g.gain.value + .005;
    level(v.root, LEVEL.root * swelling * lift, now, up(LEVEL.root * swelling * lift) ? .15 : TC_GAIN);
    level(v.main, LEVEL.main * swelling * lift, now, LEVEL.main * swelling * lift > v.main.g.gain.value + .005 ? .15 : TC_GAIN);
    level(v.partner, 0, now);   // the single partner voice is replaced by one voice per connection (this.lv)
    level(v.tension, LEVEL.tension * Math.sqrt(this.tension), now, TC_TENSION);
    for (const k in v) v[k].lp.frequency.setTargetAtTime(v[k].cut * (swelling > 1 ? 1.2 : 1) * (k === 'tension' ? 1 + .3 * this.tension : 1), now, TC_FILTER);
  };

  // lock-in: swell for ~2.5 s (ramping in over ~1 s), then the next apply() lets it settle back over a few seconds
  H.swell = function(){
    const ctx = this.ctx; if (!ctx) return;
    this.swellUntil = ctx.currentTime + 2.5;
    this.apply();
    clearTimeout(this.swellTimer); this.swellTimer = setTimeout(() => this.apply(), 2600);
  };

  H.setOn = function(on){
    this.on = !!on;
    if (this.out) this.out.gain.setTargetAtTime(this.on ? OUT : 0, this.ctx.currentTime, TC_ON);
  };

  window.Harmony = H;
})();
