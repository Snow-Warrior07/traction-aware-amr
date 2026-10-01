"""Behavioral I/O model, parameterized by the PCB's sensor chain.

This models I/O timing and quantization; SPICE separately checks the analog RC.
"""
from collections import deque
import math

class VirtualBoard:
    def __init__(self,dt=.001,delay=.01):
        self.dt=dt;self.queue=deque([(0.,0.)]*max(1,round(delay/dt)))
        self.command=(0.,0.);self.last_command=0.;self.enabled=True;self.reason=""
        self.filtered_current=0.;self.fault_time=None;self.sense_gain=.1;self.tau=.001
    def set_command(self,left,right,t):
        self.command=(left,right);self.last_command=t
    def tick(self,t,wl,wr,current,forced_current=None,stop=False):
        sensed=max(abs(current[0]),abs(current[1])) if forced_current is None else forced_current
        self.filtered_current += (1-math.exp(-self.dt/self.tau))*(sensed-self.filtered_current)
        adc=round(min(3.3,self.filtered_current*self.sense_gain)/3.3*4095)
        reconstructed=adc*3.3/4095/self.sense_gain
        raw_trip=sensed>=16. # independent comparator before RC/ADC path
        if self.enabled and (raw_trip or stop or t-self.last_command>.1000001):
            self.enabled=False;self.fault_time=t
            self.reason="overcurrent" if raw_trip else "sensor_stop" if stop else "command_timeout"
        self.queue.append(self.command);tl,tr=self.queue.popleft()
        if not self.enabled:return 0.,0.,reconstructed
        def duty(torque,omega):
            voltage=(torque/.12)*1.5+.12*omega
            value=max(-1.,min(1.,voltage/24.))
            return round(value*4095)/4095
        return duty(tl,wl),duty(tr,wr),reconstructed

