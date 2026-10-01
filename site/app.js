'use strict';
const $ = id => document.getElementById(id);
const names = {A:'LQR', B:'LQR + traction', C:'Nonlinear', D:'Nonlinear + traction'};
const descriptions = {
  A:'Linear outer LQR follows the moving reference. Inner wheel PI uses anti-windup. Traction supervision is off.',
  B:'LQR and wheel PI, with sensor-based slip estimation. Persistent slip reduces torque and acceleration; hysteresis controls recovery.',
  C:'Heading-dependent sine and cosine terms shape the nonlinear tracking command. Inner wheel PI closes the wheel loops.',
  D:'Nonlinear tracking with sensor-based traction supervision. Torque and acceleration are reduced after persistent estimated slip.'
};
const phaseTitles=['Requirements','Plant + warehouse','ROS 2 integration','Linear control','Nonlinear + traction','Virtual PCB','Timing + faults','GitHub delivery'];
let data, variant='D', position=0, playing=false, previousFrame=0;
const ctx=$('scene').getContext('2d'), chart=$('error-chart').getContext('2d');
function baseline(){return variant==='B'?'A':variant==='D'?'C':null;}
function setPlaying(value){playing=value;previousFrame=0;$('play').textContent=value?'Ⅱ':'▶';$('play').setAttribute('aria-label',value?'Pause recorded run':'Play recorded run');}
function line(context, rows, count, transform, color, dash=[], width=2){
  context.strokeStyle=color;context.lineWidth=width;context.setLineDash(dash);context.beginPath();
  rows.slice(0,count).forEach((r,i)=>{const p=transform(r);i?context.lineTo(...p):context.moveTo(...p);});
  context.stroke();context.setLineDash([]);
}
function draw(){
  if(!data)return;
  const rows=data.traces[variant], i=Math.min(Math.floor(position),rows.length-1), r=rows[i], W=900,H=460;
  $('time').max=rows.length-1;$('time').value=i;
  ctx.fillStyle='#142923';ctx.fillRect(0,0,W,H);
  const xmax=Math.max(...rows.map(p=>p.ref_x_m))+.3,ymax=Math.max(...rows.map(p=>Math.max(p.ref_y_m,p.y_m)))+.14;
  const point=(x,y)=>[54+x/xmax*(W-100),H-56-(y+.1)/(ymax+.1)*(H-100)];
  ctx.strokeStyle='#2b4434';ctx.lineWidth=1;
  for(let x=0;x<W;x+=45){ctx.beginPath();ctx.moveTo(x,0);ctx.lineTo(x,H);ctx.stroke();}
  for(let y=0;y<H;y+=45){ctx.beginPath();ctx.moveTo(0,y);ctx.lineTo(W,y);ctx.stroke();}
  const left=point(.8,0)[0],right=point(2.3,0)[0];ctx.fillStyle='#3d5a3d66';ctx.fillRect(left,20,right-left,H-53);
  ctx.font='12px monospace';ctx.fillStyle='#9fb798';ctx.fillText('LOW-FRICTION PATCH',left+12,42);
  ctx.font='10px monospace';ctx.fillStyle='#87a18f';
  for(let x=0;x<=Math.floor(xmax);x++){const p=point(x,0);ctx.fillText(`${x} m`,p[0]-8,H-17);}
  line(ctx,rows,rows.length,p=>point(p.ref_x_m,p.ref_y_m),'#9aac99',[5,8],1.6);
  const base=baseline(),overlay=base&&$('compare').checked;
  $('compare').disabled=!base;$('compare-legend').hidden=!overlay;
  if(overlay)line(ctx,data.traces[base],i+1,p=>point(p.x_m,p.y_m),'#e6a56c',[],2);
  line(ctx,rows,i+1,p=>point(p.x_m,p.y_m),'#d8f091',[],3);
  const [x,y]=point(r.x_m,r.y_m);
  ctx.save();ctx.translate(x,y);ctx.rotate(-r.yaw_rad);ctx.fillStyle='#d8f091';ctx.beginPath();ctx.roundRect(-15,-11,30,22,4);ctx.fill();
  ctx.fillStyle='#51734b';ctx.fillRect(-10,-15,13,5);ctx.fillRect(-10,10,13,5);ctx.fillStyle='#142923';ctx.fillRect(6,-6,6,12);ctx.restore();
  $('stamp').textContent=`${r.time_s.toFixed(2).padStart(5,'0')} / ${rows.at(-1).time_s.toFixed(2)} s`;
  $('error-value').textContent=(r.cross_track_m*1000).toFixed(1);$('slip-value').textContent=r.estimated_slip.toFixed(2);
  $('traction-state').textContent=!base?'SUPERVISOR OFF':r.supervisor_active?'TRACTION DERATING ACTIVE':'TRACTION MONITORING';
  $('traction-state').classList.toggle('active',!!r.supervisor_active&&!!base);
  $('controller-description').textContent=descriptions[variant];$('compute-value').textContent=`${data.live[variant].timing.compute_p99_ms.toFixed(3)} ms`;
  $('chart-caption').textContent=`${variant} · ${names[variant]} · recorded curved run · mm`;
  drawChart(rows,i,overlay?data.traces[base]:null);
}
function drawChart(rows,i,other){
  const W=1100,H=190;chart.clearRect(0,0,W,H);chart.font='12px monospace';chart.fillStyle='#758571';chart.strokeStyle='#dfe5d9';chart.lineWidth=1;
  const min=-5,max=30,end=rows.at(-1).time_s,point=r=>[48+r.time_s/end*(W-70),H-32-(r.cross_track_m*1000-min)/(max-min)*(H-59)];
  for(let n=0;n<=3;n++){const y=H-32-(n*10-min)/(max-min)*(H-59);chart.beginPath();chart.moveTo(48,y);chart.lineTo(W-20,y);chart.stroke();chart.fillText(`${n*10}`,10,y+4);}
  for(let t=0;t<=16;t+=4)chart.fillText(`${t}s`,48+t/end*(W-70)-6,H-9);
  if(other)line(chart,other,other.length,point,'#cd975e',[],1.5);
  line(chart,rows,rows.length,point,'#147b58',[],2);
  const [x,y]=point(rows[i]);chart.strokeStyle='#6d846c';chart.setLineDash([3,5]);chart.beginPath();chart.moveTo(x,20);chart.lineTo(x,H-32);chart.stroke();chart.setLineDash([]);chart.fillStyle='#147b58';chart.beginPath();chart.arc(x,y,4,0,Math.PI*2);chart.fill();
}
function selectVariant(v){variant=v;document.querySelectorAll('[data-variant]').forEach(b=>{const active=b.dataset.variant===v;b.classList.toggle('selected',active);b.setAttribute('aria-pressed',active);});draw();}
function filterMatrix(){
  if(!data)return;
  const matches=data.matrix.filter(r=>($('surface').value==='all'||r.surface===$('surface').value)&&($('payload').value==='all'||r.payload_kg===Number($('payload').value))&&($('trajectory').value==='all'||r.trajectory===$('trajectory').value));
  $('case-count').textContent=`${matches.length} matched cases · 5 seeds each`;
  const mean=(rows,key)=>rows.reduce((s,r)=>s+r[key],0)/rows.length;
  $('comparison-body').innerHTML='ABCD'.split('').map(v=>{const rows=matches.filter(r=>r.variant===v),slip=mean(rows,'integrated_slip_m');return `<tr><td><span class="variant-badge">${v}</span>${names[v]}</td><td>${rows.filter(r=>r.completion).length}/${rows.length}</td><td>${(mean(rows,'cross_track_rmse_m')*1000).toFixed(2)} mm</td><td>${slip.toFixed(4)} m<div class="mini-bar"><span style="width:${Math.min(100,slip/.5*100)}%"></span></div></td><td>${mean(rows,'energy_j').toFixed(1)} J</td></tr>`;}).join('');
}
function evidence(){
  $('phases').innerHTML=data.phases.map((p,i)=>`<article class="phase-card"><header><span class="number">PHASE ${String(p.phase).padStart(2,'0')}</span><span class="${p.status}">${p.status.toUpperCase()}</span></header><h3>${phaseTitles[i]}</h3><p>${p.result}</p><a href="https://github.com/Snow-Warrior07/traction-aware-amr/blob/main/${p.evidence.split(';')[0].trim()}" target="_blank" rel="noopener">Inspect evidence ↗</a></article>`).join('');
  $('timing-body').innerHTML='ABCD'.split('').map(v=>{const t=data.live[v].timing;return `<tr><td>${v} · ${names[v]}</td><td>${t.compute_p99_ms.toFixed(3)} ms</td><td>${t.compute_max_ms.toFixed(3)} ms</td><td>${t.compute_deadline_misses}</td></tr>`;}).join('');
  const faultNames={overcurrent:'Overcurrent',command_timeout:'Command timeout',encoder_dropout:'Encoder dropout',localization_stale:'Stale localization',imu_bias:'IMU bias'};
  $('fault-body').innerHTML=data.faults.map(f=>`<tr><td>${faultNames[f.fault]}</td><td>${((f.fault_disable_time_s-5)*1000).toFixed(0)} ms</td><td>${f.fault_stopping_distance_m.toFixed(3)} m</td></tr>`).join('');
  const g=data.gazebo,improvement=g[1].wheel_body_divergence_m_s-g[0].wheel_body_divergence_m_s;
  $('ros-metrics').innerHTML=[[data.ros.messages.odom,'odometry messages, incl. replay'],[data.ros.replayed_odom_messages,'replayed odometry messages'],['Passed','controller-selection service'],[improvement.toFixed(2)+' m/s','extra wheel/body divergence on low friction']].map(([a,b])=>`<div><strong>${a}</strong><small>${b}</small></div>`).join('');
}
document.querySelectorAll('[data-variant]').forEach(b=>b.addEventListener('click',()=>selectVariant(b.dataset.variant)));
$('play').addEventListener('click',()=>{if(position>=$('time').max)position=0;setPlaying(!playing);draw();});
$('reset').addEventListener('click',()=>{position=0;setPlaying(false);draw();});
$('time').addEventListener('input',()=>{position=Number($('time').value);draw();});
$('compare').addEventListener('change',draw);
['surface','payload','trajectory'].forEach(id=>$(id).addEventListener('change',filterMatrix));
document.querySelectorAll('[data-view]').forEach(b=>b.addEventListener('click',()=>{
  const v=b.dataset.view,schematic=v==='schematic',src=schematic?'assets/schematic.svg':`assets/carrier-${v}.png`;
  document.querySelectorAll('[data-view]').forEach(btn=>{const active=btn===b;btn.classList.toggle('active',active);btn.setAttribute('aria-pressed',active);});
  $('board-image').src=src;$('board-link').href=src;$('board-image').alt=schematic?'Editable carrier schematic exported from KiCad':`Actual KiCad ${v} render of the routed Pico carrier`;$('board-caption').textContent=schematic?'ACTUAL SCHEMATIC EXPORT':'ACTUAL KiCad RENDER';
}));
function animate(time){
  if(playing&&data){
    if(previousFrame)position+=(Math.min(time-previousFrame,120)/1000)*Number($('speed').value)/(data.traces[variant][1].time_s-data.traces[variant][0].time_s);
    previousFrame=time;if(position>=data.traces[variant].length-1){position=data.traces[variant].length-1;setPlaying(false);}draw();
  }requestAnimationFrame(animate);
}
document.addEventListener('visibilitychange',()=>{previousFrame=0;});
fetch('data.json').then(r=>{if(!r.ok)throw new Error('Data HTTP '+r.status);return r.json();}).then(d=>{
  data=d;['payload_kg','trajectory'].forEach((key,i)=>{const select=$(i?'trajectory':'payload');[...new Set(d.matrix.map(r=>r[key]))].sort((a,b)=>typeof a==='number'?a-b:a.localeCompare(b)).forEach(v=>select.add(new Option(i?v.charAt(0).toUpperCase()+v.slice(1):`${v} kg`,v)));});
  evidence();filterMatrix();draw();$('play').disabled=false;requestAnimationFrame(animate);
}).catch(error=>{$('load-error').hidden=false;$('traction-state').textContent='DATA UNAVAILABLE';console.error(error);});
