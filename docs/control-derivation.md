# Control model and limits

The plant has states x, y, yaw, body velocity, yaw rate, left/right wheel speed, and left/right motor current. Contact force is F_i = mu_i N_i tanh(500 (r omega_i - v_i)/(mu_i N_i)). Wheel and body velocities remain independent. Normal load assumes 85% of weight is carried by driven wheels. The core omits lateral tire slip, suspension, tipping, temperature dependence and detailed battery dynamics.

At 2.2–4.6 seconds all route variants include the same 0.05–0.6 m/s sinusoidal acceleration/braking demand. This produces a traction challenge while crossing the patch. Constant-speed traversal alone does not verify slip control. Contact stiffness was calibrated using open-loop/no-slip behavior before freezing the final comparison.

Motor dynamics: L di/dt = Vbus duty - R i - ke omega; J d omega/dt = kt i - r F - b_w omega. Body motion follows m dv/dt = F_L+F_R-drag and Iz d yaw_rate/dt = (F_R-F_L) axle/2 - yaw_drag. Explicit 1 ms integration is checked against 0.5 ms. Motor-drive disable allows electrical current decay, rather than teleporting body speed to zero.

Body-frame reference errors ex, ey and epsi satisfy the nominal no-slip unicycle error equations. The straight moving-reference linearization has A[1,2]=vref and B[0,0]=B[2,1]=-1. Continuous-time LQR uses Q=diag(3.24,6.25,2.25), R=I. Gains are calculated once at vref=0.45 m/s. Controllability and closed-loop eigenvalues are checked. Stationary stopping uses a separate bounded heading-alignment mode.

Nonlinear law: v = vr cos(epsi) + kx ex; yaw_rate = wr + ky vr ey + kpsi sin(epsi). Gains are kx=1.8, ky=5, kpsi=2. For V=0.5(ex^2+ey^2)+(1-cos(epsi))/ky, the unsaturated continuous-time nominal dynamics give Vdot=-kx ex^2-(kpsi/ky) sin(epsi)^2. This argument is local around the intended heading and depends on a moving reference for lateral convergence. It does not establish global convergence in the presence of slip, sensor delay, saturation or faults. Those effects are evaluated numerically.

Both trajectory controllers share the same wheel PI and board model. Anti-windup prevents integral accumulation when torque saturation is driven further into saturation. Driver duty includes resistance/back-EMF feedforward, then PWM quantization and a 10 ms command delay.

Localization is an independent noisy delayed pose sensor. Ground speed is estimated from filtered pose differences; yaw rate comes from the IMU. Slip compares encoder peripheral speed to local estimated ground speed, with a denominator regularized to 0.12 m/s. The supervisor has persistence and hysteresis, reduces acceleration and torque, and gradually resumes. Simulator truth is used only in sensor generation and evaluator metrics, never supplied directly to the controller.

The four-variant experiment uses LQR or nonlinear control, each with supervisor off/on. Energy integrates positive modeled bus power; regenerated power is not credited. Timing uses simulation time for physics and monotonic host time for live pacing.

