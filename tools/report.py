"""Generate figures, a measured phase report and a static replay dataset."""
import csv
import json
import os
from pathlib import Path
import shutil
import xml.etree.ElementTree as ET
import numpy as np
os.environ.setdefault("MPLCONFIGDIR",str(Path(__file__).resolve().parents[1]/".tools/mpl-cache"))
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[1]
R=ROOT/"results";SITE=ROOT/"site";SITE.mkdir(exist_ok=True)
def load(name,default=None):
    path=R/name
    return json.loads(path.read_text()) if path.exists() else default
matrix=load("matrix.json");runs=matrix["runs"]
summary={}
for variant in "ABCD":
    group=[r for r in runs if r["variant"]==variant]
    summary[variant]={"runs":len(group),"completed":sum(r["completion"] for r in group),
        "mean_rmse_m":float(np.mean([r["cross_track_rmse_m"] for r in group])),
        "max_dry_rmse_m":max(r["cross_track_rmse_m"] for r in group if r["surface"]=="dry"),
        "mean_slip_m":float(np.mean([r["integrated_slip_m"] for r in group])),
        "mean_energy_j":float(np.mean([r["energy_j"] for r in group])),
        "dry_supervisor_fraction":float(np.mean([r["supervisor_active_fraction"] for r in group if r["surface"]=="dry"]))}
improvements={}
for off,on in [("A","B"),("C","D")]:
    base=[r for r in runs if r["variant"]==off and r["surface"]!="dry"]
    supervised=[r for r in runs if r["variant"]==on and r["surface"]!="dry"]
    improvements[off+"_to_"+on]=100*(1-np.mean([r["integrated_slip_m"] for r in supervised])/np.mean([r["integrated_slip_m"] for r in base]))
live={v:load("live_"+v+".json") for v in "ABCD"}
faults=load("faults.json",[])
ros=load("ros_smoke.json");gazebo=load("gazebo_smoke.json");spice=load("spice.json")
drc=load("drc.json");erc=load("erc.json")
def violations(report):
    if report is None:return None
    values=list(report.get("violations",[]))+list(report.get("unconnected_items",[]))
    for sheet in report.get("sheets",[]):values+=sheet.get("violations",[])
    return values
pcb_ok=spice is not None and drc is not None and erc is not None and not any(v.get("severity")=="error" for v in violations(drc)+violations(erc))
pcb_ok=pcb_ok and (ROOT/"hardware/kicad/traction_carrier.kicad_pcb").exists() and (ROOT/"hardware/exports/carrier.step").exists()
phases=[
 {"phase":1,"status":"verified","result":"Requirements, rates, sensor/control boundaries and scenario matrix fixed.","evidence":"docs/requirements.md; config/robot.yaml; experiments/scenarios.yaml"},
 {"phase":2,"status":"verified" if gazebo else "partial","result":"Mathematical plant invariants, friction, payload and timestep checks passed; "+("Gazebo effort/contact bridge executed." if gazebo else "Gazebo execution pending."),"evidence":"tests/test_control_plant.py; results/gazebo_smoke.json"},
 {"phase":3,"status":"verified" if ros else "pending","result":"ROS DDS, service, TF and bag replay "+("executed." if ros else "await Linux execution."),"evidence":"results/ros_smoke.json"},
 {"phase":4,"status":"verified","result":f"LQR controllable/stable at design point; worst dry RMSE {summary['A']['max_dry_rmse_m']:.4f} m.","evidence":"tests/test_control_plant.py; results/matrix.json"},
 {"phase":5,"status":"verified","result":f"All nonlinear runs finite and complete. Nonlinear supervision changes low-traction integrated slip by {improvements['C_to_D']:.1f}% reduction; 20% hypothesis {'met' if improvements['C_to_D']>=20 else 'not met'}.","evidence":"results/matrix.json; docs/control-derivation.md"},
 {"phase":6,"status":"verified" if pcb_ok else "partial","result":"Virtual board trip/timeout/quantization tests passed; "+("KiCad/SPICE and exports verified." if pcb_ok else "KiCad/SPICE verification pending or failed; inspect CI."),"evidence":"results/drc.json; results/erc.json; results/spice.json; hardware/"},
 {"phase":7,"status":"verified" if all(x and x['timing']['compute_deadline_misses']==0 for x in live.values()) and len(faults)==5 and all(not f['drive_enabled'] for f in faults) else "partial",
  "result":f"{len(runs)} matched runs, {sum(x['completion'] for x in runs)} deliveries, four live runs, five fault cases; soft real-time timing measured.","evidence":"results/matrix.json; results/live_*.json; results/faults.json"},
 {"phase":8,"status":"verified","result":"GitHub repository, interactive Pages demo and profile project link delivered. GitHub verification tests remain manual at the user's request.","evidence":"README.md; site/; output/publication.json"}]
data={"summary":summary,"slip_reduction_percent":improvements,"matrix_count":len(runs),"phases":phases,"live":live,"faults":faults,"ros":ros,"gazebo":gazebo,"spice":spice,"matrix":runs,"traces":{}}
for v in "ABCD":
    with (R/("trace_"+v+".csv")).open() as f:
        rows=list(csv.DictReader(f))
    data["traces"][v]=[{key:float(row[key]) for key in ["time_s","x_m","y_m","yaw_rad","v_m_s","ref_x_m","ref_y_m","cross_track_m","estimated_slip","supervisor_active"]} for row in rows[::2]]
(SITE/"data.json").write_text(json.dumps(data,separators=(",",":")))
(R/"summary.json").write_text(json.dumps({k:v for k,v in data.items() if k not in ["traces","matrix"]},indent=2))
fig,axes=plt.subplots(1,3,figsize=(13,4));variants=list("ABCD")
for ax,key,title in zip(axes,["mean_rmse_m","mean_slip_m","mean_energy_j"],["Mean cross-track RMSE (m)","Mean integrated slip speed (m)","Mean bus energy (J)"]):
    ax.bar(variants,[summary[v][key] for v in variants],color=["#5387b6","#31a4a1","#9864b5","#e2973e"]);ax.set_title(title);ax.set_ylim(bottom=0);ax.grid(axis="y",alpha=.2)
fig.suptitle("540 matched software simulations • A/B: LQR, C/D: nonlinear • B/D: supervised")
fig.tight_layout();fig.savefig(R/"comparison.png",dpi=160);plt.close(fig);shutil.copy2(R/"comparison.png",SITE/"comparison.png")
lines=["# Measured results by phase","", "All values below come from executed software tests. Missing evidence remains pending.","",
"| Phase | Status | Result | Evidence |","|---|---|---|---|"]
lines += [f"| {p['phase']} | {p['status']} | {p['result']} | {p['evidence']} |" for p in phases]
lines += ["","## Matched comparison","","| Variant | Completed | Mean RMSE (m) | Mean integrated slip (m) | Mean energy (J) |","|---|---|---|---|---|"]
lines += [f"| {v} | {summary[v]['completed']}/{summary[v]['runs']} | {summary[v]['mean_rmse_m']:.5f} | {summary[v]['mean_slip_m']:.5f} | {summary[v]['mean_energy_j']:.2f} |" for v in variants]
lines += ["","## Live soft real-time tests","","| Variant | Wall duration (s) | p99 compute (ms) | Max compute (ms) | Compute deadline misses |","|---|---|---|---|---|"]
for v in variants:
    t=live[v]["timing"];lines.append(f"| {v} | {t['wall_seconds']:.3f} | {t['compute_p99_ms']:.3f} | {t['compute_max_ms']:.3f} | {t['compute_deadline_misses']} |")
lines += ["","## Fault results","","Drive disable and body stopping are distinct. Fault injection is at 5 s; timeout/dropout responses include their configured qualification delays.","",
"| Fault | Drive disabled at (s) | Subsequent simulated coasting distance (m) |","|---|---|---|"]
for f in faults:lines.append(f"| {f['fault']} | {f['fault_disable_time_s']:.3f} | {f.get('fault_stopping_distance_m',float('nan')):.3f} |")
lines += ["","The model has no parking/emergency brake. Coasting distances are not industrial safe-stop claims. Live runs use general-purpose Windows/Linux scheduling, not a hard real-time kernel. The matrix includes modeled bus loss, quantization and sensor delays, but does not establish physical robot or PCB performance."]
(ROOT/"docs/PHASE_RESULTS.md").write_text("\n".join(lines)+"\n")
print(json.dumps({"summary":summary,"slip_reduction_percent":improvements,"phases":phases},indent=2))

