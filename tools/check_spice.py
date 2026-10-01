import json
import subprocess
from pathlib import Path
import numpy as np
root=Path(__file__).resolve().parents[1];folder=root/"hardware"/"spice"
subprocess.run(["ngspice","-b","current_filter.cir"],cwd=folder,check=True)
a=np.loadtxt(folder/"current_filter.dat",skiprows=1)
t=a[:,0];out=a[:,2]
idx=int(np.argmin(abs(out-(1.65+(1-1/np.e)))))
tau=t[idx]-.001;final=out[-1]
result={"rc_expected_tau_s":.001,"measured_tau_s":float(tau),"final_v":float(final),
        "adc_bits":12,"current_resolution_a":3.3/4095/.1,"sense_offset_v":1.65,"sense_gain_v_a":.1,
        "model_scope":"external driver sense modeled as an ideal source; real PCB RC simulated by ngspice"}
assert abs(tau-.001)<.00005
assert abs(final-2.65)<.002
(root/"results"/"spice.json").write_text(json.dumps(result,indent=2))
print(json.dumps(result,indent=2))
