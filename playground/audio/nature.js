// NATURE SOUND MODE (alternative to the drum + synth music): the planet's drone plus real recordings of what the data shows.
// Recordings: CC0 Freesound loops in audio/nature-sounds.js (window.NATURE_SOUNDS, credits in window.NATURE_CREDITS).
// Each loop has one level 0..1 that the page sets every frame from the data of the layer it belongs to:
//   fire = crackling fire        rain = rain            wind = breeze          storm = strong gusting wind
//   waves = sea on the shore     birds = forest birds   traffic = city traffic smoke = dark low rumble (synthesized)
// Smoothness: every loop starts silent and only ever moves by slow ramps (about 3 s to settle), the whole mode fades in and
// out over about 3 s, and the one-shots (thunder, volcano) have their own soft attack and long tail. Nothing starts or
// stops abruptly.
(function(){
  const LOOPS = ['fire', 'rain', 'wind', 'storm', 'waves', 'birds', 'traffic'];
  const FILE = {storm:'storm_wind'};
  const PEAK = {fire:1.4, rain:.6, wind:.55, storm:.7, waves:.7, birds:.28, traffic:.45, smoke:.6};
  const TC = 1.1;   // ramp time constant (s): ~3 s to settle

  const b64u8 = b => { const s = atob(b), u = new Uint8Array(s.length); for (let i = 0; i < s.length; i++) u[i] = s.charCodeAt(i); return u; };
  const Nature = {ctx:null, out:null, g:{}, buf:{}, levels:{}, on:false, ready:false};

  Nature.start = async function(ctx, dest){
    if (this.ctx) return;
    this.ctx = ctx;
    this.out = ctx.createGain(); this.out.gain.value = 0; this.out.connect(dest);
    // synthesized low rumble for smoke and haze (there is no good recording of "smoke")
    { const n = ctx.sampleRate * 6, b = ctx.createBuffer(1, n, ctx.sampleRate), d = b.getChannelData(0); let last = 0;
      for (let i = 0; i < n; i++){ last = (last + .02 * (Math.random() * 2 - 1)) / 1.02; d[i] = last * 3.5; }
      const f = 4000; for (let i = 0; i < f; i++){ d[i] *= i / f; d[n - 1 - i] *= i / f; }
      const s = ctx.createBufferSource(), lp = ctx.createBiquadFilter(), g = ctx.createGain(); s.buffer = b; s.loop = true;
      lp.type = 'lowpass'; lp.frequency.value = 140; g.gain.value = 0; s.connect(lp); lp.connect(g); g.connect(this.out); s.start(); this.g.smoke = g; }
    const S = window.NATURE_SOUNDS || {};
    for (const k of LOOPS){
      const b = S[FILE[k] || k]; if (!b) continue;
      try {
        const buf = await ctx.decodeAudioData(b64u8(b).buffer);
        const s = ctx.createBufferSource(), g = ctx.createGain(); s.buffer = buf; s.loop = true; g.gain.value = 0;
        s.connect(g); g.connect(this.out); s.start(ctx.currentTime + .05, Math.random() * buf.duration);   // random start: no two stories sound identical
        this.g[k] = g;
      } catch (e){ console.warn('nature loop', k, e); }
    }
    for (const k of ['thunder', 'volcano']){ const b = S[k]; if (b) try { this.buf[k] = await ctx.decodeAudioData(b64u8(b).buffer); } catch (e){ console.warn('nature shot', k, e); } }
    this.ready = true;
    this.setOn(this.on);
    clearInterval(this.timer); this.timer = setInterval(() => this.apply(), 100);
  };

  // levels: {fire, rain, wind, storm, waves, birds, traffic, smoke} each 0..1; anything missing fades to silence
  Nature.set = function(levels){ this.levels = levels || {}; };
  Nature.setOn = function(on){ this.on = on; if (this.out) this.out.gain.setTargetAtTime(on ? 1 : 0, this.ctx.currentTime, 1); };
  Nature.apply = function(){
    const ctx = this.ctx; if (!ctx || ctx.state !== 'running') return;
    const now = ctx.currentTime;
    for (const k in this.g){ const lv = Math.max(0, Math.min(1, this.levels[k] || 0)); this.g[k].gain.setTargetAtTime(PEAK[k] * Math.sqrt(lv), now, TC); }
  };
  // one-shot at a real event: soft 40 ms attack, the recording's own long tail
  Nature.shot = function(k, strength = 1){
    const ctx = this.ctx, buf = this.buf[k]; if (!ctx || !buf || !this.on) return;
    const t = ctx.currentTime + .02, s = ctx.createBufferSource(), g = ctx.createGain(); s.buffer = buf;
    g.gain.setValueAtTime(.0001, t); g.gain.exponentialRampToValueAtTime(Math.max(.001, .9 * strength), t + .04);
    g.gain.setValueAtTime(.9 * strength, t + buf.duration - 1.5); g.gain.linearRampToValueAtTime(.0001, t + buf.duration);
    s.connect(g); g.connect(this.out); s.start(t); s.stop(t + buf.duration + .05);
  };

  window.Nature = Nature;
})();
