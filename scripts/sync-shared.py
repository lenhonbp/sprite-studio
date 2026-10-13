"""Generate browser/compatibility assets from the skill's canonical rig module."""
from pathlib import Path
root = Path(__file__).resolve().parent.parent
module = root / 'skills/produce-game-sprites/tools/rig-animation'
for source, targets in {
    'scripts/engine-adapters.mjs':['web/engine-adapters.mjs'],
    'scripts/production-export.mjs': ['web/production-export.mjs'],
    'assets/vfx-presets.mjs': ['web/vfx-presets.mjs'],
    'scripts/studio-core.mjs': ['web/studio-core.mjs'],
    'scripts/rig-core.mjs': ['web/rig-core.mjs'],
    'scripts/gif-preview.mjs': ['web/gif-preview.mjs'],
    'assets/demo-project.json': ['cli/assets/demo-project.json'],
}.items():
    data = (module / source).read_bytes()
    for target in targets:
        (root / target).write_bytes(data)
(root/'web/demo-project.json').write_bytes((root/'authoring-source/master-project.rig.json').read_bytes())
print('Shared browser assets synchronized from skill rig module.')
