# Standards alignment and model limits

This is a virtual engineering demonstrator. No formal compliance, safety performance level, CE marking, EMI result, physical braking capability, or hard real-time guarantee is asserted.

| Reference | Applied design intent | Evidence and limit |
|---|---|---|
| [IPC-2221](https://www.ipc.org/ipc-design-standards) | PCB spacing, layout and manufacturability | Editable layout and DRC; detailed clause review and physical board validation remain outside the demonstrator |
| [IPC-2152](https://www.ipc.org/TOC/IPC-2152.pdf) | Trace current/temperature-rise design | Motor current is carried by external drivers; logic-board current assumptions and conductor widths documented separately; no measured temperature-rise claim |
| [ISO 12100](https://www.iso.org/standard/51528.html) | Identify hazards and risk-reduction intentions | Hazard table below; simulation evidence only |
| [ISO 3691-4](https://www.iso.org/standard/83545.html) | Driverless industrial-truck motion and operating-zone considerations | Controlled simulated scene, speed limits, fault/stop experiments; scope-level mapping only |
| [ISO 13849-1](https://www.iso.org/standard/73481.html) | Separate safety-related fault response from ordinary commands | Independent simulated gate and PCB latch; no PL/SIL claim or certified component selection |
| [ROS REP 103](https://github.com/ros-infrastructure/rep/blob/master/rep-0103.rst) / [REP 105](https://github.com/ros-infrastructure/rep/blob/master/rep-0105.rst) | SI units and coordinate-frame ownership | map -> odom -> base_link, named wheel joints, timestamped messages |

Full paid standard texts were not reviewed. This mapping identifies applicable scopes and engineering intent, rather than clause-by-clause conformity. Verify current editions and local regulatory applicability for an actual product.

| Hazard in a future physical rover | Simulated reduction/test | Remaining limitation |
|---|---|---|
| Low traction | Independent velocity estimate, derating and matched friction tests | Tire/contact model omits lateral slip and tipping |
| Excess current | External-driver fault model plus independently latched drive gate | Comparator/driver response is behavioral; physical electrical faults untested |
| Stale command | 100 ms watchdog and drive disable | General-purpose OS transport is not safety rated |
| Lost localization/encoder | Confidence checks and stop request | Mechanical stopping depends on actual brakes and surface |
| IMU bias | Cross-check gyro against independent pose-heading change | Noise/latency thresholds are scenario-dependent |
| Unexpected restart | Latched gate; deliberate reset contract | Virtual startup is initialized armed after an assumed deliberate reset |

