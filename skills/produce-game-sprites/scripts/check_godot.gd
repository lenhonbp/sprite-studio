extends SceneTree
# Headless smoke check of exported data and real AnimatedSprite2D playback.
# It does not approve artwork, origin appearance, filtering or combat events.
var errors: Array[String] = []
var transitions: Array[int] = []

func _initialize() -> void:
    call_deferred("_run")

func require(value: bool, message: String) -> void:
    if not value:
        errors.append(message)

func _run() -> void:
    var args := OS.get_cmdline_user_args()
    if args.size() != 1:
        print(JSON.stringify({"status": "blocked", "errors": ["Pass res://path/to/release after --"]}))
        quit(2)
        return
    var release: String = args[0].trim_suffix("/")
    var timeline_file := FileAccess.open(release + "/animations.json", FileAccess.READ)
    if timeline_file == null:
        print(JSON.stringify({"status": "blocked", "errors": ["Missing animations.json"]}))
        quit(2)
        return
    var timeline = JSON.parse_string(timeline_file.get_as_text())
    var frames = load(release + "/sprite_frames.tres")
    if not timeline is Dictionary or not frames is SpriteFrames:
        print(JSON.stringify({"status": "blocked", "errors": ["Cannot load exported timeline/SpriteFrames"]}))
        quit(2)
        return
    var sprite := AnimatedSprite2D.new()
    sprite.sprite_frames = frames
    root.add_child(sprite)
    sprite.frame_changed.connect(func(): transitions.append(sprite.frame))
    for clip in timeline.clips:
        var name: String = clip.name
        require(frames.has_animation(name), "Missing clip " + name)
        if not frames.has_animation(name):
            continue
        require(frames.get_frame_count(name) == clip.frames.size(), "Frame count mismatch " + name)
        require(frames.get_animation_loop(name) == clip.loop, "Loop mismatch " + name)
        var total_ms: float = 0
        for i in range(clip.frames.size()):
            total_ms += float(clip.frames[i].duration_ms)
            if i >= frames.get_frame_count(name):
                continue
            var seconds: float = frames.get_frame_duration(name, i) / frames.get_animation_speed(name)
            require(abs(seconds * 1000.0 - float(clip.frames[i].duration_ms)) < 0.001, "Duration mismatch " + name)
            var texture = frames.get_frame_texture(name, i)
            require(texture is AtlasTexture, "Frame is not AtlasTexture " + name)
            if texture is AtlasTexture:
                require(texture.get_size() == Vector2(timeline.cell_size[0], timeline.cell_size[1]), "Cell mismatch " + name)
        transitions.clear()
        sprite.play(name)
        await create_timer(total_ms / 1000.0 + 0.15).timeout
        if clip.loop:
            require(sprite.is_playing(), "Loop stopped " + name)
        else:
            require(not sprite.is_playing(), "One-shot still playing " + name)
            require(sprite.frame == clip.frames.size() - 1, "Terminal frame mismatch " + name)
        if clip.frames.size() > 1:
            require(transitions.size() > 0, "Playback did not advance " + name)
        sprite.stop()
    print(JSON.stringify({"status": "headless_pass" if errors.is_empty() else "blocked",
        "engine": "Godot", "version": Engine.get_version_info().string, "errors": errors,
        "visual_status": "not_tested", "checks": ["resource import", "atlas geometry", "declared timing", "loop/terminal playback"]}))
    quit(0 if errors.is_empty() else 1)
