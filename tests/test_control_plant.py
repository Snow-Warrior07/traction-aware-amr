import ctypes as c
import math
import numpy as np
from amr.native import core
from amr.control import lqr_design,Controller,Observation
from amr.board import VirtualBoard
from amr.simulation import Simulation

def test_lqr_controllability_and_stability():
    A,B,K,eigs=lqr_design()
    assert np.linalg.matrix_rank(np.hstack([B,A@B,A@A@B]))==3
    assert np.max(eigs.real)<0

def test_zero_input_equilibrium():
    state=np.zeros(9)
    for _ in range(1000):core.plant_step(state,0,0,.8,.8,0,.001,1)
    assert np.max(np.abs(state))<1e-10

def test_low_friction_creates_wheel_body_divergence():
    def openloop(mu):
        s=np.zeros(9)
        for _ in range(600):core.plant_step(s,.6,.6,mu,mu,0,.001,1)
        return s
    dry= openloop(.8);wet=openloop(.1)
    assert .075*wet[5]-wet[3]>.3
    assert .075*dry[5]-dry[3]<.2
    assert dry[3]>wet[3]

def test_payload_changes_acceleration():
    a=np.zeros(9);b=np.zeros(9)
    for _ in range(200):
        core.plant_step(a,.2,.2,.8,.8,0,.001,1)
        core.plant_step(b,.2,.2,.8,.8,10,.001,1)
    assert a[3]>b[3]

def test_time_step_convergence():
    def run(dt):
        s=np.zeros(9)
        for _ in range(round(.5/dt)):core.plant_step(s,.2,.2,.8,.8,0,dt,1)
        return s
    assert np.max(np.abs(run(.001)-run(.0005)))<.025

def test_board_trip_is_independent_and_latched():
    board=VirtualBoard();board.set_command(.5,.5,0)
    board.tick(.001,0,0,[18,0])
    assert not board.enabled and board.fault_time==.001
    assert board.tick(.002,0,0,[0,0])[:2]==(0,0)

def test_command_timeout_disables_drive():
    b=VirtualBoard();b.set_command(.5,.5,0)
    b.tick(.101,0,0,[0,0])
    assert not b.enabled and b.reason=="command_timeout"

def test_native_antiwindup_recovers():
    integral=c.c_double()
    for _ in range(1000):core.wheel_pi(100,0,.005,1,c.byref(integral))
    assert abs(integral.value)<.1
    assert core.wheel_pi(0,0,.005,1,c.byref(integral))==0

def test_control_boundary_has_no_ground_truth():
    assert "truth" not in " ".join(Observation.__dataclass_fields__)
    obs=Observation(0,0,0,0,0,0,0,0,True)
    for kind in ["lqr","nonlinear"]:
        left,right,limit=Controller(kind).update(obs,[0,0,0,.45,0])
        assert np.isfinite([left,right,limit]).all()

def test_nominal_tracking():
    for variant in ["A","C"]:
        m=Simulation(variant,trajectory="curved",duration=10).run()
        assert m["finite"] and m["cross_track_rmse_m"]<.05

def test_sensor_fault_stops():
    for fault in ["encoder_dropout","localization_stale"]:
        sim=Simulation("D",fault=fault,duration=6);m=sim.run()
        assert not m["drive_enabled"] and m["fault_disable_time_s"]<5.3

def test_nominal_wheel_speed_error():
    sim=Simulation("A");sim.run();a=np.array(sim.rows)
    steady=a[(a[:,0]>10)&(a[:,0]<12)]
    assert abs(np.mean(steady[:,6])-6.)/6.<.05
    assert abs(np.mean(steady[:,7])-6.)/6.<.05

def test_route_actually_exercises_low_traction():
    dry=Simulation("A","dry").run();wet=Simulation("A","patch").run()
    assert wet["integrated_slip_m"]>2*dry["integrated_slip_m"]

