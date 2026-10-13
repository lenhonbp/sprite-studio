from pathlib import Path
import json,re

def strip_exports(code):
    return re.sub(r'^export ', '', code, flags=re.M)
root=Path(__file__).resolve().parent.parent
web=root/'web'
assets={}
for f in sorted(web.iterdir()):
 if f.is_file():assets['/'+f.name]={'text':f.read_text(),'type':{'html':'text/html; charset=utf-8','css':'text/css','mjs':'text/javascript','json':'application/json'}[f.suffix[1:]]}
widget=(root/'Nhon-Le-Sprite-Studio.html').read_text().replace('window.STUDIO_DEMO=', 'window.STUDIO_EMBEDDED=true;window.STUDIO_DEMO=')
core=strip_exports(re.sub(r'^import .*?;\n','',(web/'rig-core.mjs').read_text(),flags=re.M))
production=strip_exports((web/'studio-core.mjs').read_text())
report=strip_exports(re.sub(r'^import .*?;\n','',(web/'project-report.mjs').read_text(),flags=re.M))
service=strip_exports(re.sub(r'^import .*?;\n','',(root/'server/service.mjs').read_text(),flags=re.M))
(root/'worker/index.js').write_text(production+'\n'+core+'\n'+report+'\n'+service+'\nconst assets='+json.dumps(assets,ensure_ascii=False)+';\nconst widget='+json.dumps(widget,ensure_ascii=False)+';\nexport default createWorker(assets,widget,JSON.parse(assets["/demo-project.json"].text));\n')
