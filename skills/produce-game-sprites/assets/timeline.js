/* Offline preview timeline. Not a game-engine adapter. */
(function(root) {
  'use strict';
  function duration(clip) { return clip.frames.reduce((n, f) => n + f.duration_ms, 0); }
  function sample(clip, elapsed) {
    const total = duration(clip);
    if (!Number.isFinite(elapsed) || elapsed < 0 || total <= 0) throw new Error('Invalid timeline');
    const ended = !clip.loop && elapsed >= total;
    const time = clip.loop ? elapsed % total : Math.min(elapsed, total);
    let index = clip.frames.length - 1, start = 0;
    for (let i = 0; i < clip.frames.length; i++) {
      if (time < start + clip.frames[i].duration_ms) { index = i; break; }
      start += clip.frames[i].duration_ms;
    }
    const events = (clip.events || []).filter(e => e.time_ms <= time).map(e => e.name);
    return {index, time, total, ended, events};
  }
  const api = {duration, sample};
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
  root.SpriteTimeline = api;
})(typeof globalThis !== 'undefined' ? globalThis : this);
