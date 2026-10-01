"""Embed chapter navigation/subtitles and verify the locally delivered media."""
import hashlib
import json
from pathlib import Path
import re
import subprocess
import wave
import numpy as np
from pypdf import PdfReader
import imageio_ffmpeg

root=Path(__file__).resolve().parents[1];work=root/'.tools/demo';out=root/'output/video'
timeline=json.loads((out/'chapters.json').read_text(encoding='utf-8'))
total=sum(c['duration_s'] for c in timeline)
metadata=[';FFMETADATA1','title=Traction-aware warehouse rover - measured virtual demo','comment=Recorded software measurements and actual KiCad 10 render; synthesized Windows narration.']
for c in timeline:
    metadata += ['[CHAPTER]','TIMEBASE=1/1000',f"START={round(c['start_s']*1000)}",f"END={round((c['start_s']+c['duration_s'])*1000)}",'title='+c['title']]
(work/'chapters.ffmeta').write_text('\n'.join(metadata)+'\n',encoding='utf-8')
def timestamp(t):
    ms=round(t*1000);return f'{ms//3600000:02d}:{ms//60000%60:02d}:{ms//1000%60:02d},{ms%1000:03d}'
subtitles=[];number=0
for c in timeline:
    sentences=re.split(r'(?<=[.!?])\s+',c['narration']);weight=sum(len(s) for s in sentences);at=c['start_s']+.4
    for sentence in sentences:
        duration=(c['duration_s']-1.2)*len(sentence)/weight;number+=1
        subtitles.append(f'{number}\n{timestamp(at)} --> {timestamp(at+duration)}\n{sentence}\n');at+=duration
(out/'traction-aware-amr-demo.srt').write_text('\n'.join(subtitles),encoding='utf-8')
ffmpeg=imageio_ffmpeg.get_ffmpeg_exe();video=out/'traction-aware-amr-demo.mp4';stage=work/'demo-final.mp4'
command=[ffmpeg,'-hide_banner','-loglevel','error','-y','-i',str(video),'-i',str(work/'chapters.ffmeta'),'-i',str(out/'traction-aware-amr-demo.srt'),
 '-map','0:v:0','-map','0:a:0','-map','2:0','-map_metadata','1','-map_chapters','1','-c:v','copy','-c:a','copy','-c:s','mov_text','-metadata:s:s:0','language=eng','-movflags','+faststart',str(stage)]
subprocess.run(command,check=True)
stage.replace(video)
# Decode every frame and the entire audio stream; no new robot or Git tests run.
result=subprocess.run([ffmpeg,'-hide_banner','-v','error','-i',str(video),'-map','0:v','-map','0:a','-progress','pipe:1','-f','null','NUL'],text=True,capture_output=True,check=True)
assert not result.stderr.strip(),result.stderr
fields=dict(line.split('=',1) for line in result.stdout.splitlines() if '=' in line)
assert fields['progress']=='end' and int(fields['frame'])==round(total*20),fields
probe=subprocess.run([ffmpeg,'-hide_banner','-i',str(video)],text=True,capture_output=True)
assert 'Video: h264' in probe.stderr and '1280x720' in probe.stderr and 'Audio: aac' in probe.stderr and 'Subtitle: mov_text' in probe.stderr
assert probe.stderr.count('Chapter #')==len(timeline)
with wave.open(str(work/'narration.wav'),'rb') as wav:
    audio_seconds=wav.getnframes()/wav.getframerate();samples=np.frombuffer(wav.readframes(wav.getnframes()),dtype='<i2').astype(np.int32)
assert abs(audio_seconds-total)<.06 and np.max(np.abs(samples))>500 and np.max(np.abs(samples))<32767
assert np.mean(samples.astype(float)**2)**.5>200
pdf=root/'output/pdf/traction-aware-amr-report.pdf';reader=PdfReader(pdf)
assert len(reader.pages)==8 and all(len(p.extract_text())>800 for p in reader.pages)
for n,c in enumerate(timeline):
    at=c['start_s']+c['duration_s']*.55
    subprocess.run([ffmpeg,'-hide_banner','-loglevel','error','-y','-ss',f'{at:.3f}','-i',str(video),'-frames:v','1',str(work/(f'encoded-{n:02d}.png'))],check=True)
report={'video':str(video),'duration_s':total,'video_frames':int(fields['frame']),'resolution':'1280x720','fps':20,
 'video_codec':'H.264','audio_codec':'AAC','english_subtitle_track':True,'chapter_navigation':len(timeline),'complete_decode':'passed',
 'narration_audio_seconds':audio_seconds,'pdf_pages':len(reader.pages),'pdf_text_check':'passed',
 'video_sha256':hashlib.sha256(video.read_bytes()).hexdigest(),'pdf_sha256':hashlib.sha256(pdf.read_bytes()).hexdigest()}
(root/'output/delivery-validation.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps(report,indent=2))
