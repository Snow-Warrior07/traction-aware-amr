import ctypes as c
from collections import deque
import math
import numpy as np
from .native import core
from .control import Controller,Observation,wrap
from .board import VirtualBoard

class Simulation:
    def __init__(self,variant="A",surface="dry",payload=0,trajectory="straight",seed=0,duration=16,dt=.001,fault=None,external=False):
        self.variant=variant;self.surface=surface;self.payload=payload;self.trajectory=trajectory
        self.duration=duration;self.dt=dt;self.fault=fault;self.rng=np.random.default_rng(seed)
        self.controller=Controller("lqr" if variant in "AB" else "nonlinear",variant in "BD")
        self.board=VirtualBoard(dt);self.state=np.zeros(9);self.state[1]=.025;self.state[2]=.03
        self.tick=0;self.t=0.;self.ref=np.zeros(5);self.est=np.array([0.,.025,.03])
        self.pose_previous=None;self.v_est=0.;self.slip_est=0.;self.gyro=0.
        self.wheel_measured=np.zeros(2);self.angles=np.zeros(2);self.last_angles=np.zeros(2)
        self.left_i=c.c_double();self.right_i=c.c_double();self.wtargets=(0.,0.,1.44)
        self.pose_queue=deque();self.last_pose_time=0.;self.last_encoder_time=0.
        self.energy=0.;self.rows=[];self.stop_origin=None;self.stop_t=None
        self.fault_injected_at=5. if fault else None
        self.external=external;self.last_external_command=0.;self.last_observation=None
        self.previous_sensor_v=0.
    def friction(self):
        if self.surface=="dry" or not .8<self.state[0]<2.3:return .8,.8
        return (.10,.10) if self.surface=="patch" else (.10,.8)
    def reference_step(self):
        t=self.t; cruise=.45
        # Predeclared acceleration/braking challenge, identical on all surfaces.
        # A constant-speed crossing alone would not exercise available traction.
        if 2.2<=t<4.6:cruise=.325+.275*math.sin(2*math.pi*(t-2.2)/.8)
        ramp=min(1.,max(0.,t/.6))
        end=self.duration-3
        decel=min(1.,max(0.,(end+1-t)))
        if self.trajectory=="stop":end=8.;decel=min(1.,max(0.,(end+1-t)))
        v=cruise*ramp*decel
        yaw=.35*math.sin(.5*t) if self.trajectory=="curved" else 0.
        wr=.175*math.cos(.5*t) if self.trajectory=="curved" else 0.
        if v==0: yaw=self.ref[2];wr=0.
        self.ref[0]+=self.dt*v*math.cos(yaw);self.ref[1]+=self.dt*v*math.sin(yaw)
        self.ref[2:]=yaw,v,wr
        if v==0 and t>1 and self.stop_origin is None:
            self.stop_origin=self.state[:2].copy();self.stop_t=t
    def sensors(self):
        t=self.t;s=self.state
        bias=.35 if self.fault=="imu_bias" and t>=5 else 0.
        self.gyro=s[4]+self.rng.normal(0,.003)+bias
        accel=(s[3]-self.previous_sensor_v)/.02+self.rng.normal(0,.02)
        self.previous_sensor_v=s[3];self.v_est+=accel*.02
        sample=s[:3]+self.rng.normal(0,[.001,.001,.001])
        if not(self.fault=="localization_stale" and t>=5):self.pose_queue.append((t+.04,t,sample))
        delivered=None
        while self.pose_queue and self.pose_queue[0][0]<=t+1e-9:
            _,stamp,delivered=self.pose_queue.popleft();self.last_pose_time=stamp
        if delivered is not None:
            if self.pose_previous is not None:
                delta=delivered[:2]-self.pose_previous[:2]
                velocity=(delta[0]*math.cos(delivered[2])+delta[1]*math.sin(delivered[2]))/.02
                self.v_est += .08*(velocity+.05*accel-self.v_est)
            self.est[:2]=delivered[:2]+.04*self.v_est*np.array([math.cos(delivered[2]),math.sin(delivered[2])])
            self.est[2]=wrap(delivered[2]+.04*self.gyro)
            self.pose_previous=delivered
        else:self.est[2]=wrap(self.est[2]+.02*self.gyro)
        if not(self.fault=="encoder_dropout" and t>=5):
            quant=np.round(self.angles/(2*math.pi)*4096)*(2*math.pi)/4096
            self.wheel_measured[:]=(quant-self.last_angles)/.02;self.last_angles[:]=quant
            self.last_encoder_time=t
        local=np.array([self.v_est-.19*self.gyro,self.v_est+.19*self.gyro])
        peripheral=.075*self.wheel_measured
        slip=float(np.max(np.abs(peripheral-local)/np.maximum(.12,np.maximum(np.abs(local),np.abs(peripheral)))))
        self.slip_est += .2*(slip-self.slip_est)
        confidence=t-self.last_pose_time<.15 and t-self.last_encoder_time<.06
        if self.fault=="imu_bias" and t>=5 and delivered is not None:
            if abs(wrap(delivered[2]-self.pose_previous_yaw)/.02-self.gyro)>.25:confidence=False
        self.pose_previous_yaw=delivered[2] if delivered is not None else self.est[2]
        return Observation(*self.est,self.v_est,self.gyro,*self.wheel_measured,self.slip_est,confidence)
    def step(self,n=20):
        for _ in range(n):
            self.t=self.tick*self.dt; self.reference_step()
            if self.tick % round(.02/self.dt)==0:
                obs=self.sensors();self.last_observation=obs
                if not self.external:self.wtargets=self.controller.update(obs,self.ref)
                if not obs.confidence:self.board.tick(self.t,*self.state[5:7],self.state[7:9],stop=True)
            if self.tick % round(.005/self.dt)==0:
                tl=core.wheel_pi(self.wtargets[0],self.wheel_measured[0],.005,self.wtargets[2],c.byref(self.left_i))
                tr=core.wheel_pi(self.wtargets[1],self.wheel_measured[1],.005,self.wtargets[2],c.byref(self.right_i))
                fresh=not self.external or self.t-self.last_external_command<.1
                if fresh and not(self.fault=="command_timeout" and self.t>=5):self.board.set_command(tl,tr,self.t)
            forced=18. if self.fault=="overcurrent" and self.t>=5 else None
            dl,dr,current=self.board.tick(self.t,*self.state[5:7],self.state[7:9],forced_current=forced)
            mu_l,mu_r=self.friction()
            core.plant_step(self.state,dl,dr,mu_l,mu_r,self.payload,self.dt,int(self.board.enabled))
            self.angles+=self.dt*self.state[5:7]
            self.energy+=max(0.,24*(dl*self.state[7]+dr*self.state[8]))*self.dt
            if self.tick % round(.02/self.dt)==0:
                s=self.state;dx=s[0]-self.ref[0];dy=s[1]-self.ref[1]
                cross=-math.sin(self.ref[2])*dx+math.cos(self.ref[2])*dy
                slip=max(abs(.075*s[5]-(s[3]-.19*s[4])),abs(.075*s[6]-(s[3]+.19*s[4])))
                self.rows.append([self.t,*s[:7],*self.ref[:3],cross,self.slip_est,slip,
                                  int(self.controller.active),int(self.board.enabled),self.energy,current])
            self.tick+=1
        return self.state
    def run(self):
        total=round(self.duration/self.dt)
        while self.tick<total:self.step(min(20,total-self.tick))
        return self.metrics()
    def metrics(self):
        a=np.array(self.rows);endpoint=float(np.linalg.norm(self.state[:2]-self.ref[:2]))
        return {"variant":self.variant,"surface":self.surface,"payload_kg":self.payload,"trajectory":self.trajectory,
            "cross_track_rmse_m":float(np.sqrt(np.mean(a[:,11]**2))),"cross_track_peak_m":float(np.max(np.abs(a[:,11]))),
            "heading_rmse_rad":float(np.sqrt(np.mean([wrap(x-y)**2 for x,y in zip(a[:,3],a[:,10])]))),
            "integrated_slip_m":float(np.sum(a[:,13])*.02),"supervisor_active_fraction":float(np.mean(a[:,14])),
            "energy_j":self.energy,"endpoint_error_m":endpoint,"completion":bool(endpoint<.15 and abs(self.state[3])<.06),
            "stop_distance_m":None if self.stop_origin is None else float(np.linalg.norm(self.state[:2]-self.stop_origin)),
            "finite":bool(np.isfinite(a).all()),"drive_enabled":self.board.enabled,"fault":self.fault,
            "fault_reason":self.board.reason,"fault_disable_time_s":self.board.fault_time,
            "duration_s":self.tick*self.dt}

TRACE_COLUMNS=["time_s","x_m","y_m","yaw_rad","v_m_s","yaw_rate_rad_s","wl_rad_s","wr_rad_s",
               "ref_x_m","ref_y_m","ref_yaw_rad","cross_track_m","estimated_slip","true_slip_speed_m_s",
               "supervisor_active","drive_enabled","energy_j","current_a"]

