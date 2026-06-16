// Procedural ambient music via the Web Audio API — no audio files needed, so
// it ships fine to Vercel. A slow detuned drone pad plus a gentle minor-key
// arpeggio. Must be started from a user gesture (browser autoplay policy).

export class AudioService {
  private ctx: AudioContext | null = null;
  private master: GainNode | null = null;
  private padOscs: OscillatorNode[] = [];
  private padFilter: BiquadFilterNode | null = null;
  private timer: number | null = null;

  private enabled = false;
  private playing = false;

  // arpeggio pattern (A minor pentatonic), one step per ~0.34s
  private pattern = [220, 261.63, 329.63, 392, 440, 392, 329.63, 261.63];
  private step = 0;
  private nextNoteTime = 0;
  private readonly stepDur = 0.34;
  private readonly lookahead = 0.1;

  get isEnabled(): boolean {
    return this.enabled;
  }

  /** Toggle music. Starting must happen inside a user-gesture call stack. */
  setEnabled(on: boolean): void {
    this.enabled = on;
    if (on) this.start();
    else this.stop();
  }

  private ensureContext(): void {
    if (this.ctx) return;
    const AC =
      window.AudioContext ||
      (window as unknown as { webkitAudioContext: typeof AudioContext })
        .webkitAudioContext;
    if (!AC) return;
    this.ctx = new AC();
    this.master = this.ctx.createGain();
    this.master.gain.value = 0;
    this.master.connect(this.ctx.destination);
  }

  private start(): void {
    this.ensureContext();
    if (!this.ctx || !this.master || this.playing) return;
    void this.ctx.resume();
    this.playing = true;

    // ---- drone pad: two detuned saws through a lowpass with a slow LFO ----
    this.padFilter = this.ctx.createBiquadFilter();
    this.padFilter.type = "lowpass";
    this.padFilter.frequency.value = 600;
    const padGain = this.ctx.createGain();
    padGain.gain.value = 0.18;
    this.padFilter.connect(padGain).connect(this.master);

    for (const detune of [-6, 6]) {
      const o = this.ctx.createOscillator();
      o.type = "sawtooth";
      o.frequency.value = 110; // A2
      o.detune.value = detune;
      o.connect(this.padFilter);
      o.start();
      this.padOscs.push(o);
    }
    // filter LFO for a breathing pad
    const lfo = this.ctx.createOscillator();
    const lfoGain = this.ctx.createGain();
    lfo.frequency.value = 0.07;
    lfoGain.gain.value = 350;
    lfo.connect(lfoGain).connect(this.padFilter.frequency);
    lfo.start();
    this.padOscs.push(lfo);

    // fade master in
    const now = this.ctx.currentTime;
    this.master.gain.cancelScheduledValues(now);
    this.master.gain.setValueAtTime(this.master.gain.value, now);
    this.master.gain.linearRampToValueAtTime(0.14, now + 1.5);

    // arpeggio scheduler
    this.nextNoteTime = now + 0.1;
    this.step = 0;
    this.timer = window.setInterval(() => this.schedule(), 25);
  }

  private schedule(): void {
    if (!this.ctx) return;
    while (this.nextNoteTime < this.ctx.currentTime + this.lookahead) {
      this.playNote(this.pattern[this.step % this.pattern.length], this.nextNoteTime);
      this.nextNoteTime += this.stepDur;
      this.step++;
    }
  }

  private playNote(freq: number, time: number): void {
    if (!this.ctx || !this.master) return;
    const osc = this.ctx.createOscillator();
    const g = this.ctx.createGain();
    osc.type = "triangle";
    osc.frequency.value = freq;
    // pluck envelope
    g.gain.setValueAtTime(0, time);
    g.gain.linearRampToValueAtTime(0.12, time + 0.02);
    g.gain.exponentialRampToValueAtTime(0.001, time + 0.32);
    osc.connect(g).connect(this.master);
    osc.start(time);
    osc.stop(time + 0.34);
  }

  private stop(): void {
    if (!this.ctx || !this.master) return;
    const now = this.ctx.currentTime;
    this.master.gain.cancelScheduledValues(now);
    this.master.gain.setValueAtTime(this.master.gain.value, now);
    this.master.gain.linearRampToValueAtTime(0, now + 0.4);

    if (this.timer !== null) {
      clearInterval(this.timer);
      this.timer = null;
    }
    // stop pad oscillators shortly after the fade
    const oscs = this.padOscs;
    this.padOscs = [];
    setTimeout(() => {
      for (const o of oscs) {
        try {
          o.stop();
          o.disconnect();
        } catch {
          /* already stopped */
        }
      }
    }, 450);
    this.playing = false;
  }

  dispose(): void {
    this.stop();
    setTimeout(() => {
      void this.ctx?.close();
      this.ctx = null;
      this.master = null;
    }, 500);
  }
}
