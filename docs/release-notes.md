The traction-aware AMR virtual engineering demonstrator combines linear PI/LQR, nonlinear tracking, independent sensor estimation, traction supervision, ROS 2 and a custom KiCad Pico carrier.

- Interactive GitHub Pages demo: controller replay/overlays, filtered 540-case matrix, PCB views, ROS evidence, timing/fault tables and narrated video.
- Editable Desktop/downloadable KiCad 10 project: zero local ERC, all-track DRC, unconnected and schematic-parity findings; Gerbers, drills, netlist, BOM and board STEP included.
- Saved ROS DDS/TF/service/bag replay and corrected Gazebo dry/low-friction wheel-effort contact evidence.
- Phase report, source hashes, 540 completed routes, four recorded paced runs and five modeled fault cases.

Low-traction slip reduction was 18.76% (LQR) and 18.48% (nonlinear); the 20% hypothesis was not met. The project is entirely virtual, uses soft real-time scheduling and makes no safety certification, physical performance or manufacturing-readiness claim. GitHub verification tests remain manual; prior test failures were set aside at the user's request.
