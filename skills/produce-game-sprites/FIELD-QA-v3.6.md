> Historical record supplied with the original archive; superseded for current acceptance by references/verification-v3.8.md. Engine/API claims below were not rerun during v3.8.

# FIELD / QA v3.6 — real five-sect production

v3.6 was hardened during a real 5-character × 4-direction × 7-action production attempt.

The AI aggregate sources looked good at sheet level but contained touching/overlapping poses and VFX. Naive midpoint slicing produced amputated frames; marker-controlled watershed produced mixed/double or empty frames because composited overlap destroys hidden pixel information. Those outputs were rejected by visual QA despite technically valid PNG/canvas metadata.

The new `sheet-separability-check` was then run against all five aggregate sheets. It correctly blocked deterministic auto-slicing with 55 (Võ Đang), 62 (Cái Bang), 58 (Nga Mi), 57 (Thiếu Lâm) and 56 (Ngũ Độc) overlap/gutter risks.

Production switched to a deterministic native modular/vector rig. The delivered field build produced 820 runtime PNG frames at 128×128, preserved 820 256×256 masters, generated 140 GIF previews and five engine handoff atlases. All five animation manifests passed technical inspection with zero errors and zero warnings; motion metadata had no structural errors/warnings. Visual review passed against complete contact sheets. Target-engine runtime remains intentionally `not_tested` because the current environment did not run the assets inside the requested Godot/PixiJS project.

This field validates the v3.6 rules: detect source separability before slicing, never fabricate hidden overlap pixels, switch methods after a failed source route, keep a shared master→runtime transform, and never promote preview evidence into runtime approval.
