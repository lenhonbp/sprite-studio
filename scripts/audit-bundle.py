"""Check full skill preservation, source ownership, portable links and JSON."""
from pathlib import Path
import hashlib,json,re,sys
root=Path(__file__).resolve().parent.parent
skill=root/'skills/produce-game-sprites'
errors=[]
provenance=json.loads((root/'config/skill-source.json').read_text())
changed={'SKILL.md','agents/openai.yaml'}
for name,digest in provenance['base_files'].items():
    p=skill/name
    if not p.is_file(): errors.append('Missing base skill file: '+name)
    elif name not in changed and hashlib.sha256(p.read_bytes()).hexdigest()!=digest: errors.append('Changed base skill resource: '+name)
module=skill/'tools/rig-animation'
for source,targets in {'scripts/engine-adapters.mjs':['web/engine-adapters.mjs'],
    'scripts/production-export.mjs':['web/production-export.mjs'],'assets/vfx-presets.mjs':['web/vfx-presets.mjs'],'scripts/studio-core.mjs':['web/studio-core.mjs'],'scripts/rig-core.mjs':['web/rig-core.mjs'],'scripts/gif-preview.mjs':['web/gif-preview.mjs'],'assets/demo-project.json':['cli/assets/demo-project.json']}.items():
    for target in targets:
        if (module/source).read_bytes()!=(root/target).read_bytes(): errors.append('Generated asset stale: '+target)
if (root/'web/demo-project.json').read_bytes()!=(root/'authoring-source/master-project.rig.json').read_bytes():errors.append('Generated browser master project stale')
for name in ['rig-core.mjs','gif-preview.mjs']:
    expected="export * from '../../skills/produce-game-sprites/tools/rig-animation/scripts/"+name+"';\n"
    if (root/'cli/scripts'/name).read_text()!=expected:errors.append('Compatibility module must re-export canonical skill source: '+name)
for p in [*skill.rglob('*.md'),root/'README.md',* (root/'docs').glob('*.md')]:
    for link in re.findall(r'\[[^\]]*\]\(([^)]+)\)',p.read_text()):
        link=link.split('#')[0]
        if not link or '://' in link or link.startswith(('mailto:','<')):continue
        if not (p.parent/link).exists():errors.append(str(p.relative_to(root))+': missing '+link)
for p in skill.rglob('*.json'):
    try:json.loads(p.read_text())
    except Exception as e:errors.append(str(p.relative_to(root))+': '+str(e))
text=(skill/'SKILL.md').read_text()
if not text.startswith('---\nname: produce-game-sprites\ndescription:'):errors.append('Skill frontmatter invalid')
for name in ['Technical','Visual','Runtime']:
    if '### '+name not in text:errors.append('Missing acceptance gate '+name)
for p in [*skill.rglob('*.md'),root/'AGENTS.md',*(root/'local').glob('*.mjs')]:
    if '/workspace/scratch/' in p.read_text() or '/root/.codex/' in p.read_text():errors.append('Nonportable path: '+str(p.relative_to(root)))
if errors:print('\n'.join(errors),file=sys.stderr);sys.exit(1)
print(f'Bundle audit passed: all {len(provenance["base_files"])} base skill files retained; shared rig assets, references, JSON and acceptance gates valid.')
