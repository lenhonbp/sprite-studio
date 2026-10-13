from pathlib import Path
import re

def strip_exports(code):
    return re.sub(r'^export ', '', code, flags=re.M)

root=Path(__file__).resolve().parent
dist=root/'web'
html=(dist/'index.html').read_text()
html=html.replace('<link rel="stylesheet" href="studio.css">','<style>'+(dist/'studio.css').read_text()+'</style>')
core=strip_exports(re.sub(r'^import .*?;\n','',(dist/'rig-core.mjs').read_text(),flags=re.M))
production=strip_exports((dist/'studio-core.mjs').read_text())
presets=strip_exports((dist/'vfx-presets.mjs').read_text())
engines=strip_exports((dist/'engine-adapters.mjs').read_text())
fxexport=strip_exports(re.sub(r'^import .*?;\n','',(dist/'production-export.mjs').read_text(),flags=re.M))
fxui=strip_exports(re.sub(r'^import .*?;\n','',(dist/'production-ui.mjs').read_text(),flags=re.M))
zip_code=strip_exports((dist/'zip-store.mjs').read_text())
editor=re.sub(r'^import .*?;\n','',(dist/'editor.mjs').read_text(),flags=re.M)
demo=(dist/'demo-project.json').read_text().replace('</','<\\/')
html=html.replace('href="guide.html"','href="#" id="offlineGuide"')
gif_code=strip_exports((dist/'gif-preview.mjs').read_text())
bridge_code=strip_exports((dist/'agent-bridge.mjs').read_text())
extra='\n'.join(strip_exports(re.sub(r'^import .*?;\n','',(dist/f).read_text(),flags=re.M)) for f in ['project-vault.mjs','project-report.mjs'])
script=engines+'\n'+production+'\n'+presets+'\n'+fxexport+'\n'+fxui+'\n'+extra+'\n'+bridge_code+'\n'+core+'\n'+gif_code+'\n'+zip_code+'\nwindow.STUDIO_DEMO='+demo+';\n'+editor
script+='\ndocument.getElementById("offlineGuide").onclick=e=>{e.preventDefault();alert("v4.1.1: Lưu bản vào Thư viện thiết bị, Xuất/Nhập backup để chuyển máy. Có kiểm tra project trước xuất, thử lại hoặc tạm dừng đồng bộ online. Chọn xương và clip, kéo khớp hoặc dùng IK để lưu key. Kéo key trên timeline; quản lý event/socket/preset trong inspector. Bật Sửa rig gốc khi dựng rig. Lưu JSON để giữ nguồn; Xuất frame ZIP để kiểm tra với produce-game-sprites v3.8. Hướng dẫn đầy đủ nằm trên Site.");};'
html=html.replace('<script type="module" src="editor.mjs"></script>','<script type="module">'+script.replace('</script','<\\/script')+'</script>')
out=root/'Nhon-Le-Sprite-Studio.html'
out.write_text(html)
print(out)

