# Traction-aware AMR: local demo report

| Phase | Status | Result |
|---|---|---|
| 1. Requirements and experiment matrix | Verified | Fixed sensor/control boundaries, rates, payloads and friction cases. |
| 2. Robot model and warehouse | Verified | Mathematical dynamics checks and real Gazebo dry/low-friction contact bridge passed. |
| 3. ROS 2 basics and integration | Verified | Actual DDS traffic, TF, controller-selection service, bag record/replay. |
| 4. Linear PI / LQR | Verified | Controllable and stable design point. Worst dry LQR RMSE: 8.76 mm. |
| 5. Nonlinear control / traction | Verified | All runs finite and complete. Low-traction slip reduction: 18.48%; 20% target not met. |
| 6. Virtual PCB and circuit | Verified | KiCad 10 ERC 0, DRC 0, connectivity 0; source, renders, Gerbers and RC simulation. |
| 7. Software and paced tests | Verified | 15 local tests; 540 completed routes; 4 recorded live runs; 5 fault cases. |
| 8. GitHub demo and profile | Verified | Repository, interactive Pages website, phase report and profile project link delivered. |

540/540 matched routes completed; 15 local regression tests passed. Low-traction slip reduction: LQR 18.76%, nonlinear 18.48% (20% hypothesis not met). Four recorded live tests: zero 20 ms compute-budget misses.

Local KiCad: ERC 0; unconnected items 0; DRC 0 errors / 0 warnings. Ngspice RC tau: 1.00116 ms. Actual Gazebo torque/contact checks passed in recovered saved run 36900851054.

GitHub verification tests remain manual at the user request. Website: https://snow-warrior07.github.io/traction-aware-amr/ . See output/publication.json for deployment evidence.
