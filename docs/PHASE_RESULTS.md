# Measured results by phase

All values below come from executed software tests. Missing evidence remains pending.

| Phase | Status | Result | Evidence |
|---|---|---|---|
| 1 | verified | Requirements, rates, sensor/control boundaries and scenario matrix fixed. | docs/requirements.md; config/robot.yaml; experiments/scenarios.yaml |
| 2 | partial | Mathematical plant invariants, friction, payload and timestep checks passed; Gazebo execution pending. | tests/test_control_plant.py; results/gazebo_smoke.json |
| 3 | pending | ROS DDS, service, TF and bag replay await Linux execution. | results/ros_smoke.json |
| 4 | verified | LQR controllable/stable at design point; worst dry RMSE 0.0088 m. | tests/test_control_plant.py; results/matrix.json |
| 5 | verified | All nonlinear runs finite and complete. Nonlinear supervision changes low-traction integrated slip by 18.5% reduction; 20% hypothesis not met. | results/matrix.json; docs/control-derivation.md |
| 6 | partial | Virtual board trip/timeout/quantization tests passed; KiCad/SPICE verification pending or failed; inspect CI. | results/drc.json; results/erc.json; results/spice.json; hardware/ |
| 7 | verified | 540 matched runs, 540 deliveries, four live runs, five fault cases; soft real-time timing measured. | results/matrix.json; results/live_*.json; results/faults.json |
| 8 | partial | Dedicated GitHub repository published; final CI/release/showcase checks remain until recorded. | https://github.com/Snow-Warrior07/traction-aware-amr |

## Matched comparison

| Variant | Completed | Mean RMSE (m) | Mean integrated slip (m) | Mean energy (J) |
|---|---|---|---|---|
| A | 135/135 | 0.00811 | 0.21029 | 434.15 |
| B | 135/135 | 0.00806 | 0.17676 | 391.50 |
| C | 135/135 | 0.00917 | 0.21050 | 433.12 |
| D | 135/135 | 0.00913 | 0.17741 | 390.55 |

## Live soft real-time tests

| Variant | Wall duration (s) | p99 compute (ms) | Max compute (ms) | Compute deadline misses |
|---|---|---|---|---|
| A | 15.982 | 1.923 | 2.782 | 0 |
| B | 15.982 | 2.132 | 13.116 | 0 |
| C | 15.981 | 1.967 | 2.476 | 0 |
| D | 15.982 | 2.133 | 2.605 | 0 |

## Fault results

Drive disable and body stopping are distinct. Fault injection is at 5 s; timeout/dropout responses include their configured qualification delays.

| Fault | Drive disabled at (s) | Subsequent simulated coasting distance (m) |
|---|---|---|
| overcurrent | 5.000 | 1.104 |
| command_timeout | 5.096 | 1.430 |
| encoder_dropout | 5.060 | 1.296 |
| localization_stale | 5.140 | 1.442 |
| imu_bias | 5.000 | 1.104 |

The model has no parking/emergency brake. Coasting distances are not industrial safe-stop claims. Live runs use general-purpose Windows/Linux scheduling, not a hard real-time kernel. The matrix includes modeled bus loss, quantization and sensor delays, but does not establish physical robot or PCB performance.
