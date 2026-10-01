"""Render a narrated measured-data demo and an evidence-based PDF report.

Animations replay existing CSV measurements; diagrams are explicitly explanatory.
No GitHub workflow, publication or new experiment is launched by this tool.
"""
import argparse
import collections
import csv
import hashlib
import json
import math
import os
from pathlib import Path
import re
import subprocess
import textwrap
import wave
import xml.etree.ElementTree as ET
import numpy as np
from PIL import Image,ImageDraw,ImageFont,ImageOps
import imageio_ffmpeg
from demo_chapters import CHAPTERS

ROOT=Path(__file__).resolve().parents[1]
WORK=ROOT/'.tools/demo';OUT=ROOT/'output/video';PDF=ROOT/'output/pdf'
for folder in [WORK,OUT,PDF]:folder.mkdir(parents=True,exist_ok=True)
W,H,FPS=1280,720,20
BG='#0b1424';PANEL='#142237';FG='#eaf0f7';MUTED='#a7b9ce';TEAL='#60dfca';AMBER='#f1b363';BLUE='#70acec';PURPLE='#c49ce3';RED='#f48e87'
COLORS={'A':BLUE,'B':TEAL,'C':PURPLE,'D':AMBER}
FONT_DIR=Path('C:/Windows/Fonts')
def font(size,bold=False):return ImageFont.truetype(str(FONT_DIR/('segoeuib.ttf' if bold else 'segoeui.ttf')),size)
F={s:font(s) for s in [16,18,20,22,24,26,30,36,42,52]}
FB={s:font(s,True) for s in [18,20,22,24,26,30,36,42,52]}
def load(p):return json.loads((ROOT/p).read_text(encoding='utf-8'))
MATRIX=load('results/matrix.json');SUMMARY=load('results/summary.json');LIVE={v:load(f'results/live_{v}.json') for v in 'ABCD'}
FAULTS=load('results/faults.json');ROS=load('results/ros_smoke.json');SPICE=load('results/spice.json')
ERC=load('results/erc.json');DRC=load('results/drc.json')
GAZEBO=load('results/gazebo_smoke.json')
def erc_violations():return [v for sheet in ERC['sheets'] for v in sheet['violations']]
DRC_COUNTS=collections.Counter(v['severity'] for v in DRC['violations'])
DRC_TYPES=collections.Counter((v['severity'],v['type']) for v in DRC['violations'])
def trace(path):
    with (ROOT/path).open() as stream:return [{k:float(v) for k,v in row.items()} for row in csv.DictReader(stream)]
TRACES={v:trace(f'results/trace_{v}.csv') for v in 'ABCD'}
FAULT_TRACE=trace('results/trace_D_overcurrent.csv')
SPICE_TRACE=np.loadtxt(ROOT/'hardware/spice/current_filter.dat',skiprows=1)
PCB_IMAGES=[Image.open(ROOT/f'hardware/exports/{name}.png').convert('RGBA') for name in ['carrier-top','carrier-isometric']]
PHASES=[
 (1,'Verified','Requirements and experiment matrix','Fixed sensor/control boundaries, rates, payloads and friction cases.'),
 (2,'Verified','Robot model and warehouse','Mathematical dynamics checks and real Gazebo dry/low-friction contact bridge passed.'),
 (3,'Verified','ROS 2 basics and integration','Actual DDS traffic, TF, controller-selection service, bag record/replay.'),
 (4,'Verified','Linear PI / LQR','Controllable and stable design point. Worst dry LQR RMSE: 8.76 mm.'),
 (5,'Verified','Nonlinear control / traction','All runs finite and complete. Low-traction slip reduction: 18.48%; 20% target not met.'),
 (6,'Verified','Virtual PCB and circuit','KiCad 10 ERC 0, DRC 0, connectivity 0; source, renders, Gerbers and RC simulation.'),
 (7,'Verified','Software and paced tests','15 local tests; 540 completed routes; 4 recorded live runs; 5 fault cases.'),
 (8,'Verified','GitHub demo and profile','Repository, interactive Pages website, phase report and profile project link delivered.')]

def tx(draw,x,y,s,size=22,color=FG,bold=False):draw.text((x,y),str(s),font=(FB if bold else F)[size],fill=color)
def wrap(draw,x,y,s,width,size=22,color=FG,leading=None):
    words=s.split();line='';lines=[];f=F[size]
    for word in words:
        candidate=(line+' '+word).strip()
        if draw.textlength(candidate,font=f)>width and line:lines.append(line);line=word
        else:line=candidate
    if line:lines.append(line)
    for i,line in enumerate(lines):tx(draw,x,y+i*(leading or size+7),line,size,color)
    return y+len(lines)*(leading or size+7)
def box(draw,xy,fill=PANEL,outline='#2a405b',radius=13):draw.rounded_rectangle(xy,radius,fill=fill,outline=outline,width=1)
def arrow(draw,a,b,color=TEAL,width=3):
    draw.line([a,b],fill=color,width=width);angle=math.atan2(b[1]-a[1],b[0]-a[0]);length=10
    draw.polygon([b,(b[0]-length*math.cos(angle-.5),b[1]-length*math.sin(angle-.5)),(b[0]-length*math.cos(angle+.5),b[1]-length*math.sin(angle+.5))],fill=color)
def stat(draw,x,y,value,label,color=TEAL,w=260):
    box(draw,(x,y,x+w,y+105));tx(draw,x+16,y+12,value,36,color,True);tx(draw,x+16,y+61,label,20,MUTED)
def plot(draw,xy,series,xmin,xmax,ymin,ymax,xlabel='',ylabel='',cursor=None):
    x0,y0,x1,y1=xy;draw.rectangle(xy,fill='#0c192b')
    def point(x,y):return (x0+(x-xmin)/(xmax-xmin)*(x1-x0),y1-(y-ymin)/(ymax-ymin)*(y1-y0))
    for n in range(5):
        xx=x0+n*(x1-x0)/4;yy=y0+n*(y1-y0)/4
        draw.line((xx,y0,xx,y1),fill='#26364b');draw.line((x0,yy,x1,yy),fill='#26364b')
        tx(draw,xx-12,y1+7,f'{xmin+n*(xmax-xmin)/4:.1f}',16,MUTED)
        tx(draw,x0-42,yy-9,f'{ymax-n*(ymax-ymin)/4:.1f}',16,MUTED)
    for values,color,width in series:
        pts=[point(x,y) for x,y in values if xmin<=x<=xmax]
        if len(pts)>1:draw.line(pts,fill=color,width=width)
    if cursor is not None:
        px=point(cursor,ymin)[0];draw.line((px,y0,px,y1),fill=FG,width=1)
    tx(draw,x0,y0-29,ylabel,18,MUTED);tx(draw,x1-130,y1+30,xlabel,18,MUTED)
    return point
def route(draw,rows,index,xy,color=TEAL,show_patch=True):
    x0,y0,x1,y1=xy
    xmax=max(r['ref_x_m'] for r in rows)+.2;ymax=max(max(r['ref_y_m'],r['y_m']) for r in rows)+.1
    point=plot(draw,xy,[],0,max(1.,xmax),-.08,max(.3,ymax),'x (m)','y (m)')
    if show_patch:
        a=point(.8,0)[0];b=point(2.3,0)[0];draw.rectangle((a,y0,b,y1),fill='#283b4b')
        tx(draw,a+5,y0+7,'SLIPPERY PATCH',16,AMBER)
    pts=[point(r['ref_x_m'],r['ref_y_m']) for r in rows]
    for k in range(0,len(pts)-2,6):draw.line(pts[k:k+3],fill='#71859d',width=2)
    path=[point(r['x_m'],r['y_m']) for r in rows[:index+1]]
    if len(path)>1:draw.line(path,fill=color,width=3)
    r=rows[index];px,py=point(r['x_m'],r['y_m']);yaw=-r['yaw_rad']
    corners=[(-12,-8),(12,-8),(12,8),(-12,8)]
    draw.polygon([(px+math.cos(yaw)*a-math.sin(yaw)*b,py+math.sin(yaw)*a+math.cos(yaw)*b) for a,b in corners],fill=color)
    return r
def paste_fit(im,picture,xy):
    x0,y0,x1,y1=xy;p=picture.copy()
    if p.mode=='RGBA':
        bounds=p.getbbox()
        if bounds:p=p.crop(bounds)
    p=ImageOps.contain(p,(x1-x0,y1-y0),Image.Resampling.LANCZOS)
    at=(x0+(x1-x0-p.width)//2,y0+(y1-y0-p.height)//2)
    im.paste(p,at,p if p.mode=='RGBA' else None)

def frame(ch,p,elapsed,total):
    im=Image.new('RGB',(W,H),BG);d=ImageDraw.Draw(im)
    tx(d,42,22,ch['phase'],18,TEAL,True);tx(d,42,52,ch['title'],36,FG,True)
    tx(d,1050,29,'MEASURED DEMO',16,MUTED)
    key=ch['key']
    if key=='intro':
        box(d,(42,126,815,565));r=route(d,TRACES['D'],round(p*(len(TRACES['D'])-1)),(94,178,760,492),AMBER)
        tx(d,92,523,'Recorded rover path + reference',22,MUTED)
        stat(d,850,140,'540 / 540','Completed routes',w=382)
        stat(d,850,270,'Linear + nonlinear','Control methods',w=382)
        stat(d,850,400,'No physical hardware','Virtual deployment',w=382)
    elif key=='architecture':
        nodes=[(52,144,'Independent sensors','Delayed pose + encoders + IMU'),(457,144,'Trajectory controller','LQR or nonlinear, 50 Hz'),(862,144,'Wheel PI control','200 Hz + anti-windup'),(862,358,'Virtual controller PCB','ADC / PWM / delay / fault gate'),(457,358,'Motor + contact plant','1 kHz; wheel/body states'),(52,358,'Ground-truth evaluator','Metrics only; not controller input')]
        for x,y,title,body in nodes:
            box(d,(x,y,x+350,y+139));tx(d,x+18,y+18,title,24,FG,True);wrap(d,x+18,y+65,body,315,22,MUTED)
        for a,b in [((402,213),(457,213)),((807,213),(862,213)),((1037,283),(1037,358)),((862,427),(807,427)),((457,427),(402,427))]:arrow(d,a,b)
        tx(d,60,534,'12 kg base + 0/5/10 kg payload    |    24 V motors    |    75 mm wheels',24,AMBER)
    elif key=='linear':
        box(d,(42,128,842,560));i=round(p*(len(TRACES['A'])-1));r=route(d,TRACES['A'],i,(98,190,796,473),BLUE)
        tx(d,94,517,f"Recorded time: {r['time_s']:.2f} s",22,FG)
        stat(d,878,137,'A / LQR','Supervisor off',BLUE,354)
        stat(d,878,267,f"{r['cross_track_m']*1000:.1f} mm",'Current lateral error',BLUE,354)
        stat(d,878,397,'8.76 mm','Worst dry matrix RMSE',TEAL,354)
    elif key=='nonlinear':
        i=round(p*(len(TRACES['D'])-1));r=TRACES['D'][i]
        box(d,(42,128,712,560));route(d,TRACES['D'],i,(93,192,663,474),AMBER)
        tx(d,91,514,f"D replay: {r['time_s']:.2f} s",22)
        box(d,(743,128,1238,560));tx(d,769,153,'True slip speed, same route',22,FG,True)
        vals=[([(a['time_s'],a['true_slip_speed_m_s']) for a in TRACES[v][:i+1]],COLORS[v],3) for v in 'CD']
        ymax=max(a['true_slip_speed_m_s'] for v in 'CD' for a in TRACES[v])*1.12
        plot(d,(799,216,1192,440),vals,0,16,0,max(.2,ymax),'time (s)','m/s',r['time_s'])
        tx(d,770,494,'C: no supervisor',20,PURPLE);tx(d,1000,494,'D: supervised',20,AMBER)
        tx(d,770,527,'Supervisor '+('ACTIVE' if r['supervisor_active'] else 'monitoring'),20,AMBER if r['supervisor_active'] else TEAL)
    elif key=='comparison':
        specs=[('mean_rmse_m',1000,'Mean lateral RMSE (mm)',12),('mean_slip_m',1,'Mean integrated slip (m)',.26),('mean_energy_j',1,'Mean bus energy (J)',520)]
        for n,(field,scale,title,maximum) in enumerate(specs):
            left=42+n*402;box(d,(left,130,left+381,495));tx(d,left+16,150,title,22,FG,True)
            for j,v in enumerate('ABCD'):
                value=SUMMARY['summary'][v][field]*scale;height=value/maximum*226;xx=left+34+j*82
                d.rectangle((xx,441-height,xx+48,441),fill=COLORS[v]);tx(d,xx-4,451,v,22,COLORS[v],True)
                tx(d,xx-6,441-height-27,f'{value:.3f}' if field=='mean_slip_m' else f'{value:.2f}',18,FG)
        tx(d,55,522,'Low-traction slip reduction: LQR 18.76%  |  Nonlinear 18.48%',26,TEAL,True)
        tx(d,55,557,'Bars show all matrix runs; reduction percentages use low-traction cases only.',18,MUTED)
    elif key=='ros':
        for x,y,title,body,color in [(52,159,'PlantNode','Noisy sensors + /odom + /tf',BLUE),(466,159,'ControllerNode','/amr/observation -> targets',AMBER),(878,159,'ROS monitor','Subscribe, service, record',TEAL)]:
            box(d,(x,y,x+350,y+126));tx(d,x+18,y+16,title,26,color,True);wrap(d,x+18,y+64,body,314,20,MUTED)
        arrow(d,(402,221),(466,221));arrow(d,(878,245),(816,245));arrow(d,(635,292),(635,336))
        box(d,(442,337,822,417));tx(d,460,350,'/controller/use_nonlinear',24);tx(d,460,383,'SetBool service: successful',20,TEAL)
        stat(d,53,451,str(ROS['messages']['odom']),'Odom observed (incl. replay)',BLUE,367)
        stat(d,455,451,str(ROS['replayed_odom_messages']),'Replayed odometry messages',TEAL,367)
        stat(d,855,451,f"{ROS['body_displacement_m']:.2f} m",'Measured body displacement',AMBER,367)
        tx(d,55,315,'TESTED GRAPH / EXPLANATORY DIAGRAM',16,MUTED)
    elif key=='pcb':
        box(d,(42,123,797,570));paste_fit(im,PCB_IMAGES[0 if p<.42 else 1],(58,134,782,550));d=ImageDraw.Draw(im)
        tx(d,828,143,'Pico controller carrier',26,TEAL,True)
        items=[('29 components / 29 nets',FG),('96 x 96 mm, two copper layers',MUTED),('External motor power stages',MUTED),('Encoders + IMU + UART',MUTED),('Current RC filters + fault latch',MUTED),(f'ERC: {len(erc_violations())} violations',TEAL),(f"Unconnected items: {len(DRC['unconnected_items'])}",TEAL),(f"DRC: {DRC_COUNTS['error']} errors / {DRC_COUNTS['warning']} warnings",AMBER)]
        for k,(line,color) in enumerate(items):tx(d,828,197+k*40,line,22,color)
        box(d,(828,526,1236,571),fill='#20382e',outline='#456a51');tx(d,842,535,'LOCAL ERC / DRC: ZERO VIOLATIONS',18,TEAL,True)
    elif key=='circuit':
        box(d,(42,132,581,552));tx(d,66,153,'Current-sense path',26,FG,True)
        d.line((81,273,152,273),fill=TEAL,width=3);d.rectangle((152,258,266,288),outline=TEAL,width=3);d.line((266,273,483,273),fill=TEAL,width=3)
        d.line((368,273,368,349),fill=TEAL,width=3);d.line((340,349,397,349),fill=TEAL,width=3);d.line((340,362,397,362),fill=TEAL,width=3);d.line((368,362,368,406),fill=TEAL,width=3)
        for k,width in enumerate([43,28,12]):d.line((368-width/2,406+k*8,368+width/2,406+k*8),fill=TEAL,width=2)
        tx(d,174,218,'1 kohm',22);tx(d,404,349,'1 uF',22);tx(d,82,309,'Driver',20,MUTED);tx(d,445,309,'ADC',20,MUTED)
        tx(d,65,465,'1.65 V center + 0.1 V/A',26,AMBER,True);tx(d,65,508,'12-bit resolution: 8.06 mA',22,MUTED)
        box(d,(611,132,1238,552));tx(d,636,153,'Actual ngspice transient',26,FG,True)
        values=[(float(row[0])*1000,float(row[2])) for row in SPICE_TRACE if row[0]<=.006]
        plot(d,(676,231,1183,451),[(values,TEAL,3)],0,6,1.5,2.8,'time (ms)','ADC voltage (V)')
        tx(d,642,509,f"Measured RC tau: {SPICE['measured_tau_s']*1000:.5f} ms",24,TEAL,True)
    elif key=='faults':
        rows=FAULT_TRACE;i=round(p*(len(rows)-1));r=rows[i]
        box(d,(42,127,618,560));tx(d,66,149,'Recorded overcurrent run',24,FG,True)
        plot(d,(100,221,574,452),[([(a['time_s'],a['v_m_s']) for a in rows[:i+1]],BLUE,3)],0,16,0,.8,'time (s)','body speed (m/s)',r['time_s'])
        tx(d,66,512,f"t={r['time_s']:.2f} s | Drive {'ON' if r['drive_enabled'] else 'DISABLED'}",24,TEAL if r['drive_enabled'] else AMBER,True)
        box(d,(645,127,1238,560));tx(d,665,149,'Separate dry, straight fault cases',22,FG,True)
        tx(d,665,195,'Fault',18,MUTED);tx(d,943,195,'Delay',18,MUTED);tx(d,1055,195,'Coast',18,MUTED)
        for k,f in enumerate(FAULTS):
            y=235+k*51;name={'overcurrent':'Overcurrent','command_timeout':'Command timeout','encoder_dropout':'Encoder dropout','localization_stale':'Stale localization','imu_bias':'IMU bias'}[f['fault']]
            tx(d,665,y,name,22);tx(d,943,y,f"{(f['fault_disable_time_s']-5)*1000:.0f} ms",22,TEAL);tx(d,1055,y,f"{f['fault_stopping_distance_m']:.3f} m",22,AMBER)
        tx(d,664,511,'No modeled emergency / parking brake',20,AMBER)
    elif key=='live':
        for k,v in enumerate('ABCD'):
            y=149+k*92;t=LIVE[v]['timing'];box(d,(52,y,1228,y+78));tx(d,75,y+16,v,30,COLORS[v],True)
            tx(d,135,y+12,f"p99 compute {t['compute_p99_ms']:.3f} ms",24);tx(d,544,y+12,f"max {t['compute_max_ms']:.3f} ms",24)
            tx(d,873,y+12,f"{t['compute_deadline_misses']} misses",24,TEAL,True)
            tx(d,135,y+44,f"Wall duration {t['wall_seconds']:.3f} s; wake p99 {t['wake_lateness_p99_ms']:.3f} ms",18,MUTED)
        tx(d,57,534,'20 ms compute deadline | Ordinary Windows scheduling | Saved timing logs',22,AMBER)
    elif key=='phases':
        for k,(number,status,title,result) in enumerate(PHASES):
            y=125+k*55;box(d,(42,y,1238,y+49),radius=6)
            tx(d,57,y+9,f'{number}',22,TEAL,True);tx(d,104,y+9,title,22)
            tx(d,948,y+9,status.upper(),20,TEAL if status=='Verified' else AMBER,True)
    else:
        tx(d,57,147,'WHAT YOU CAN REVIEW NOW',22,TEAL,True)
        for k,(label,detail) in enumerate([('Narrated video','Recorded motion, comparisons, ROS, PCB and faults'),('Phase report','Measured results, limitations and reproduction guide'),('Editable PCB','KiCad 10 source, schematic and actual 3D renders'),('Engineering scope','Virtual prototype; industry intent, no certification')]):
            y=202+k*86;box(d,(52,y,1228,y+71));tx(d,73,y+13,label,26,FG,True);tx(d,395,y+18,detail,22,MUTED)
    box(d,(42,594,1238,674),fill='#101c2e');wrap(d,61,605,ch['caption'],1152,22,MUTED,29)
    d.rectangle((42,698,1238,702),fill='#22354a');d.rectangle((42,698,42+1196*elapsed/total,702),fill=TEAL)
    tx(d,1105,668,f'{int(elapsed)//60:02d}:{int(elapsed)%60:02d} / {int(total)//60:02d}:{int(total)%60:02d}',16,MUTED)
    return im

def audio_schedule():
    durations=[];audio=[];rate=22050
    for ch in CHAPTERS:
        path=WORK/(ch['key']+'.wav')
        with wave.open(str(path),'rb') as wav:
            assert wav.getnchannels()==1 and wav.getsampwidth()==2
            original_rate=wav.getframerate();samples=np.frombuffer(wav.readframes(wav.getnframes()),dtype='<i2').copy()
        if original_rate!=rate:
            samples=np.interp(np.arange(round(len(samples)*rate/original_rate))*original_rate/rate,np.arange(len(samples)),samples).astype('<i2')
        length=max(ch['minimum'],len(samples)/rate+1.2);length=math.ceil(length*FPS)/FPS
        padding=np.zeros(round(length*rate)-len(samples),dtype='<i2')
        # 0.4 seconds of silence lets the chapter settle before narration begins.
        lead=np.zeros(round(.4*rate),dtype='<i2');tail=padding[len(lead):]
        audio.extend([lead,samples,tail]);durations.append(length)
    with wave.open(str(WORK/'narration.wav'),'wb') as wav:
        wav.setnchannels(1);wav.setsampwidth(2);wav.setframerate(rate);wav.writeframes(np.concatenate(audio).tobytes())
    return durations

def build_video():
    durations=audio_schedule();total=sum(durations);ffmpeg=imageio_ffmpeg.get_ffmpeg_exe()
    command=[ffmpeg,'-y','-f','rawvideo','-vcodec','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r',str(FPS),'-i','-',
      '-i',str(WORK/'narration.wav'),'-c:v','libx264','-preset','fast','-crf','20','-pix_fmt','yuv420p','-c:a','aac','-b:a','128k',
      '-movflags','+faststart','-shortest',str(OUT/'traction-aware-amr-demo.mp4')]
    log=(WORK/'encode.log').open('w');process=subprocess.Popen(command,stdin=subprocess.PIPE,stdout=log,stderr=log)
    elapsed=0.;timeline=[]
    for ch,duration in zip(CHAPTERS,durations):
        count=round(duration*FPS);timeline.append(dict(key=ch['key'],title=ch['title'],start_s=elapsed,duration_s=duration,narration=ch['narration']))
        for n in range(count):
            progress=min(1.,n/max(1,count-1));image=frame(ch,progress,elapsed+n/FPS,total)
            process.stdin.write(image.tobytes())
            if n==count//2:image.save(WORK/(ch['key']+'-preview.png'))
        print(f"Rendered {ch['key']}: {duration:.1f} s",flush=True);elapsed+=duration
    process.stdin.close();returncode=process.wait();log.close()
    if returncode:raise RuntimeError((WORK/'encode.log').read_text()[-3000:])
    (OUT/'chapters.json').write_text(json.dumps(timeline,indent=2),encoding='utf-8')
    (OUT/'transcript.md').write_text('# Video transcript\n\n'+'\n\n'.join(f"## {int(c['start_s'])//60:02d}:{int(c['start_s'])%60:02d} - {c['title']}\n\n{c['narration']}" for c in timeline),encoding='utf-8')
    def timestamp(t):return f'{int(t)//3600:02d}:{int(t)%3600//60:02d}:{int(t)%60:02d},{round((t%1)*1000):03d}'
    subtitles=[];number=0
    for c in timeline:
        sentences=re.split(r'(?<=[.!?])\s+',c['narration']);weight=sum(len(s) for s in sentences);at=c['start_s']+.4
        for sentence in sentences:
            duration=(c['duration_s']-1.2)*len(sentence)/weight;number+=1
            subtitles.append(f'{number}\n{timestamp(at)} --> {timestamp(at+duration)}\n{textwrap.fill(sentence,85)}\n');at+=duration
    (OUT/'traction-aware-amr-demo.srt').write_text('\n'.join(subtitles),encoding='utf-8')
    poster=frame(CHAPTERS[0],.55,0,total);poster.save(OUT/'poster.png')
    print(json.dumps({'video':str(OUT/'traction-aware-amr-demo.mp4'),'duration_s':total,'frames':round(total*FPS)},indent=2),flush=True)

def audit():
    assert MATRIX['count']==540 and len(MATRIX['runs'])==540
    keys={(r['variant'],r['surface'],r['payload_kg'],r['trajectory'],r['seed']) for r in MATRIX['runs']};assert len(keys)==540
    assert all(r['finite'] and r['completion'] for r in MATRIX['runs'])
    for v in 'ABCD':
        group=[r for r in MATRIX['runs'] if r['variant']==v]
        for source,target in [('cross_track_rmse_m','mean_rmse_m'),('integrated_slip_m','mean_slip_m'),('energy_j','mean_energy_j')]:
            assert abs(np.mean([r[source] for r in group])-SUMMARY['summary'][v][target])<1e-9
        assert LIVE[v]['timing']['compute_deadline_misses']==0 and 15.5<LIVE[v]['timing']['wall_seconds']<16.5
    for off,on in [('A','B'),('C','D')]:
        means=[np.mean([r['integrated_slip_m'] for r in MATRIX['runs'] if r['variant']==v and r['surface']!='dry']) for v in [off,on]]
        assert abs(100*(1-means[1]/means[0])-SUMMARY['slip_reduction_percent'][off+'_to_'+on])<1e-9
    assert len(FAULTS)==5 and all(f['finite'] and not f['drive_enabled'] and 5<=f['fault_disable_time_s']<=5.3 for f in FAULTS)
    root=ET.parse(ROOT/'results/pytest.xml').getroot();suites=list(root.iter('testsuite'))
    tests=sum(int(s.attrib['tests']) for s in suites);assert tests==15
    assert all(int(s.attrib.get('failures',0))==0 and int(s.attrib.get('errors',0))==0 for s in suites)
    files=['results/matrix.json','results/pytest.xml','results/ros_smoke.json','results/gazebo_smoke.json','results/spice.json','results/erc.json','results/drc.json','results/faults.json','hardware/spice/current_filter.dat','hardware/kicad/traction_carrier.kicad_pcb','hardware/kicad/traction_carrier.kicad_sch','hardware/exports/carrier-top.png','hardware/exports/carrier-isometric.png','results/trace_D_overcurrent.csv']+[f'results/{name}_{v}.{ext}' for v in 'ABCD' for name,ext in [('live','json'),('trace','csv')]]
    result={'matrix_runs':540,'unique_matched_cases':540,'completed':540,'local_regressions_passed':tests,
      'erc_violations':len(erc_violations()),'drc_errors':DRC_COUNTS['error'],'drc_warnings':DRC_COUNTS['warning'],
      'drc_unconnected_items':len(DRC['unconnected_items']),'schematic_parity_issues':len(DRC['schematic_parity']),'gazebo_contact_status':'passed; recovered from successful saved ROS/Gazebo run 36900851054',
      'github_verification_tests':'manual; prior failures ignored at user request','source_sha256':{p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in files}}
    (PDF/'evidence.json').write_text(json.dumps(result,indent=2),encoding='utf-8');return result

def build_report():
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet,ParagraphStyle
    from reportlab.lib.enums import TA_LEFT
    from reportlab.lib.units import mm
    from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle,PageBreak,Image as PdfImage
    evidence=audit();assert not DRC['schematic_parity'];styles=getSampleStyleSheet()
    styles.add(ParagraphStyle(name='TitleAMR',fontName='Helvetica-Bold',fontSize=26,leading=31,textColor=colors.HexColor('#15374e'),spaceAfter=15))
    styles.add(ParagraphStyle(name='HeadAMR',fontName='Helvetica-Bold',fontSize=17,leading=21,textColor=colors.HexColor('#15374e'),spaceAfter=10))
    styles.add(ParagraphStyle(name='BodyAMR',fontName='Helvetica',fontSize=9.5,leading=14,spaceAfter=9))
    styles.add(ParagraphStyle(name='SmallAMR',fontName='Helvetica',fontSize=8,leading=11,spaceAfter=7))
    story=[]
    def p(s,style='BodyAMR'):return Paragraph(s,styles[style])
    def add(s,style='BodyAMR'):story.append(p(s,style))
    def table(rows,widths,fontsize=8.3):
        converted=[[p(str(c),'SmallAMR') for c in row] for row in rows]
        tab=Table(converted,colWidths=widths,repeatRows=1,hAlign='LEFT')
        tab.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#e5eff3')),('VALIGN',(0,0),(-1,-1),'TOP'),('LINEBELOW',(0,0),(-1,0),.7,colors.HexColor('#446a7e')),('LINEBELOW',(0,1),(-1,-1),.3,colors.HexColor('#c4d2db')),('LEFTPADDING',(0,0),(-1,-1),6),('RIGHTPADDING',(0,0),(-1,-1),6),('TOPPADDING',(0,0),(-1,-1),7),('BOTTOMPADDING',(0,0),(-1,-1),6)]))
        story.append(tab);story.append(Spacer(1,10))
    def heading(s):add(s,'HeadAMR')
    def page():story.append(PageBreak())
    def image_file(path,width):
        with Image.open(path) as im:height=width*im.height/im.width
        story.append(PdfImage(str(path),width=width,height=height));story.append(Spacer(1,10))
    add('Traction-aware<br/>warehouse rover','TitleAMR')
    add('Measured virtual-prototype demo and phase report | 2 October 2026','SmallAMR')
    add('A software-only project combining linear PI/LQR, nonlinear tracking, traction supervision, real ROS 2 messaging, and an editable virtual controller PCB. The interactive website, narrated demo, editable KiCad project and phase evidence are delivered through GitHub. Automated GitHub verification tests remain manual at the user\'s request.')
    table([['Executed evidence','Result'],['Matched simulations','540 unique cases; 540 completed routes; all states finite'],['Local regressions','15 passed; zero failures/errors in saved JUnit results'],['Recorded wall-clock tests','Four approximately 16 s runs; zero 20 ms compute-budget misses'],['ROS 2 integration','DDS/TF, controller-selection service, bag record/replay executed'],['KiCad / circuit',f"KiCad 10.0.6; ERC 0; DRC {DRC_COUNTS['error']} errors / {DRC_COUNTS['warning']} warnings; RC tau 1.00116 ms"],['Gazebo contact','Torque commands moved the body; low-friction wheel/body divergence increased']],[155,355])
    # Put transparent KiCad render onto a white page for consistent PDF output.
    white=Image.new('RGB',PCB_IMAGES[1].size,'white');white.paste(PCB_IMAGES[1],mask=PCB_IMAGES[1].getchannel('A'));white.save(WORK/'pcb-pdf.png')
    image_file(WORK/'pcb-pdf.png',280)
    add('Actual local KiCad render of the 29-component Pico carrier. Library keepouts, pad clearance and via drills are respected. Local rule checks pass; manufacturing readiness and physical performance require further validation.','SmallAMR')
    page();heading('Results by phase')
    table([['Phase','Status','Work and verified result']]+[[str(n),status,f'<b>{title}</b><br/>{result}'] for n,status,title,result in PHASES],[37,69,404])
    add('A phase marked Verified has executed evidence for its stated software scope. The 20% slip-reduction hypothesis was not met. Zero local PCB violations does not establish physical performance or formal standards conformance.')
    heading('Project purpose and standards intent')
    add('Slippery patches and varying payloads can make wheel speed a poor proxy for body motion. The project addresses that issue with independent velocity estimation and torque/acceleration derating, using an inspectable digital model and matched comparisons.')
    add('Design intent is mapped to IPC-2221/IPC-2152 (PCB design), ISO 12100 (hazards), ISO 3691-4 (driverless trucks), ISO 13849-1 (fault-response separation), and ROS REP 103/105 (units/frames). Paid standard texts were not reviewed clause by clause. This is scope-level alignment, not conformance or certification.')
    page();heading('Model and control methods')
    table([['Item','Implemented setting'],['Plant','Independent x/y/yaw, body speed/yaw rate, wheel speeds and motor currents'],['Mechanical / electrical','12 kg base; 0/5/10 kg payload; 75 mm wheels; 380 mm axle; 24 V; R 1.5 ohm; L 3 mH; kt/ke 0.12'],['Sampling rates','Plant 1 kHz; wheel PI 200 Hz; estimator / outer control 50 Hz'],['Traction scenarios','Dry mu 0.8; patch mu 0.1; asymmetric left/right friction'],['Sensor boundary','Noisy delayed independent pose, quantized encoders and IMU estimates; truth only for sensor generation/evaluation'],['Board model','Signed centered 12-bit ADC; 12-bit PWM; 10 ms command delay; 1 ms RC; 100 ms watchdog; independent latched 16 A trip']],[139,371])
    add('<b>Linear:</b> wheel PI with anti-windup, plus moving-reference LQR at 0.45 m/s. Q = diag(3.24, 6.25, 2.25), R = I. Controllability and negative closed-loop eigenvalue real parts are checked. Stopping uses a separate bounded alignment mode.')
    add('<b>Nonlinear:</b> v = vr cos(epsi) + 1.8 ex; yaw rate = wr + 5 vr ey + 2 sin(epsi). A nominal no-slip Lyapunov argument supports local behavior; it does not prove global convergence with saturation, delay, slip or faults.')
    add('<b>Traction supervision:</b> sensor-derived slip threshold 0.22 with 60 ms persistence; recovery threshold 0.12. Active derating lowers torque from 1.44 to 0.32 Nm and acceleration from 1.8 to 0.25 m/s^2. The route uses a shared 2.2-4.6 s acceleration/braking demand to exercise traction.')
    add('<b>Model limits:</b> no lateral tire-slip, tipping, suspension, thermal or detailed battery model. Coasting follows loss of drive; no emergency or parking brake is modeled.')
    page();heading('Matched controller comparison')
    add('540 cases = 4 variants x 3 surfaces x 3 payloads x 3 routes x 5 noise seeds. A/B use LQR, C/D nonlinear tracking. B/D enable supervision. All four groups completed 135/135 routes.')
    rows=[['Variant','Mean RMSE (mm)','Mean integrated slip (m)','Mean energy (J)']]
    for v in 'ABCD':
        s=SUMMARY['summary'][v];rows.append([v,f"{s['mean_rmse_m']*1000:.3f}",f"{s['mean_slip_m']:.5f}",f"{s['mean_energy_j']:.2f}"])
    table(rows,[70,135,170,135]);image_file(ROOT/'results/comparison.png',510)
    add('Low-traction integrated-slip reduction, calculated only on patch/asymmetric cases: <b>18.76% LQR (A to B)</b> and <b>18.48% nonlinear (C to D)</b>. The bars/table above average all surfaces, including dry cases; their percent difference therefore differs.')
    add('<b>The predeclared 20% reduction hypothesis was not met.</b> All recorded runs remained finite and completed, and supervised dry runs had no supervisor activation. This is evidence for the modeled scenarios, not a general guarantee across floors or robots.')
    page();heading('ROS integration and warehouse validation')
    table([['Actual ROS check','Saved result'],['Observed messages, including replay',f"Odometry {ROS['messages']['odom']}; commands {ROS['messages']['commands']}; TF {ROS['messages']['tf']}"],['Bag replay',f"{ROS['replayed_odom_messages']} replayed odometry messages; metadata created"],['Controller-selection service','SetBool call successful'],['Body displacement',f"{ROS['body_displacement_m']:.6f} m"],['Test elapsed, including replay',f"{ROS['elapsed_live_s']:.3f} s"]],[224,286])
    add('The graph contains separate PlantNode and ControllerNode processes/classes, timestamped odometry, /tf, /clock, wheel-state/IMU messages, diagnostics, parameters, a controller-selection service and a reset service. The test used actual ROS 2 Jazzy middleware and recorded/replayed a bag. The explanatory graph in the video is an illustration of that tested data path, not a live ROS screen capture.')
    add(f"<b>Gazebo:</b> the corrected inertia ran successfully in saved run 36900851054. Both worlds received 0.8 Nm wheel effort through ros_gz_bridge. Dry displacement: {GAZEBO[0]['displacement_m']:.3f} m; low-friction displacement: {GAZEBO[1]['displacement_m']:.3f} m. Wheel/body divergence increased from {GAZEBO[0]['wheel_body_divergence_m_s']:.3f} to {GAZEBO[1]['wheel_body_divergence_m_s']:.3f} m/s. Evidence was recovered from the existing successful run; no new GitHub test was launched. This checks contact response separately from the 540-case mathematical-plant study.")
    heading('ROS reproduction commands')
    add('On a ROS 2 Jazzy Linux environment, source /opt/ros/jazzy/setup.bash; install the root Python package; run colcon build --symlink-install from ros_ws; source install/setup.bash; then run python tools/ros_smoke.py from the project root. See the repository workflow for exact environment setup. A fresh bag output folder is required for repeated recordings.','SmallAMR')
    add('Key interfaces: /amr/observation, /reference, /drive/wheel_targets, /odom, /tf, /clock, /controller/use_nonlinear and /amr/reset. SI units and map -> odom -> base_link frame ownership follow the documented REP design intent.','SmallAMR')
    page();heading('Virtual PCB, analog circuit and local KiCad')
    add('The editable carrier uses a Raspberry Pi Pico, 74HC08 gating and a 74HC74 latch, seven connectors, RC current-sense filtering, bus-voltage divider, I2C pullups and decoupling. Motor current flows in external power drivers. Their centered 0.1 V/A current outputs and active-low driver faults are interface assumptions.')
    table([['Local artifact/check','Actual result'],['KiCad version','10.0.6'],['Carrier geometry','96 x 96 mm; two copper layers; 29 components; 29 connected nets + 18 no-connect nets'],['Schematic ERC',f'{len(erc_violations())} violations'],['PCB connectivity',f"{len(DRC['unconnected_items'])} unconnected items"],['PCB DRC',f"{DRC_COUNTS['error']} errors; {DRC_COUNTS['warning']} warnings"],['Exports','Top and angled component renders; board-only STEP; schematic SVG'],['Analog RC expected / measured','1.00000 ms / 1.00116 ms'],['Analog final voltage','2.64909 V for a 1.65 -> 2.65 V sense-source step']],[168,342])
    rows=[['DRC finding','Count']]+([[f'{severity}: {kind}',str(count)] for (severity,kind),count in sorted(DRC_TYPES.items())] or [['No layout violations','0']])
    table(rows,[400,110]);add('The local router respects library copper keepouts, rotated pad bounds, separate copper clearance, and drill spacing. Through-hole pads can connect on either copper layer; existing vias are reused and collinear segments are merged. DRC and ERC pass without suppressing the previous keepout, shorting or drilling defects. The full project includes editable source, Gerbers, drills and a STEP export. Physical fabrication and assembled-board validation remain outside this virtual project.')
    add('Ngspice simulates the RC measurement chain driven by an ideal external-driver sense source. Digital trip/watchdog/ADC/PWM behavior is checked in the virtual board model. These are separate evidence sources; a complete assembled-board SPICE simulation, EMI validation and physical timing measurements were not performed.')
    page();heading('Live pacing and injected faults')
    rows=[['Variant','Wall duration (s)','p99 / max compute (ms)','Misses / wake p99 (ms)']]
    for v in 'ABCD':
        t=LIVE[v]['timing'];rows.append([v,f"{t['wall_seconds']:.3f}",f"{t['compute_p99_ms']:.3f} / {t['compute_max_ms']:.3f}",f"{t['compute_deadline_misses']} / {t['wake_lateness_p99_ms']:.3f}"])
    table(rows,[53,124,173,160]);add('The 20 ms compute budget was met in all four saved Windows runs. Wall duration is approximately 15.98 s because the first simulated block starts at wall time zero and the last block begins at 15.98 s. Wake lateness is separate from compute duration. This does not demonstrate a hard real-time kernel or guaranteed future deadlines.')
    rows=[['Fault, injected at 5 s','Drive off at (s)','Response (ms)','Modeled coast (m)']]
    for f in FAULTS:rows.append([f['fault'],f"{f['fault_disable_time_s']:.3f}",f"{(f['fault_disable_time_s']-5)*1000:.0f}",f"{f['fault_stopping_distance_m']:.3f}"])
    table(rows,[188,112,105,105]);add('All five fault cases remained finite and disabled drive. These are separate dry, straight-route cases. The fault animation in the video replays a recorded Linux curved-route overcurrent test; its trace is not the source of the dry-case coast distances in this table.')
    add('Power cut permits electrical current decay and body coasting. The distance starts at fault injection and accumulates subsequent simulated travel. These values are not safe-stop or certified industrial braking distances. No physical brake is modeled.')
    page();heading('Delivered files and reproduction')
    table([['Deliverable','Project-relative location'],['Narrated H.264 / AAC demo','output/video/traction-aware-amr-demo.mp4'],['Chapter transcript / subtitles','output/video/transcript.md; traction-aware-amr-demo.srt'],['This PDF / evidence hashes','output/pdf/traction-aware-amr-report.pdf; evidence.json'],['Editable schematic / PCB','hardware/kicad/traction_carrier.kicad_sch; traction_carrier.kicad_pcb'],['KiCad renders / geometry','hardware/exports/carrier-top.png; carrier-isometric.png; carrier.step'],['Saved measurements','results/matrix.json; live_A/B/C/D.json; faults.json; ros_smoke.json; spice.json; erc.json; drc.json']],[158,352])
    add('Local software commands: install requirements.txt in Python 3.12 with a compatible native compiler; python -m pytest -q; python -m amr.experiments matrix --workers 4; python -m amr.experiments live --variant D --seconds 16; python -m amr.experiments faults. These commands are for reproduction; they were not rerun for this video assembly.')
    add('Video reproduction uses tools/demo_chapters.py, tools/narrate.py (installed Windows SAPI voice through comtypes), and tools/build_demo.py --video. PDF reproduction uses tools/build_demo.py --report. Additional local authoring dependencies: Pillow, imageio-ffmpeg, comtypes, reportlab and pypdf. Video animations use recorded traces and actual local KiCad renders. Narration is computer-generated; caption callouts and the transcript are included.')
    add('Project repository: <link href="https://github.com/Snow-Warrior07/traction-aware-amr" color="#116273">github.com/Snow-Warrior07/traction-aware-amr</link>. Interactive demo: <link href="https://snow-warrior07.github.io/traction-aware-amr/" color="#116273">snow-warrior07.github.io/traction-aware-amr/</link>. GitHub profile links to the project. The website includes downloads for this report, KiCad project, Gerbers, evidence and narrated demo. output/publication.json records the verified deployment.')
    heading('Evidence and standards references')
    add('The accompanying evidence.json records SHA-256 hashes of the exact input measurements and KiCad files used. Principal evidence: 540-case matrix, 15-test JUnit output, four local paced-run JSON/CSV pairs, five-fault JSON, ROS smoke JSON, ngspice JSON/data, and local KiCad ERC/DRC JSON. A green job status or an unexecuted source file was not used to infer an engineering pass.','SmallAMR')
    add('Primary scope references: IPC design standards (ipc.org/ipc-design-standards); ISO 12100 (iso.org/standard/51528.html); ISO 3691-4 (iso.org/standard/83545.html); ISO 13849-1 (iso.org/standard/73481.html); ROS REP 103/105 (github.com/ros-infrastructure/rep); KiCad CLI reference (docs.kicad.org/10.0/en/cli/cli.html). Existing docs/standards.md gives the project hazard register and limits.','SmallAMR')
    def footer(canvas,doc):
        canvas.setStrokeColor(colors.HexColor('#c5d3dc'));canvas.line(42,40,553,40);canvas.setFont('Helvetica',8);canvas.setFillColor(colors.HexColor('#5e7688'))
        canvas.drawString(42,27,'Traction-aware AMR | Measured virtual prototype | Local delivery');canvas.drawRightString(553,27,str(doc.page))
    document=SimpleDocTemplate(str(PDF/'traction-aware-amr-report.pdf'),pagesize=(595.276,841.89),rightMargin=42,leftMargin=42,topMargin=43,bottomMargin=56,title='Traction-aware warehouse rover - measured phase report',author='Project engineering demonstrator')
    document.build(story,onFirstPage=footer,onLaterPages=footer)
    md=['# Traction-aware AMR: local demo report','', '| Phase | Status | Result |','|---|---|---|']+[f'| {n}. {title} | {status} | {result} |' for n,status,title,result in PHASES]
    md+=['','540/540 matched routes completed; 15 local regression tests passed. Low-traction slip reduction: LQR 18.76%, nonlinear 18.48% (20% hypothesis not met). Four recorded live tests: zero 20 ms compute-budget misses.','',f"Local KiCad: ERC {len(erc_violations())}; unconnected items {len(DRC['unconnected_items'])}; DRC {DRC_COUNTS['error']} errors / {DRC_COUNTS['warning']} warnings. Ngspice RC tau: 1.00116 ms. Actual Gazebo torque/contact checks passed in recovered saved run 36900851054.",'','GitHub verification tests remain manual at the user request. Website: https://snow-warrior07.github.io/traction-aware-amr/ . See output/publication.json for deployment evidence.']
    (ROOT/'output/PHASE_REPORT.md').write_text('\n'.join(md)+'\n',encoding='utf-8')
    print(json.dumps({'report':str(PDF/'traction-aware-amr-report.pdf'),'evidence':evidence},indent=2),flush=True)

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--video',action='store_true');parser.add_argument('--report',action='store_true');args=parser.parse_args()
    if args.video:build_video()
    if args.report:build_report()
