"""Compile and load the same C++ control core used in SIL and ROS."""
import ctypes as c
import os
import subprocess
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
LIB = ROOT / "build" / ("core.dll" if os.name == "nt" else "libcore.so")

def build():
    source = ROOT / "firmware" / "core.cpp"
    if not LIB.exists() or LIB.stat().st_mtime < source.stat().st_mtime:
        LIB.parent.mkdir(exist_ok=True)
        target=subprocess.check_output(["g++","-dumpmachine"],text=True).strip()
        lcc=Path(r"C:\Program Files\MATLAB\R2024b\sys\lcc64\lcc64\bin")
        if os.name=="nt" and target=="mingw32" and lcc.exists():
            # Installed MinGW is 32-bit; MATLAB's bundled LCC64 compiles the identical C-compatible core.
            csource=LIB.parent/"core.c";csource.write_text(source.read_text())
            subprocess.run([str(lcc/"lcc64.exe"),"-I"+str(lcc.parent/"include64"),"-O",str(csource),"-o",str(LIB.parent/"core.obj")],check=True,cwd=LIB.parent)
            subprocess.run([str(lcc/"lcclnk64.exe"),"-L"+str(lcc.parent/"lib64"),"-dll","-o",str(LIB),str(LIB.parent/"core.obj")],check=True,cwd=LIB.parent)
        else:
            subprocess.run(["g++", "-std=c++11", "-O2", "-shared", "-static-libgcc", "-static-libstdc++",
                            *( [] if os.name == "nt" else ["-fPIC"]), str(source), "-o", str(LIB)], check=True)
    return LIB

build()
core = c.CDLL(str(LIB))
if os.name=="nt":
    # Use the initialized Windows runtime's math functions with LCC's pure numerical DLL.
    crt=c.CDLL("ucrtbase.dll")
    core.set_math.argtypes=[c.c_void_p]*3
    core.set_math(*[c.cast(getattr(crt,name),c.c_void_p) for name in ["cos","sin","tanh"]])
pointer = np.ctypeslib.ndpointer(dtype=np.float64, flags="C_CONTIGUOUS")
core.trajectory_control.argtypes = [c.c_int]+[c.c_double]*5+[pointer,pointer]
core.wheel_pi.argtypes = [c.c_double]*4+[c.POINTER(c.c_double)]
core.wheel_pi.restype = c.c_double
core.plant_step.argtypes = [pointer]+[c.c_double]*6+[c.c_int]

