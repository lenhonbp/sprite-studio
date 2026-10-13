/** One clock for pose selection and gameplay events. No renderer or collision claims. */
let serial = 0;

export function sampleClip(clip, timeMs) {
  const total = clip.frames.reduce((n, f) => n + f.duration_ms, 0);
  let local = clip.loop ? ((timeMs % total) + total) % total : Math.min(Math.max(timeMs, 0), total);
  let boundary = 0;
  for (let i = 0; i < clip.frames.length; i++) {
    boundary += clip.frames[i].duration_ms;
    if (local < boundary) return { index: i, frame: clip.frames[i], localTimeMs: local };
  }
  return { index: clip.frames.length - 1, frame: clip.frames.at(-1), localTimeMs: local };
}

export function createClipClock(clip, onEvent = () => {}, options = {}) {
  if (!clip || !Array.isArray(clip.frames) || !clip.frames.length || typeof clip.loop !== 'boolean' ||
      clip.frames.some(f => !Number.isFinite(f.duration_ms) || f.duration_ms <= 0)) throw new Error('Invalid clip');
  const total = clip.frames.reduce((n, f) => n + f.duration_ms, 0);
  const events = clip.events || [];
  if (!Array.isArray(events) || events.some(e => !Number.isFinite(e.time_ms) || e.time_ms < 0 || e.time_ms >= total)) throw new Error('Invalid event time');
  let absolute = 0, playing = false, paused = false, instance = '';
  const state = () => ({ ...sampleClip(clip, absolute), absoluteTimeMs: absolute, playing, paused, instance });
  const emit = (event, cycle) => {
    const pose = sampleClip(clip, event.time_ms);
    onEvent({ ...event, clip: clip.name, instance, cycle, frameId: pose.frame.id,
              frameIndex: pose.index, localTimeMs: event.time_ms });
  };
  return {
    start() {
      absolute = 0; playing = true; paused = false; instance = `${clip.name || 'clip'}:${++serial}`;
      const activeInstance = instance;
      for (const event of events) {
        if (!playing || paused || instance !== activeInstance) break;
        if (event.time_ms === 0) emit(event, 0);
      }
      return state();
    },
    advance(deltaMs) {
      if (!Number.isFinite(deltaMs) || deltaMs < 0) throw new Error('deltaMs must be finite and nonnegative');
      if (!playing || paused || deltaMs === 0) return state();
      const end = clip.loop ? absolute + deltaMs : Math.min(total, absolute + deltaMs);
      const firstCycle = Math.floor(absolute / total), lastCycle = clip.loop ? Math.floor(end / total) : 0;
      if (lastCycle - firstCycle > (options.maxCyclesPerAdvance ?? 1000)) throw new Error('Delta exceeds clock sweep budget');
      const pending = [];
      for (let cycle = firstCycle; cycle <= lastCycle; cycle++) {
        for (const event of events) {
          const at = cycle * total + event.time_ms;
          if (at > absolute && at <= end) pending.push({ event, cycle, at });
        }
      }
      pending.sort((a, b) => a.at - b.at);
      const activeInstance = instance;
      for (const row of pending) {
        if (!playing || paused || instance !== activeInstance) return state(); // interruption cancels remaining tick
        absolute = row.at;
        emit(row.event, row.cycle);
        if (!playing || paused || instance !== activeInstance) return state();
      }
      absolute = end;
      if (!clip.loop && absolute >= total) playing = false;
      return state();
    },
    pause() { paused = true; return state(); },
    resume() { paused = false; return state(); },
    stop() { playing = false; paused = false; return state(); },
    state,
  };
}
