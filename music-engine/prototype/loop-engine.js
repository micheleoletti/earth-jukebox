// Loop engine: renders one 8-bar cinematic loop (D, 96 BPM) at a fixed intensity with OfflineAudioContext.
// Same loop, 5 intensities -> 5 bounces that line up sample for sample, so a player can crossfade them.
// No DAW: everything is synthesized here except the taiko hits (Pixabay samples).
window.LoopEngine = (() => {
  const BPM = 96, STEP = 60 / BPM / 4, BARS = 8, STEPS = BARS * 16, LOOP = STEPS * STEP; // 20 s
  const mtof = m => 440 * Math.pow(2, (m - 69) / 12);
  const at5 = (a, x) => { const p = x * 4, i = Math.min(3, Math.floor(p)), f = p - i; return a[i] + (a[i + 1] - a[i]) * f; };
  const rng = seed => () => { seed |= 0; seed = seed + 0x6D2B79F5 | 0; let t = Math.imul(seed ^ seed >>> 15, 1 | seed); t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296; };

  // taikoStem: optional AudioBuffer rendered by tools/render_taiko.py (Kontakt, Thunder X3M), 3 cycles long,
  // same grid. When given it replaces the sample-based taiko hits.
  // parts: 'all' (default), 'nobeds' (no pad/saw/air drones), 'beds' (only them), 'taiko' (only the taiko stem: no synthesized sound at all)
  // only: render a single synth layer as its own stem ('sub','ost','thump','brass','braam','riser','chime','pad',
  // 'shimmer','glass','bells','arp','pluck','sparkle','trumpet'), at its loudest level
  async function render({ x, taikoBig, taikoHit, taikoStem, parts = 'all', only = null, sr = 48000, cycles = 3 }) {
    const L = Math.round(LOOP * sr);
    const ctx = new OfflineAudioContext(2, L * cycles, sr);
    const R = rng(1234);                       // same seed for every intensity: shared randomness
    const noiseBuf = (() => { const b = ctx.createBuffer(1, sr * 4, sr), d = b.getChannelData(0); const r = rng(99); for (let i = 0; i < d.length; i++) d[i] = (r() * 2 - 1) * 0.5; return b; })();

    // --- master + buses
    const master = ctx.createGain(); master.gain.value = 0.8;
    const comp = ctx.createDynamicsCompressor(); comp.threshold.value = -16; comp.knee.value = 10; comp.ratio.value = 3; comp.attack.value = 0.012; comp.release.value = 0.25;
    const lim = ctx.createDynamicsCompressor(); lim.threshold.value = -2; lim.knee.value = 0; lim.ratio.value = 20; lim.attack.value = 0.002; lim.release.value = 0.12;
    master.connect(comp); comp.connect(lim); lim.connect(ctx.destination);
    const revIn = ctx.createGain();
    { const hp = ctx.createBiquadFilter(); hp.type = 'highpass'; hp.frequency.value = 150;
      const conv = ctx.createConvolver(); const len = sr * 3.6, ir = ctx.createBuffer(2, len, sr); const r = rng(7);
      for (let c = 0; c < 2; c++) { const d = ir.getChannelData(c); for (let i = 0; i < len; i++) d[i] = (r() * 2 - 1) * Math.pow(1 - i / len, 2.3); }
      conv.buffer = ir; const out = ctx.createGain(); out.gain.value = 0.75;
      revIn.connect(hp); hp.connect(conv); conv.connect(out); out.connect(master); }

    // --- helpers
    const chan = (gain, { rev = 0, pan = 0 } = {}) => {
      const g = ctx.createGain(); g.gain.value = gain; const p = ctx.createStereoPanner(); p.pan.value = pan;
      g.connect(p); p.connect(master); if (rev) { const s = ctx.createGain(); s.gain.value = rev; p.connect(s); s.connect(revIn); } return g;
    };
    const osc = (type, f, t, dur, dest, detune = 0) => { const o = ctx.createOscillator(); o.type = type; o.frequency.setValueAtTime(f, t); o.detune.value = detune; o.connect(dest); o.start(t); o.stop(t + dur); return o; };
    const vca = (dest, t, peak, a, d) => { const g = ctx.createGain(); g.gain.setValueAtTime(0.0001, t); g.gain.exponentialRampToValueAtTime(Math.max(peak, 0.0002), t + a); g.gain.exponentialRampToValueAtTime(0.0001, t + a + d); g.connect(dest); return g; };
    const filt = (type, f, q, dest) => { const b = ctx.createBiquadFilter(); b.type = type; b.frequency.value = f; b.Q.value = q; b.connect(dest); return b; };
    const lfo = (rate, depth, param) => { const o = ctx.createOscillator(); o.frequency.value = rate; const g = ctx.createGain(); g.gain.value = depth; o.connect(g); g.connect(param); o.start(0); };
    const drone = (type, f, gain, dest, detune = 0) => { const o = ctx.createOscillator(); o.type = type; o.frequency.value = f; o.detune.value = detune; const g = ctx.createGain(); g.gain.value = gain; o.connect(g); g.connect(dest); o.start(0); };
    const shaper = amt => { const ws = ctx.createWaveShaper(), n = 1024, c = new Float32Array(n); for (let i = 0; i < n; i++) { const v = i / (n - 1) * 2 - 1; c[i] = Math.tanh(amt * v) / Math.tanh(amt); } ws.curve = c; return ws; };
    const sample = (buf, dest, t, v, rate = 1) => { const s = ctx.createBufferSource(); s.buffer = buf; s.playbackRate.value = rate; const g = ctx.createGain(); g.gain.value = v; s.connect(g); g.connect(dest); s.start(t); };
    // LFO rates are whole multiples of 1/LOOP (0.05 Hz) so slow movement repeats exactly every loop.
    const F = n => n / LOOP;

    // --- layers (gain at 5 intensity points: 0, .25, .5, .75, 1)
    const lv = a => at5(a, x);
    let bedOn = (parts === 'all' || parts === 'beds') ? 1 : 0, pulseOn = parts !== 'beds' ? 1 : 0, synthOn = (parts === 'all' || parts === 'nobeds') ? 1 : 0;
    if (only) { bedOn = only === 'pad' ? 1 : 0; synthOn = only === 'pad' ? 0 : 1; pulseOn = 0; }
    const G = (name, v, max) => only ? (only === name ? max : 0) : v;   // layer gain
    // beds
    const sub = chan(G('sub', synthOn * lv([0.55, 0.55, 0.6, 0.6, 0.65]), 0.6));
    drone('sine', mtof(26), 0.7, sub); drone('sine', mtof(38), 0.4, sub);
    const saw = chan(bedOn * lv([0.3, 0.35, 0.42, 0.5, 0.55]), { rev: 0.4 });
    const sawLP = filt('lowpass', 250 + x * 1100, 3, saw); lfo(F(1), 80, sawLP.frequency);
    [38, 45, 50].forEach(m => [-8, 8].forEach(dt => drone('sawtooth', mtof(m), 0.06, sawLP, dt)));
    const pad = chan(bedOn * lv([0.3, 0.3, 0.24, 0.16, 0.1]), { rev: 0.6 });
    const padLP = filt('lowpass', 900, 0.7, pad); lfo(F(2), 300, padLP.frequency);
    [50, 57, 62, 69].forEach(m => [-6, 6].forEach(dt => drone('sawtooth', mtof(m), 0.035, padLP, dt)));
    const air = chan(bedOn * lv([0.28, 0.2, 0.12, 0.06, 0.03]), { rev: 0.8 });
    { const trem = ctx.createGain(); trem.gain.value = 0.5; trem.connect(air); lfo(F(4), 0.4, trem.gain); drone('sine', mtof(86), 0.05, trem); drone('sine', mtof(93), 0.035, trem); }
    // pulses
    const chimeC = chan(G('chime', synthOn * lv([0.35, 0.25, 0.1, 0, 0]), 0.35), { rev: 0.7 });
    const ostC = chan(G('ost', synthOn * lv([0, 0.35, 0.5, 0.6, 0.7]), 0.6), { rev: 0.25, pan: -0.15 });
    const thumpC = chan(G('thump', synthOn * lv([0, 0.5, 0.55, 0.35, 0.25]), 0.55), { rev: 0.2 });
    const taikoC = taikoStem ? chan(1.7 * lv([0, 0.9, 0.95, 1, 1]), { rev: synthOn ? 0.08 : 0 }) /* taiko-only: Thunder X3M's own hall mic, no added reverb */ : chan(lv([0, 0, 0.75, 0.9, 1]), { rev: 0.3 });
    if (taikoStem && pulseOn && !only) sample(taikoStem, taikoC, 0, 1);
    const brassC = chan(G('brass', synthOn * lv([0, 0, 0, 0.35, 0.6]), 0.6), { rev: 0.4, pan: 0.15 });
    const braamC = chan(G('braam', synthOn * lv([0, 0, 0, 0.4, 0.6]), 0.6), { rev: 0.5 });
    const riserC = chan(G('riser', synthOn * (x >= 0.99 ? 0.45 : 0), 0.45), { rev: 0.3 });

    // --- voices
    const chime = (t, m, v) => { const f = mtof(m); [[1, 1, 3], [2, 0.45, 2.2], [3.01, 0.25, 1.4], [4.17, 0.16, 1]].forEach(([r, a, dec]) => osc('sine', f * r, t, dec + 0.1, vca(chimeC, t, 0.16 * v * a, 0.002, dec))); };
    const ost = (t, m, v, cut) => { const g = vca(ostC, t, 0.2 * v, 0.003, 0.17); const lp = filt('lowpass', cut, 5, g); lp.frequency.setValueAtTime(cut * 2.5, t); lp.frequency.exponentialRampToValueAtTime(cut, t + 0.12); osc('sawtooth', mtof(m), t, 0.22, lp, -6); osc('sawtooth', mtof(m), t, 0.22, lp, 6); };
    const thump = (t, v) => { const o = osc('sine', 75, t, 0.5, vca(thumpC, t, 0.8 * v, 0.003, 0.45)); o.frequency.exponentialRampToValueAtTime(42, t + 0.2); };
    const taiko = (t, v, big) => {
      const jitter = t > 0.01 ? (R() - 0.5) * 0.01 : 0;
      if (big) sample(taikoBig, taikoC, t + jitter, 1.05 * v, 0.9);
      else sample(taikoHit, taikoC, t + jitter, 0.9 * v, [1, 1.05, 0.96][Math.floor(R() * 3)] * (v < 0.6 ? 1.1 : 1));
    };
    const stab = (t, v) => { const g = vca(brassC, t, 0.3 * v, 0.006, 0.45); const ws = shaper(2); ws.connect(g); const pre = ctx.createGain(); pre.gain.value = 0.2; pre.connect(ws); const lp = filt('lowpass', 300, 3, pre); lp.frequency.setValueAtTime(300, t); lp.frequency.exponentialRampToValueAtTime(4200, t + 0.03); lp.frequency.exponentialRampToValueAtTime(500, t + 0.4); [50, 57, 62].forEach(m => [-12, 0, 12].forEach(dt => osc('sawtooth', mtof(m), t, 0.55, lp, dt))); };
    const braam = (t, dur) => { const g = ctx.createGain(); g.gain.setValueAtTime(0.0001, t); g.gain.exponentialRampToValueAtTime(0.32, t + 0.12); g.gain.setTargetAtTime(0.0001, t + dur * 0.45, dur * 0.18); g.connect(braamC); const ws = shaper(2.5); ws.connect(g); const pre = ctx.createGain(); pre.gain.value = 0.18; pre.connect(ws); const lp = filt('lowpass', 140, 5, pre); lp.frequency.setValueAtTime(140, t); lp.frequency.exponentialRampToValueAtTime(2200, t + 0.3); lp.frequency.exponentialRampToValueAtTime(260, t + dur); [26, 38, 45, 50].forEach(m => [-9, 0, 9].forEach(dt => osc('sawtooth', mtof(m), t, dur + 0.4, lp, dt))); };
    const riser = (t, dur) => { const g = ctx.createGain(); g.gain.setValueAtTime(0.0001, t); g.gain.exponentialRampToValueAtTime(0.3, t + dur); g.gain.exponentialRampToValueAtTime(0.0001, t + dur + 0.06); g.connect(riserC); const bp = filt('bandpass', 300, 1.5, g); bp.frequency.setValueAtTime(300, t); bp.frequency.exponentialRampToValueAtTime(7000, t + dur); const s = ctx.createBufferSource(); s.buffer = noiseBuf; s.loop = true; s.connect(bp); s.start(t); s.stop(t + dur + 0.1); };

    // --- arrangement
    const ostPat = [50, 50, 62, 50, 50, 62, 50, 57, 50, 50, 62, 50, 50, 62, 57, 50];
    const groove = { 0: 1, 3: 0.45, 6: 0.7, 8: 0.9, 10: 0.4, 11: 0.55, 14: 0.75 };
    const sparse = { 0: 1, 8: 0.8, 14: 0.45 };
    const extra = { 1: 0.3, 4: 0.5, 7: 0.35, 12: 0.5, 15: 0.4 };
    for (let n = 0; synthOn && n < STEPS * cycles; n++) {
      const t = n * STEP, i = n % STEPS, s = i % 16, bar = i / 16 | 0;
      if (lv([0.35, 0.25, 0.1, 0, 0]) > 0 && s === 0 && bar % 4 === 0) chime(t, bar === 0 ? 86 : 81, 1);
      if (x >= 0.24 && (x >= 0.6 || s % 2 === 0)) ost(t, ostPat[s], s % 4 === 0 ? 1 : 0.65, 500 + x * 2000);
      if (x >= 0.24 && (s === 0 || s === 8)) thump(t, s === 0 ? 1 : 0.7);
      if (!only && !taikoStem && x >= 0.49) {
        let v;
        if (x < 0.74) { v = sparse[s]; if (bar % 4 === 3 && s === 12) v = 0.5; }
        else { v = groove[s]; if (x >= 0.99 && !v) v = extra[s]; if (bar % 4 === 3 && s >= 12) v = 0.5 + 0.15 * (s - 12); }
        if (v) taiko(t, v, s === 0 && (bar % 2 === 0 || x >= 0.99));
        if (x >= 0.99 && s === 8) taiko(t, 0.7, true);
      }
      if (x >= 0.74) { if (s === 0 && bar % 2 === 0) stab(t, 1); if (x >= 0.99 && s === 6 && bar % 2 === 1) stab(t, 0.7); if (x >= 0.99 && s === 10) stab(t, 0.45); }
      if (x >= 0.74 && s === 0 && bar % 4 === 0) braam(t, STEP * 32);
      if (x >= 0.99 && i === 7 * 16) riser(t, STEP * 16);
    }

    // ---- higher synth layers + synth trumpets (only rendered as their own stems, for the knob player)
    const HI = only && ['shimmer', 'glass', 'bells', 'arp', 'pluck', 'sparkle', 'trumpet'].includes(only);
    if (HI) {
      const out = chan(1, { rev: only === 'trumpet' ? 0.35 : 0.6 });
      const R2 = rng(4242);
      // dotted-8th echo for the melodic ones
      const echo = ctx.createDelay(2); echo.delayTime.value = STEP * 3;
      const efb = ctx.createGain(); efb.gain.value = 0.35; const elp = filt('lowpass', 3500, 0.7, efb);
      echo.connect(elp); efb.connect(echo); const eout = ctx.createGain(); eout.gain.value = ['arp', 'pluck', 'sparkle'].includes(only) ? 0.45 : 0;
      elp.connect(eout); eout.connect(out);
      const send = node => { node.connect(out); node.connect(echo); };
      const bell = (t, m, v, dec = 4) => {   // FM bell: carrier + inharmonic modulator, index decays (bright strike -> soft tail)
        const f = mtof(m), g = vca(out, t, 0.16 * v, 0.003, dec), c = ctx.createOscillator(), md = ctx.createOscillator(), mg = ctx.createGain();
        c.frequency.value = f; md.frequency.value = f * 3.5; mg.gain.setValueAtTime(f * 2.2, t); mg.gain.exponentialRampToValueAtTime(f * 0.05, t + dec * 0.6);
        md.connect(mg); mg.connect(c.frequency); c.connect(g); c.start(t); md.start(t); c.stop(t + dec + 0.1); md.stop(t + dec + 0.1);
      };
      const mallet = (t, m, v) => { const f = mtof(m), g = ctx.createGain(); send(g);
        osc('sine', f, t, 1.0, vca(g, t, 0.22 * v, 0.002, 0.9)); osc('sine', f * 4, t, 0.12, vca(g, t, 0.06 * v, 0.001, 0.1)); osc('triangle', f * 2, t, 0.4, vca(g, t, 0.05 * v, 0.002, 0.35)); };
      const pluck = (t, m, v) => { const g = ctx.createGain(); send(g); const e = vca(g, t, 0.12 * v, 0.002, 0.28);
        const lp = filt('lowpass', 900, 4, e); lp.frequency.setValueAtTime(5200, t); lp.frequency.exponentialRampToValueAtTime(900, t + 0.18);
        osc('square', mtof(m), t, 0.32, lp, -5); osc('sawtooth', mtof(m), t, 0.32, lp, 5); };
      const ping = (t, m, v) => { const g = ctx.createGain(); send(g); const f = mtof(m);
        const o = osc('sine', f, t, 0.3, vca(g, t, 0.1 * v, 0.001, 0.22)); o.frequency.exponentialRampToValueAtTime(f * 1.004, t + 0.2); };
      const HIGH = [74, 76, 78, 81, 83, 86, 88, 90, 93];   // D major pentatonic, D5..A6
      if (only === 'shimmer') {          // airy high sines with slow tremolo
        const trem = ctx.createGain(); trem.gain.value = 0.5; trem.connect(out); lfo(F(4), 0.4, trem.gain);
        [[86, 0.05], [93, 0.035], [98, 0.02]].forEach(([m, a], i) => { drone('sine', mtof(m), a, trem, i * 3); });
      }
      if (only === 'glass') {            // high glassy pad: detuned triangles on D5 + A5, slow filter breathing
        const lp = filt('lowpass', 2600, 0.8, out); lfo(F(2), 900, lp.frequency);
        [74, 81, 86].forEach(m => [-7, 0, 7].forEach(dt => drone('triangle', mtof(m), 0.035, lp, dt)));
      }
      for (let n = 0; n < STEPS * cycles; n++) {
        const t = n * STEP, i = n % STEPS, s = i % 16, bar = i / 16 | 0;
        if (only === 'bells' && s === 0 && bar % 2 === 0) { bell(t, bar % 4 === 0 ? 86 : 81, 1); bell(t + STEP * 6, 93, 0.5, 3); }
        if (only === 'arp') { const seq = [0, 2, 4, 1, 3, 5, 2, 6, 4, 7, 5, 3, 6, 8, 4, 2]; mallet(t, HIGH[seq[s]], s % 4 === 0 ? 1 : 0.65); }
        if (only === 'pluck') { const pat = { 0: 74, 3: 81, 6: 86, 8: 74, 10: 81, 13: 86, 14: 88 }; if (pat[s]) pluck(t, pat[s], s === 0 ? 1 : 0.7); }
        if (only === 'sparkle' && R2() < 0.22) ping(t, HIGH[3 + Math.floor(R2() * 6)], 0.5 + R2() * 0.5);
      }
      if (only === 'trumpet') {          // synth "trumpet field": many slightly detuned brassy voices drifting in pitch
        const bus = ctx.createGain(); bus.gain.value = 1; const sat = shaper(1.6); bus.connect(sat);
        const lp = filt('lowpass', 1500, 1.2, out); sat.connect(lp); lfo(F(1), 350, lp.frequency);   // slow swell of brightness
        const swell = ctx.createGain(); swell.gain.value = 0.75; swell.connect(bus); lfo(F(2), 0.25, swell.gain);
        [[62, 1], [69, 0.8], [50, 0.5]].forEach(([m, lev]) => {
          for (let k = 0; k < 6; k++) {
            const o = ctx.createOscillator(); o.type = 'sawtooth'; o.frequency.value = mtof(m);
            o.detune.value = (k - 2.5) * 6;                                    // spread like several players
            lfo(F(1 + k), 4 + k * 1.5, o.detune);                             // each player drifts at its own slow rate
            lfo(4.6 + k * 0.37, 3, o.detune);                                  // a little natural vibrato
            const g = ctx.createGain(); g.gain.value = 0.022 * lev; o.connect(g); g.connect(swell); o.start(0);
          }
        });
        const br = ctx.createBufferSource(); br.buffer = noiseBuf; br.loop = true;   // breath
        const bp = filt('bandpass', 1400, 1.4, out); const bg = ctx.createGain(); bg.gain.value = 0.02; br.connect(bg); bg.connect(bp); br.start(0);
      }
    }

    const buf = await ctx.startRendering();
    // Take the middle cycle; crossfade the start with what follows the end, so the loop wraps without a click.
    const xf = Math.round(0.3 * sr), out = new AudioBuffer({ numberOfChannels: 2, length: L, sampleRate: sr });
    for (let c = 0; c < 2; c++) {
      const src = buf.getChannelData(c), dst = out.getChannelData(c);
      for (let k = 0; k < L; k++) dst[k] = src[L + k];
      for (let k = 0; k < xf; k++) { const w = k / xf; dst[k] = src[L + k] * w + src[2 * L + k] * (1 - w); }
    }
    return out;
  }

  function toWav(buf, gain = 1) {
    const ch = buf.numberOfChannels, n = buf.length, sr = buf.sampleRate, bytes = 44 + n * ch * 2, v = new DataView(new ArrayBuffer(bytes));
    const w = (o, s) => [...s].forEach((c, i) => v.setUint8(o + i, c.charCodeAt(0)));
    w(0, 'RIFF'); v.setUint32(4, bytes - 8, true); w(8, 'WAVE'); w(12, 'fmt '); v.setUint32(16, 16, true); v.setUint16(20, 1, true); v.setUint16(22, ch, true);
    v.setUint32(24, sr, true); v.setUint32(28, sr * ch * 2, true); v.setUint16(32, ch * 2, true); v.setUint16(34, 16, true); w(36, 'data'); v.setUint32(40, n * ch * 2, true);
    const data = [...Array(ch)].map((_, c) => buf.getChannelData(c)); let o = 44;
    for (let i = 0; i < n; i++) for (let c = 0; c < ch; c++) { const s = Math.max(-1, Math.min(1, data[c][i] * gain)); v.setInt16(o, s < 0 ? s * 0x8000 : s * 0x7fff, true); o += 2; }
    return v.buffer;
  }

  return { BPM, BARS, LOOP, LEVELS: [0, 0.25, 0.5, 0.75, 1], render, toWav };
})();
