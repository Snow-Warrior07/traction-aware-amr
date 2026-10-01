"""Generate an editable Pico carrier schematic and routed two-layer PCB.

Run with KiCad's system Python (pcbnew). Custom symbols retain physical pin numbers.
External motor drivers supply centered current-sense outputs and active-low fault signals.
"""
import csv
import heapq
import json
import math
import os
import re
import uuid
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"hardware"/"kicad"
OUT.mkdir(parents=True,exist_ok=True)
def uid():return str(uuid.uuid4())
def quote(value):return json.dumps(str(value))
def component(ref,value,footprint,xy,pins):return dict(ref=ref,value=value,fp=footprint,xy=xy,pins=pins)
pico_names={1:"UART_TX",2:"UART_RX",3:"GND",4:"ENC_L_A",5:"ENC_L_B",6:"SDA",7:"SCL",8:"GND",
  9:"ENC_R_A",10:"ENC_R_B",11:"PWM_L",12:"DIR_L",13:"GND",14:"PWM_R",15:"DIR_R",16:"MCU_ENABLE",
  18:"GND",23:"GND",28:"GND",31:"ADC_CURRENT_L",32:"ADC_CURRENT_R",33:"GND",34:"ADC_BUS",
  35:"ADC_VREF",36:"3V3",38:"GND",39:"5V",42:"GND"}
P=[component("U1","Raspberry Pi Pico RP2040","Module:RaspberryPi_Pico_Common_THT",(50,48),{str(i):pico_names.get(i) for i in range(1,41)}),
 component("U2","74HC08 AND gate","Package_DIP:DIP-14_W7.62mm",(10,30),
 {"1":"FAULT_L_N","2":"FAULT_R_N","3":"FAULT_OK","4":"MCU_ENABLE","5":"ARMED","6":"DRIVE_ENABLE",
  "7":"GND","8":None,"9":"GND","10":"GND","11":None,"12":"GND","13":"GND","14":"3V3"}),
 component("U3","74HC74 fault latch","Package_DIP:DIP-14_W7.62mm",(80,30),
 {"1":"FAULT_OK","2":"3V3","3":"RESET_CLOCK","4":"3V3","5":"ARMED","6":None,"7":"GND",
  "8":None,"9":None,"10":"3V3","11":"GND","12":"GND","13":"GND","14":"3V3"})]
connectors=[("J1","5V power / 24V sense",(8,8),["5V","GND","BUS_24V"]),
 ("J2","LEFT DRIVER",(8,65),["PWM_L","DIR_L","DRIVE_ENABLE","GND","ISENSE_L","FAULT_L_N"]),
 ("J3","RIGHT DRIVER",(88,65),["PWM_R","DIR_R","DRIVE_ENABLE","GND","ISENSE_R","FAULT_R_N"]),
 ("J4","LEFT ENCODER",(25,8),["3V3","GND","ENC_L_A","ENC_L_B"]),
 ("J5","RIGHT ENCODER",(75,8),["3V3","GND","ENC_R_A","ENC_R_B"]),
 ("J6","3V3 IMU",(25,86),["3V3","GND","SDA","SCL"]),
 ("J7","UART DEBUG",(75,86),["3V3","GND","UART_TX","UART_RX"])]
for ref,value,xy,nets in connectors:
    P.append(component(ref,value,f"Connector_PinHeader_2.54mm:PinHeader_1x{len(nets):02d}_P2.54mm_Vertical",xy,
                       {str(i+1):net for i,net in enumerate(nets)}))
passives=[("R1","1k",(25,68),"ISENSE_L","ADC_CURRENT_L"),("R2","1k",(75,68),"ISENSE_R","ADC_CURRENT_R"),
 ("R3","100k",(25,22),"BUS_24V","ADC_BUS"),("R4","10k",(33,22),"ADC_BUS","GND"),
 ("R5","2.2k",(30,84),"3V3","SDA"),("R6","2.2k",(30,91),"3V3","SCL"),
 ("R7","10k",(88,20),"RESET_CLOCK","GND"),("R8","10k",(70,44),"MCU_ENABLE","GND"),
 ("R9","10k",(12,58),"3V3","FAULT_L_N"),("R10","10k",(80,58),"3V3","FAULT_R_N"),
 ("C1","1u",(33,68),"ADC_CURRENT_L","GND"),("C2","1u",(67,68),"ADC_CURRENT_R","GND"),
 ("C3","100n",(35,29),"ADC_BUS","GND"),("C4","100n",(35,35),"3V3","GND"),
 ("C5","10u",(13,14),"5V","GND"),("C6","100n",(25,35),"3V3","GND"),
 ("C7","100n",(75,35),"3V3","GND"),("C8","100n",(65,35),"ADC_VREF","GND")]
for ref,value,xy,a,b in passives:
    fp="Resistor_SMD:R_0805_2012Metric" if ref[0]=="R" else "Capacitor_SMD:C_0805_2012Metric"
    P.append(component(ref,value,fp,xy,{"1":a,"2":b}))
P.append(component("SW1","Manual drive reset","Button_Switch_THT:SW_PUSH_6mm_H4.3mm",(88,10),
                   {"1":"3V3","2":"RESET_CLOCK"}))

def electrical_type(part,pin):
    ref=part["ref"]
    if ref=="U1":
        if pin=="36":return "power_out"
        if pin in ["3","8","13","18","23","28","33","38","39","42"]:return "power_in"
        return "bidirectional"
    if ref=="J1" and pin in ["1","2"]:return "power_out"
    if ref in ["U2","U3"]:
        if pin in ["7","14"]:return "power_in"
        if pin in (["3","6","8","11"] if ref=="U2" else ["5","6","8","9"]):return "output"
        return "input"
    return "passive"

def schematic():
    rootuid=uid();libs=[];instances=[];labels=[]
    for index,part in enumerate(P):
        part['symbol_uuid']=uid();part['sheet_uuid']=rootuid
        pins=part["pins"];count=len(pins);side=(count+1)//2;height=max(5.08,side*2.54)
        symbol_name="AMR:"+part["ref"]; stem=part["ref"]
        lib=f'(symbol {quote(symbol_name)} (pin_names (offset 0.5)) (in_bom yes) (on_board yes) '
        lib+=f'(property "Reference" {quote(stem)} (at 0 {height/2+3} 0) (effects (font (size 1.27 1.27)))) '
        lib+=f'(property "Value" {quote(part["value"])} (at 0 {-height/2-3} 0) (effects (font (size 1 1)))) '
        lib+=f'(symbol "{stem}_0_1" (rectangle (start -9 {height/2+1.27}) (end 9 {-height/2-1.27}) (stroke (width 0.254) (type default)) (fill (type background)))) '
        lib+=f'(symbol "{stem}_1_1" '
        x=69.85+(index%5)*121.92;y=101.6+(index//5)*63.5
        coords=[]
        for n,(pin,net) in enumerate(pins.items()):
            left=n<side;row=n if left else n-side
            px=-12.7 if left else 12.7;py=height/2-row*2.54;angle=0 if left else 180
            name=net if net else "NC_"+pin
            lib+=f'(pin {electrical_type(part,pin)} line (at {px} {py} {angle}) (length 3.7) (name {quote(name)} (effects (font (size .75 .75)))) (number {quote(pin)} (effects (font (size .75 .75))))) '
            coords.append((pin,net,x+px,y-py,left))
        lib+='))';libs.append(lib)
        item=f'(symbol (lib_id {quote(symbol_name)}) (at {x} {y} 0) (unit 1) (in_bom yes) (on_board yes) (dnp no) (uuid {part["symbol_uuid"]}) '
        for name,value,offset,hide in [("Reference",part["ref"],-height/2-5,False),("Value",part["value"],height/2+5,False),("Footprint",part["fp"],0,True)]:
            item+=f'(property {quote(name)} {quote(value)} (at {x} {y+offset} 0) (effects (font (size 1 1)) {"(hide yes)" if hide else ""})) '
        for pin in pins:item+=f'(pin {quote(pin)} (uuid {uid()})) '
        item+=f'(instances (project "traction_carrier" (path "/{rootuid}" (reference {quote(part["ref"])}) (unit 1)))))'
        instances.append(item)
        for pin,net,px,py,left in coords:
            if net:
                labels.append(f'(label {quote(net)} (at {px} {py} 0) (effects (font (size .75 .75)) (justify {"right" if left else "left"} bottom)) (uuid {uid()}))')
            else:labels.append(f'(no_connect (at {px} {py}) (uuid {uid()}))')
    text=f'(kicad_sch (version 20231120) (generator "eeschema") (uuid {rootuid}) (paper "A1") (lib_symbols {" ".join(libs)}) '
    text+=' '.join(instances+labels)+')'
    (OUT/"traction_carrier.kicad_sch").write_text(text)
    library='(kicad_symbol_lib (version 20231120) (generator "kicad_symbol_editor") '+ ' '.join(s.replace('(symbol "AMR:', '(symbol "',1) for s in libs)+')'
    (OUT/'AMR.kicad_sym').write_text(library)
    (OUT/'sym-lib-table').write_text('(sym_lib_table (version 7) (lib (name "AMR") (type "KiCad") (uri "${KIPRJMOD}/AMR.kicad_sym") (options "") (descr "Project carrier symbols")))')
    libraries=sorted({p['fp'].split(':')[0] for p in P})
    major=10 if os.name=='nt' else 9
    (OUT/'fp-lib-table').write_text('(fp_lib_table (version 7) '+ ' '.join(f'(lib (name "{name}") (type "KiCad") (uri "${{KICAD{major}_FOOTPRINT_DIR}}/{name}.pretty") (options "") (descr "KiCad standard library"))' for name in libraries)+')')
    with (OUT/"bom.csv").open("w",newline="") as f:
        writer=csv.writer(f);writer.writerow(["Reference","Value","Footprint"])
        writer.writerows((p["ref"],p["value"],p["fp"]) for p in P)

def board():
    import pcbnew as k
    import numpy as np
    b=k.BOARD();b.SetCopperLayerCount(2)
    nets={name:k.NETINFO_ITEM(b,'/'+name,i+1) for i,name in enumerate(sorted({v for p in P for v in p["pins"].values() if v}))}
    for net in nets.values():b.Add(net)
    padlist=[];footprint_root=Path(os.environ.get('KICAD_FOOTPRINT_DIR',"/usr/share/kicad/footprints"))
    for part in P:
        lib,name=part["fp"].split(":");fp=k.FootprintLoad(str(footprint_root/(lib+".pretty")),name)
        if fp is None:raise RuntimeError("Missing footprint "+part["fp"]+"; available Pico footprints: "+str(list(footprint_root.glob("Module.pretty/*Pico*"))))
        fp.SetPath(k.KIID_PATH('/'+part['sheet_uuid']+'/'+part['symbol_uuid']))
        fp.SetFPID(k.LIB_ID(lib,name))
        fp.SetReference(part["ref"]);fp.SetValue(part["value"]);fp.SetPosition(k.VECTOR2I(k.FromMM(part["xy"][0]),k.FromMM(part["xy"][1])))
        if part["ref"]=="U1":
            # Library origins differ across editions. Center the two header rows.
            main=[pad.GetPosition() for pad in fp.Pads() if pad.GetNumber().isdigit() and 1<=int(pad.GetNumber())<=40]
            center=k.VECTOR2I((min(p.x for p in main)+max(p.x for p in main))//2,(min(p.y for p in main)+max(p.y for p in main))//2)
            fp.SetPosition(fp.GetPosition()+k.VECTOR2I(k.FromMM(part["xy"][0]),k.FromMM(part["xy"][1]))-center)
        for pad in fp.Pads():
            name=part["pins"].get(pad.GetNumber())
            if name:pad.SetNet(nets[name])
            elif pad.GetNumber() in part['pins']:
                nc=k.NETINFO_ITEM(b,f"unconnected-({part['ref']}-NC_{pad.GetNumber()}-Pad{pad.GetNumber()})",len(nets)+1)
                b.Add(nc);nets['NC_'+part['ref']+'_'+pad.GetNumber()]=nc;pad.SetNet(nc)
            padlist.append(pad)
        b.Add(fp)
    for a,z in [((2,2),(98,2)),((98,2),(98,98)),((98,98),(2,98)),((2,98),(2,2))]:
        edge=k.PCB_SHAPE();edge.SetShape(k.SHAPE_T_SEGMENT);edge.SetStart(k.VECTOR2I(k.FromMM(a[0]),k.FromMM(a[1])));edge.SetEnd(k.VECTOR2I(k.FromMM(z[0]),k.FromMM(z[1])));edge.SetLayer(k.Edge_Cuts);edge.SetWidth(k.FromMM(.05));b.Add(edge)
    grid=.25;N=401;occ=np.zeros((2,N,N),dtype=np.int32)
    track_occ=np.zeros_like(occ)
    drill_block=np.zeros((N,N),dtype=bool)
    vias={}
    occ[:,:12,:]=-1;occ[:,-12:,:]=-1;occ[:,:,:12]=-1;occ[:,:,-12:]=-1
    def coord(pos):return (round(k.ToMM(pos.x)/grid),round(k.ToMM(pos.y)/grid))
    for pad in padlist:
        pos=pad.GetPosition();x,y=coord(pos);size=pad.GetSize()
        angle=math.radians(pad.GetOrientation().AsDegrees())
        rx=(abs(math.cos(angle))*k.ToMM(size.x)+abs(math.sin(angle))*k.ToMM(size.y))/2+.4
        ry=(abs(math.sin(angle))*k.ToMM(size.x)+abs(math.cos(angle))*k.ToMM(size.y))/2+.4
        # A new via cannot overlap a pad or its drill, even on the same net.
        drill=pad.GetDrillSize()
        radius=max(k.ToMM(size.x),k.ToMM(size.y),k.ToMM(drill.x),k.ToMM(drill.y))/2+.6
        for xx in range(max(0,x-math.ceil(radius/grid)),min(N,x+math.ceil(radius/grid)+1)):
            for yy in range(max(0,y-math.ceil(radius/grid)),min(N,y+math.ceil(radius/grid)+1)):
                if math.hypot(xx*grid-k.ToMM(pos.x),yy*grid-k.ToMM(pos.y))<radius:drill_block[xx,yy]=True
        for layer in [0,1]:
            if not pad.IsOnLayer(k.F_Cu if layer==0 else k.B_Cu):continue
            for xx in range(max(0,x-math.ceil(rx/grid)),min(N,x+math.ceil(rx/grid)+1)):
                for yy in range(max(0,y-math.ceil(ry/grid)),min(N,y+math.ceil(ry/grid)+1)):
                    if abs(xx*grid-k.ToMM(pos.x))<rx and abs(yy*grid-k.ToMM(pos.y))<ry:occ[layer,xx,yy]=pad.GetNetCode() or -1
    # Respect library copper keepouts, enlarged for half the track width.
    for fp in b.GetFootprints():
        for zone in fp.Zones():
            if not zone.GetIsRuleArea() or not zone.GetDoNotAllowTracks():continue
            box=zone.GetBoundingBox()
            x0=math.floor(k.ToMM(box.GetX())/grid)-1;x1=math.ceil(k.ToMM(box.GetRight())/grid)+1
            y0=math.floor(k.ToMM(box.GetY())/grid)-1;y1=math.ceil(k.ToMM(box.GetBottom())/grid)+1
            for layer in [0,1]:
                if zone.IsOnLayer(k.F_Cu if layer==0 else k.B_Cu):
                    occ[layer,max(0,x0):min(N,x1+1),max(0,y0):min(N,y1+1)]=-1
    def segment(a,z,layer,net):
        if a==z:return
        s=k.PCB_TRACK(b);s.SetStart(k.VECTOR2I(k.FromMM(a[0]),k.FromMM(a[1])));s.SetEnd(k.VECTOR2I(k.FromMM(z[0]),k.FromMM(z[1])));s.SetLayer(k.F_Cu if layer==0 else k.B_Cu);s.SetWidth(k.FromMM(.25));s.SetNetCode(net);b.Add(s)
    def via(x,y,net):
        key=(round(x/grid),round(y/grid))
        if key in vias:return
        v=k.PCB_VIA(b);v.SetPosition(k.VECTOR2I(k.FromMM(x),k.FromMM(y)));v.SetWidth(k.FromMM(.65));v.SetDrill(k.FromMM(.3));v.SetViaType(k.VIATYPE_THROUGH);v.SetLayerPair(k.F_Cu,k.B_Cu);v.SetNetCode(net);b.Add(v)
        vias[key]=net
        xx,yy=key
        drill_block[max(0,xx-3):min(N,xx+4),max(0,yy-3):min(N,yy+4)]=True
    def route(src,dest,net):
        start=(*coord(src.GetPosition()),0);end=(*coord(dest.GetPosition()),0)
        starts=[(*coord(src.GetPosition()),l) for l in [0,1] if src.IsOnLayer(k.F_Cu if l==0 else k.B_Cu) and track_occ[l,start[0],start[1]] in [0,net]]
        ends={(*coord(dest.GetPosition()),l) for l in [0,1] if dest.IsOnLayer(k.F_Cu if l==0 else k.B_Cu)}
        queue=[(0.,0.,s) for s in starts];cost={s:0. for s in starts};previous={s:None for s in starts};visited=set();found=False
        while queue:
            _,g,node=heapq.heappop(queue)
            if node in visited:continue
            visited.add(node)
            if node in ends:end=node;found=True;break
            x,y,l=node
            options=[(x+1,y,l),(x-1,y,l),(x,y+1,l),(x,y-1,l),(x,y,1-l)]
            for xx,yy,ll in options:
                if not 0<xx<N-1 or not 0<yy<N-1:continue
                if occ[ll,xx,yy] not in [0,net]:continue
                if track_occ[ll,xx,yy] not in [0,net]:continue
                if ll!=l:
                    if drill_block[xx,yy] and vias.get((xx,yy))!=net:continue
                    if any(not 0<=xx+dx<N or not 0<=yy+dy<N or occ[layer,xx+dx,yy+dy] not in [0,net] or track_occ[layer,xx+dx,yy+dy] not in [0,net] for layer in [0,1] for dx in range(-2,3) for dy in range(-2,3)):continue
                ng=g+(4 if ll!=l else 1)
                nxt=(xx,yy,ll)
                if ng>=cost.get(nxt,1e30):continue
                cost[nxt]=ng;previous[nxt]=node
                h=abs(xx-end[0])+abs(yy-end[1])+.5*(ll!=end[2])
                heapq.heappush(queue,(ng+1.15*h,ng,nxt))
        if not found:
            k.SaveBoard(str(OUT/"routing_debug.kicad_pcb"),b)
            raise RuntimeError(f"Routing failed net {src.GetNetname()} from {src.GetNumber()} {start} to {dest.GetNumber()} {end}; endpoint occupancy {occ[start[2],start[0],start[1]]}, {occ[end[2],end[0],end[1]]}; track occupancy {track_occ[start[2],start[0],start[1]]}, {track_occ[end[2],end[0],end[1]]}")
        path=[end]
        while previous[path[-1]] is not None:path.append(previous[path[-1]])
        path.reverse()
        start=path[0]
        a=src.GetPosition();z=dest.GetPosition()
        segment((k.ToMM(a.x),k.ToMM(a.y)),(start[0]*grid,start[1]*grid),start[2],net)
        run_start=path[0];last_direction=None
        for p,q in zip(path,path[1:]):
            if p[2]!=q[2]:via(p[0]*grid,p[1]*grid,net)
            direction=(q[0]-p[0],q[1]-p[1],q[2]-p[2])
            if direction!=last_direction:
                segment((run_start[0]*grid,run_start[1]*grid),(p[0]*grid,p[1]*grid),run_start[2],net)
                run_start=p if p[2]==q[2] else q
            elif p[2]!=q[2]:run_start=q
            last_direction=direction
            for layer in ([0,1] if p[2]!=q[2] else [p[2]]):
                radius=3 if p[2]!=q[2] else 1
                for point in [p,q]:
                    for dx,dy in ((dx,dy) for dx in range(-radius,radius+1) for dy in range(-radius,radius+1)):
                        xx=point[0]+dx;yy=point[1]+dy
                        if 0<=xx<N and 0<=yy<N and track_occ[layer,xx,yy]==0:track_occ[layer,xx,yy]=net
        segment((run_start[0]*grid,run_start[1]*grid),(end[0]*grid,end[1]*grid),run_start[2],net)
        segment((end[0]*grid,end[1]*grid),(k.ToMM(z.x),k.ToMM(z.y)),end[2],net)
    groups={}
    for pad in padlist:
        if pad.GetNetCode():groups.setdefault(pad.GetNetCode(),[]).append(pad)
    lengths=[]
    for net,pads in groups.items():
        for pad in pads[1:]:
            nearest=min(pads[:pads.index(pad)],key=lambda p:(p.GetPosition()-pad.GetPosition()).EuclideanNorm())
            lengths.append((-(nearest.GetPosition()-pad.GetPosition()).EuclideanNorm(),nearest,pad,net))
    # Shortest links first; reserve local routes before long interconnects.
    for _,src,dest,net in sorted(lengths,key=lambda x:-x[0]):route(src,dest,net)
    k.SaveBoard(str(OUT/"traction_carrier.kicad_pcb"),b)
    print(json.dumps({"components":len(P),"connected_nets":sum(not n.startswith('NC_') for n in nets),"no_connect_nets":sum(n.startswith('NC_') for n in nets),"tracks":len(list(b.GetTracks()))}))

if __name__=="__main__":
    schematic();board()

