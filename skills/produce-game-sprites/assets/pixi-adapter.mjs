/** Create a timed PixiJS v8 sprite from a parsed local sheet.
 * The caller owns ticker updates, clip transitions and gameplay event dispatch.
 */
export function createTimedSprite(PIXI, sheet, timeline, clipName) {
  const clip = timeline.clips.find(c => c.name === clipName);
  if (!clip) throw new Error('Unknown clip: ' + clipName);
  const textures = clip.frames.map(frame => {
    const texture = sheet.textures[frame.id];
    if (!texture) throw new Error('Missing frame texture: ' + frame.id);
    return {texture, time: frame.duration_ms};
  });
  const sprite = new PIXI.AnimatedSprite({textures, autoUpdate:false, loop:clip.loop, animationSpeed:1});
  sprite.anchor.set(timeline.origin[0]/timeline.cell_size[0], timeline.origin[1]/timeline.cell_size[1]);
  return sprite;
}

/** Runtime controller: advance milliseconds once; do not also call sprite.update(). */
export async function createClockedSprite(PIXI, sheet, timeline, clipName, onEvent = () => {}) {
  const {createClipClock} = await import('./clip-clock.mjs');
  const sprite = createTimedSprite(PIXI, sheet, timeline, clipName);
  const clip = timeline.clips.find(c => c.name === clipName);
  const clock = createClipClock(clip, event => {
    sprite.gotoAndStop(event.frameIndex);
    onEvent({...event, displayedFrameId: clip.frames[sprite.currentFrame].id});
  });
  const apply = state => { sprite.gotoAndStop(state.index); return state; };
  return {sprite, clock, start: () => apply(clock.start()),
          advance: ms => apply(clock.advance(ms)), stop: () => apply(clock.stop()),
          pause: () => clock.pause(), resume: () => clock.resume()};
}
