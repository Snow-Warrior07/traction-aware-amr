import argparse
import csv
import itertools
import json
from pathlib import Path
import platform
import time
from datetime import datetime,timezone
from concurrent.futures import ProcessPoolExecutor
import numpy as np
from .simulation import Simulation,TRACE_COLUMNS

ROOT=Path(__file__).resolve().parents[1]
def write(path,data):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(data,indent=2),encoding="utf-8")
def one(args):
    variant,surface,payload,trajectory,seed=args
    sim=Simulation(variant,surface,payload,trajectory,seed)
    result=sim.run();result["seed"]=seed
    return result
def live(variant="D",seconds=16,fault=None):
    sim=Simulation(variant,"patch",0,"curved",0,duration=seconds,fault=fault)
    started_utc=datetime.now(timezone.utc).isoformat()
    start=time.perf_counter();compute=[];lateness=[];period=.02;next_tick=start
    while sim.tick*sim.dt < seconds-1e-8:
        now=time.perf_counter()
        if now<next_tick:time.sleep(next_tick-now)
        begin=time.perf_counter();lateness.append(max(0.,begin-next_tick))
        sim.step(20);compute.append(time.perf_counter()-begin);next_tick+=period
        if sim.tick%1000==0:print(f"LIVE {variant} t={sim.t:.1f}s x={sim.state[0]:.3f} slip={sim.slip_est:.3f} enabled={sim.board.enabled}",flush=True)
    wall=time.perf_counter()-start
    result=sim.metrics();result["timing"]={"mode":"wall-clock-paced soft real-time; not hard real-time",
        "wall_seconds":wall,"period_ms":20,"compute_p99_ms":float(np.percentile(compute,99)*1000),
        "compute_max_ms":max(compute)*1000,"compute_deadline_misses":sum(t>period for t in compute),
        "wake_lateness_p99_ms":float(np.percentile(lateness,99)*1000),"wake_lateness_max_ms":max(lateness)*1000,
        "start_utc":started_utc,"end_utc":datetime.now(timezone.utc).isoformat(),"host":platform.platform()}
    write(ROOT/f"results/live_{variant}{'_'+fault if fault else ''}.json",result)
    path=ROOT/f"results/trace_{variant}{'_'+fault if fault else ''}.csv"
    with path.open("w",newline="") as f:
        writer=csv.writer(f);writer.writerow(TRACE_COLUMNS);writer.writerows(sim.rows)
    print(json.dumps(result,indent=2),flush=True)
    return result
def main():
    p=argparse.ArgumentParser();p.add_argument("mode",choices=["smoke","matrix","live","faults"])
    p.add_argument("--variant",default="D");p.add_argument("--seconds",type=float,default=16)
    p.add_argument("--workers",type=int,default=4);p.add_argument("--fault",default=None)
    a=p.parse_args()
    if a.mode=="live":
        result=live(a.variant,a.seconds,a.fault)
        assert result['finite'] and result['timing']['compute_deadline_misses']==0
        assert abs(result['timing']['wall_seconds']-a.seconds)<.5
        if a.fault:assert not result['drive_enabled']
        else:assert result['completion']
        return
    if a.mode=="faults":
        results=[Simulation("D",fault=f).run() for f in ["overcurrent","command_timeout","encoder_dropout","localization_stale","imu_bias"]]
        write(ROOT/"results/faults.json",results);print(json.dumps(results,indent=2))
        assert all(r['finite'] and not r['drive_enabled'] and r['fault_disable_time_s']<=5.3 for r in results)
        return
    cases=list(itertools.product("ABCD",["dry","patch","asymmetric"],[0,5,10],["straight","curved","stop"],range(5)))
    if a.mode=="smoke":cases=list(itertools.product("ABCD",["dry","patch"],[0],["curved"],[0]))
    started=time.perf_counter()
    with ProcessPoolExecutor(max_workers=a.workers) as pool:
        results=[]
        for n,result in enumerate(pool.map(one,cases)):
            results.append(result)
            if n%20==0:print(f"{n+1}/{len(cases)} simulations complete",flush=True)
    write(ROOT/f"results/{a.mode}.json",{"runs":results,"elapsed_seconds":time.perf_counter()-started,"count":len(results)})
    print(json.dumps({"count":len(results),"finite":all(r["finite"] for r in results),
        "completed":sum(r["completion"] for r in results),"elapsed_seconds":time.perf_counter()-started},indent=2))
    assert len(results)==len(cases) and all(r['finite'] and r['completion'] for r in results)

if __name__=="__main__":main()

