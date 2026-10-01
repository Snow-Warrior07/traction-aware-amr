from dataclasses import dataclass
import math
import numpy as np
from scipy.linalg import solve_continuous_are
from .native import core

def wrap(angle):
    return (angle+math.pi) % (2*math.pi)-math.pi

@dataclass(frozen=True)
class Observation:
    """Only sensor-derived estimates; the control boundary has no truth input."""
    x: float
    y: float
    yaw: float
    v: float
    yaw_rate: float
    wl: float
    wr: float
    slip: float
    confidence: bool

def lqr_design(v=.45):
    A=np.array([[0.,0.,0.],[0.,0.,v],[0.,0.,0.]])
    B=np.array([[-1.,0.],[0.,0.],[0.,-1.]])
    Q=np.diag([3.24,6.25,2.25]); R=np.eye(2)
    P=solve_continuous_are(A,B,Q,R)
    K=np.linalg.solve(R,B.T@P)
    return A,B,K,np.linalg.eigvals(A-B@K)

class Controller:
    def __init__(self,kind="lqr",supervisor=False):
        self.kind=kind; self.supervisor=supervisor
        _,_,K,_=lqr_design()
        self.gains=np.array([-K[0,0],-K[1,1],-K[1,2]]) if kind=="lqr" else np.array([1.8,5.,2.])
        self.output=np.zeros(2); self.active=False; self.persistence=0.; self.scale=1.
        self.last_v=0.; self.last_w=0.

    def update(self,obs:Observation,reference,dt=.02):
        x,y,yaw,vr,wr=reference
        dx=x-obs.x;dy=y-obs.y
        ex=math.cos(obs.yaw)*dx+math.sin(obs.yaw)*dy
        ey=-math.sin(obs.yaw)*dx+math.cos(obs.yaw)*dy
        ep=wrap(yaw-obs.yaw)
        if self.supervisor:
            credible=obs.confidence and max(abs(obs.wl),abs(obs.wr))*.075>.2
            self.persistence=self.persistence+dt if credible and obs.slip>.22 else max(0.,self.persistence-dt)
            if self.persistence>=.06:self.active=True
            if obs.slip<.12 and self.persistence==0:self.active=False
        limit=.32 if self.active else 1.44
        if not obs.confidence:
            self.output[:]=0.;self.last_v=0.;self.last_w=0.
            return 0.,0.,0.
        if abs(vr)<1e-6:
            # Separate stationary alignment; no zero-speed LQR controllability claim.
            v=0.;w=float(np.clip(2.*ep,-.8,.8)) if math.hypot(dx,dy)<.08 else 0.
        else:
            core.trajectory_control(self.kind=="nonlinear",ex,ey,ep,vr,wr,self.gains,self.output)
            v=float(np.clip(self.output[0],0.,.6));w=float(np.clip(self.output[1],-1.2,1.2))
        accel=.25 if self.active else 1.8
        v=float(np.clip(v,self.last_v-accel*dt,self.last_v+accel*dt))
        w=float(np.clip(w,self.last_w-3*dt,self.last_w+3*dt))
        self.last_v=v;self.last_w=w
        return (v-.19*w)/.075,(v+.19*w)/.075,limit

