# Requirements and fixed verification criteria

The system is entirely simulated. A carrier PCB connects a Raspberry Pi Pico module to external 24 V motor drivers, encoder/IMU interfaces, analog current/voltage sensing, and an independent driver-fault gate. The virtual drivers implement motor electrical dynamics and current limiting. Physical parts and board manufacture are not required.

| ID | Requirement | Evidence |
|---|---|---|
| R1 | Separate body/wheel dynamics with friction-limited forces | Open-loop dry/low-friction and payload tests; timestep convergence |
| R2 | Linear wheel PI and outer LQR | Native C++ core, controllability/eigenvalues, dry-floor RMSE <= 0.05 m |
| R3 | Nonlinear trigonometric tracking with traction supervision | Native controller, estimator, four-variant matched study |
| R4 | Real ROS 2 publishers/subscribers, parameters, services, transforms, bags | Linux CI build, live ROS smoke test, recorded/replayed bag |
| R5 | Editable PCB, schematic, 3D and circuit simulation | KiCad source, DRC/ERC, manufacturing exports, ngspice transient results |
| R6 | Circuit-derived virtual I/O impacts the loop | RC time constant, ADC/PWM quantization, delay, trip and timeout checks |
| R7 | Live wall-clock-paced tests | Actual elapsed time, 20 ms compute budget, wake lateness, saved traces |
| R8 | Robust fault behavior | Overcurrent, stale command, encoder/localization dropout, IMU bias |
| R9 | GitHub source and reproducible results | Dedicated repository, passing CI, tagged release, Pages showcase |
| R10 | Industry-alignment evidence | Hazard register, scope-level standards mapping, limitations |

The 20% slip-reduction target is a research hypothesis, not a condition for hiding or rejecting honest results. Timing tests are soft real-time on general-purpose hosts. Mechanical stopping is evaluated separately from digital drive disable. No safety certification or hard real-time guarantee is claimed.

Plant settings: 12 kg empty mass, 0/5/10 kg payload, 75 mm wheels, 380 mm axle, 24 V supply, torque constant 0.12 Nm/A, resistance 1.5 ohm, inductance 3 mH, 12 A modeled driver current limit. Maximum route speed is 0.6 m/s. Plant integration is 1 kHz, wheel control 200 Hz, pose/outer control 50 Hz. Friction settings are simulation parameters rather than measured floor classifications.

