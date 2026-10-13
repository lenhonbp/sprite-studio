import {studioReport} from './studio-core.mjs';
import {validateProject,samplePose,auditPose,coverageReport,hasArtwork} from './rig-core.mjs';
export function projectReport(p,fps=24){
 if(!Number.isFinite(fps)||fps<1||fps>120)throw Error('FPS từ 1 đến 120');
 validateProject(p);const bytes=new TextEncoder().encode(JSON.stringify(p)).length,frames=p.clips.reduce((n,c)=>n+Math.ceil(c.duration_ms*fps/1000),0),warnings=[];
 if(!hasArtwork(p))warnings.push('Chưa có ảnh gắn vào slot hoặc key trang bị.');
 if(bytes>4_000_000)warnings.push('Nguồn vượt 4 MB: dùng offline/CLI hoặc giảm kích thước PNG trước khi đồng bộ.');
 if(frames*p.canvas[0]*p.canvas[1]>64_000_000)warnings.push('Xuất tất cả frame tại FPS đã chọn vượt giới hạn trình duyệt; giảm FPS hoặc dùng CLI.');
 const coverage=coverageReport(p);if(coverage.missing.length)warnings.push('Còn thiếu các cặp động tác/hướng yêu cầu.');
 if(p.clips.some(c=>Math.ceil(c.duration_ms*fps/1000)>3000))warnings.push('Có clip vượt 3000 frame ở FPS đã chọn; giảm FPS hoặc rút ngắn clip.');
 const samples=[];for(const c of p.clips.slice(0,40)){for(const time of [...new Set([0,Math.round(c.duration_ms/2),c.loop?Math.max(0,c.duration_ms-1):c.duration_ms])]){const audit=auditPose(p,samplePose(p,c.id,time));if(audit.possible_canvas_intrusion.length)samples.push({clip:c.id,time_ms:time,slots:audit.possible_canvas_intrusion});}}
 if(samples.length)warnings.push('Một số pose lấy mẫu có thể chạm/vượt biên; xem PNG thực tế trước khi dùng.');
 return {schema:'nhon-le-project-check/v1',technical:'valid',visual:'not_reviewed',runtime:'not_tested',project:p.id,source_bytes:bytes,online_eligible:bytes<=4_000_000,counts:{bones:p.bones.length,slots:p.slots.length,images:Object.keys(p.attachments).length,clips:p.clips.length},fps,frames_at_fps:frames,coverage,production:studioReport(p),warnings:[...warnings,...studioReport(p).warnings],possible_canvas_intrusion:samples,sampling:'0, giữa và cuối clip; tối đa 40 clip. Đây không phải kiểm tra toàn bộ frame hay duyệt hình ảnh.'};
}
