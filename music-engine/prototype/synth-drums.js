// Synthesized cinematic drums (Web Audio, no samples). One voice per piano-roll row.
// Used live by piano-roll.html and offline (OfflineAudioContext) for bouncing, so preview == bounce.
window.SynthDrums = (() => {
  // f0 -> f1: pitch sweep of the drum skin; dec: body decay (s); noise: stick/skin noise amount; nf: noise filter (Hz);
  // ndec: noise decay; over: 2nd skin mode level; sub: extra low sine for the big drums; click: attack transient
  const VOICES = {
    k24: { f0: 88, f1: 38, sweep: 0.28, dec: 1.9, noise: 0.22, nf: 700, ndec: 0.16, over: 0.18, sub: 0.55, click: 0.15 },   // Deep (big)
    k30: { f0: 108, f1: 52, sweep: 0.16, dec: 0.95, noise: 0.28, nf: 1100, ndec: 0.10, over: 0.22, sub: 0.2, click: 0.2 },   // Low (groove)
    k36: { f0: 132, f1: 68, sweep: 0.12, dec: 0.75, noise: 0.42, nf: 1800, ndec: 0.09, over: 0.28, sub: 0, click: 0.35 },    // Mid 1 (accent)
    k42: { f0: 150, f1: 82, sweep: 0.11, dec: 0.6, noise: 0.32, nf: 1600, ndec: 0.08, over: 0.25, sub: 0, click: 0.25 },     // Mid 2
    k48: { f0: 172, f1: 98, sweep: 0.1, dec: 0.5, noise: 0.3, nf: 1900, ndec: 0.07, over: 0.25, sub: 0, click: 0.25 },       // Mid 3
    k54: { f0: 230, f1: 150, sweep: 0.06, dec: 0.22, noise: 0.45, nf: 2600, ndec: 0.05, over: 0.3, sub: 0, click: 0.4 },     // Bright 1 (short)
    k60: { f0: 265, f1: 180, sweep: 0.07, dec: 0.3, noise: 0.38, nf: 2800, ndec: 0.06, over: 0.3, sub: 0, click: 0.35 },     // Bright 2
    k66: { f0: 320, f1: 215, sweep: 0.07, dec: 0.3, noise: 0.36, nf: 3200, ndec: 0.06, over: 0.3, sub: 0, click: 0.35 },     // Bright 3
    k72: { f0: 900, f1: 700, sweep: 0.02, dec: 0.05, noise: 0.9, nf: 3800, ndec: 0.05, over: 0, sub: 0, click: 0.6, rim: 1 }, // Rim
  };
  const noiseCache = new WeakMap(), busCache = new WeakMap();
  function noiseBuf(ctx) {
    if (noiseCache.has(ctx)) return noiseCache.get(ctx);
    const b = ctx.createBuffer(1, ctx.sampleRate * 2, ctx.sampleRate), d = b.getChannelData(0);
    let s = 12345; for (let i = 0; i < d.length; i++) { s = (s * 1103515245 + 12345) >>> 0; d[i] = (s / 2147483648 - 1); }
    noiseCache.set(ctx, b); return b;
  }
  // per-context bus: gentle saturation + a big room, so the synth skins sound like drums in a hall
  function bus(ctx, dest) {
    let m = busCache.get(ctx); if (m && m.dest === dest) return m.input;
    const input = ctx.createGain(), sat = ctx.createWaveShaper(), n = 1024, c = new Float32Array(n);
    for (let i = 0; i < n; i++) { const x = i / (n - 1) * 2 - 1; c[i] = Math.tanh(1.8 * x) / Math.tanh(1.8); }
    sat.curve = c; const dry = ctx.createGain(); dry.gain.value = 0.85;
    const conv = ctx.createConvolver(), len = ctx.sampleRate * 2.6, ir = ctx.createBuffer(2, len, ctx.sampleRate);
    let s = 777; for (let ch = 0; ch < 2; ch++) { const d = ir.getChannelData(ch); for (let i = 0; i < len; i++) { s = (s * 1103515245 + 12345) >>> 0; d[i] = (s / 2147483648 - 1) * Math.pow(1 - i / len, 2.6); } }
    conv.buffer = ir; const hp = ctx.createBiquadFilter(); hp.type = 'highpass'; hp.frequency.value = 120;
    const wet = ctx.createGain(); wet.gain.value = 0.22;
    input.connect(sat); sat.connect(dry); dry.connect(dest); sat.connect(hp); hp.connect(conv); conv.connect(wet); wet.connect(dest);
    busCache.set(ctx, { dest, input }); return input;
  }
  function env(ctx, dest, t, peak, a, d) {
    const g = ctx.createGain(); g.gain.setValueAtTime(0.0001, t); g.gain.exponentialRampToValueAtTime(Math.max(peak, 0.0002), t + a);
    g.gain.exponentialRampToValueAtTime(0.0001, t + a + d); g.connect(dest); return g;
  }
  // vel 1..127; detune: small per-hit pitch variation (like hitting a real skin in a different spot)
  function play(ctx, dest, id, t, vel, detune = 0) {
    const V = VOICES[id]; if (!V) return;
    const out = bus(ctx, dest), g = Math.pow(vel / 127, 1.3), bright = 0.55 + 0.45 * vel / 127, k = 1 + detune;
    // skin: pitch sweep
    if (!V.rim) {
      const o = ctx.createOscillator(); o.type = 'sine';
      o.frequency.setValueAtTime(V.f0 * k, t); o.frequency.exponentialRampToValueAtTime(V.f1 * k, t + V.sweep);
      o.connect(env(ctx, out, t, 0.9 * g, 0.002, V.dec)); o.start(t); o.stop(t + V.dec + 0.1);
      if (V.over) {   // second skin mode, inharmonic, dies faster
        const o2 = ctx.createOscillator(); o2.type = 'sine';
        o2.frequency.setValueAtTime(V.f0 * 1.58 * k, t); o2.frequency.exponentialRampToValueAtTime(V.f1 * 1.58 * k, t + V.sweep);
        o2.connect(env(ctx, out, t, V.over * g, 0.002, V.dec * 0.45)); o2.start(t); o2.stop(t + V.dec);
      }
      if (V.sub) {
        const o3 = ctx.createOscillator(); o3.type = 'sine'; o3.frequency.setValueAtTime(V.f1 * 1.05 * k, t);
        o3.connect(env(ctx, out, t, V.sub * g, 0.01, V.dec * 1.1)); o3.start(t); o3.stop(t + V.dec * 1.2);
      }
    } else {
      const o = ctx.createOscillator(); o.type = 'triangle'; o.frequency.setValueAtTime(V.f0 * k, t); o.frequency.exponentialRampToValueAtTime(V.f1 * k, t + V.sweep);
      o.connect(env(ctx, out, t, 0.35 * g, 0.001, V.dec)); o.start(t); o.stop(t + 0.1);
    }
    // stick + skin noise
    const ns = ctx.createBufferSource(); ns.buffer = noiseBuf(ctx);
    const f = ctx.createBiquadFilter(); f.type = V.rim ? 'bandpass' : 'lowpass'; f.frequency.value = V.nf * bright * k; f.Q.value = V.rim ? 2.5 : 0.7;
    ns.connect(f); f.connect(env(ctx, out, t, V.noise * g, 0.001, V.ndec)); ns.start(t, Math.random() * 1.5); ns.stop(t + V.ndec + 0.05);
    // attack click
    if (V.click) {
      const c = ctx.createOscillator(); c.type = 'sine'; c.frequency.setValueAtTime(V.f0 * 3.1 * k, t);
      c.connect(env(ctx, out, t, V.click * g * bright, 0.0005, 0.018)); c.start(t); c.stop(t + 0.03);
    }
  }
  return { VOICES, play };
})();
