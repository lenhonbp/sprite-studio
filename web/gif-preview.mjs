// Deterministic 255-color RGB palette + transparent index. Preview only, no raster master changes.
export function makeGif(width,height,frames,loop=true){
 if(!Number.isInteger(width)||!Number.isInteger(height)||width<1||height<1||width>4096||height>4096||!frames.length||width*height*frames.length>16000000)throw Error('GIF preview exceeds pixel budget');
 const out=[],byte=n=>out.push(n&255),word=n=>{byte(n);byte(n>>8);},ascii=s=>{for(const c of s)byte(c.charCodeAt(0));};
 ascii('GIF89a');word(width);word(height);byte(247);byte(0);byte(0);for(let i=0;i<256;i++){const q=i?Math.round((i-1)*255/254):0;byte(Math.round((q>>5)*255/7));byte(Math.round(((q>>2)&7)*255/7));byte((q&3)*85);}
 if(loop){byte(33);byte(255);byte(11);ascii('NETSCAPE2.0');byte(3);byte(1);word(0);byte(0);}
 let clock=0,csClock=0;for(const f of frames){if(!f.rgba||f.rgba.length!==width*height*4||!Number.isFinite(f.duration_ms)||f.duration_ms<10)throw Error('Invalid GIF frame');clock+=f.duration_ms;const next=Math.round(clock/10),delay=next-csClock;csClock=next;if(delay<1||delay>65535)throw Error('GIF delay out of range');byte(33);byte(249);byte(4);byte(9);word(delay);byte(0);byte(0);byte(44);word(0);word(0);word(width);word(height);byte(0);byte(8);
  // Clear before the decoder's dictionary can exceed 9-bit codes. Large but portable and bounded.
  const data=[];let bits=0,acc=0,count=0;const code=n=>{acc|=n<<bits;bits+=9;while(bits>=8){data.push(acc&255);acc>>>=8;bits-=8;}};code(256);
  for(let j=0;j<f.rgba.length;j+=4){if(count===200){code(256);count=0;}const a=f.rgba[j+3],q=(f.rgba[j]>>5)*32+(f.rgba[j+1]>>5)*4+(f.rgba[j+2]>>6);code(a<128?0:1+Math.floor(q*254/255));count++;}code(257);if(bits)data.push(acc&255);for(let j=0;j<data.length;j+=255){byte(Math.min(255,data.length-j));for(const v of data.slice(j,j+255))byte(v);}byte(0);
 }byte(59);return new Uint8Array(out);
}
