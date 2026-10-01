# Traction-aware warehouse rover

An entirely virtual control-engineering project: a differential-drive rover, linear PI/LQR and nonlinear tracking, traction estimation/supervision, ROS 2, a custom controller PCB, and live tests.

The plant models independent wheel/body velocity, motor current, payload and friction-limited contact. A noisy delayed pose sensor plus wheel encoders and IMU feeds the estimator. Simulator truth is used only for sensor generation and evaluation.

## Run locally

Use Python 3.12 and a 64-bit C++ compiler. Linux is the simplest reproduction environment. The Windows development host used MATLAB R2024b's installed LCC64 with the same C-compatible C++ source because its MinGW installation is 32-bit. Windows runtime math functions are bound explicitly; Linux uses standard libm.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m pytest -q
python -m amr.experiments smoke
python -m amr.experiments matrix --workers 4
python -m amr.experiments live --variant D --seconds 16
python -m amr.experiments faults
```

On Windows, use `.venv\Scripts\python.exe` for the Python commands. The native library is compiled from `firmware/core.cpp` on first import. Generated measurements go into `results/`.

## Phases

1. Requirements and fixed experiment criteria: `docs/requirements.md`, `config/robot.yaml`, `experiments/scenarios.yaml`.
2. Plant/contact dynamics and warehouse model: `firmware/core.cpp`, `amr/simulation.py`, `tools/generate_world.py`.
3. Actual ROS graph, service, TF and bag replay: `ros_ws/`, `tools/ros_smoke.py`, `tools/gazebo_smoke.py`.
4. Linear wheel PI and trajectory LQR: `amr/control.py`, native control core, stability and tracking tests.
5. Nonlinear controller, sensor estimator and supervisor: matched A/B/C/D comparison.
6. Pico carrier PCB, RC circuit and virtual I/O: `tools/generate_pcb.py`, `hardware/spice/`, `amr/board.py`.
7. Regression, faults, live timing and standards mapping: tests, saved results, phase report.
8. GitHub verification and public release: Actions artifacts and static demonstration.

Each phase is reported from executed evidence. A source file alone does not establish an unexecuted check as passing. The public repository may show work in progress until the verification workflow and final evidence audit complete.

## Controller comparison

| Variant | Outer controller | Traction supervisor |
|---|---|---|
| A | LQR | Off |
| B | LQR | On |
| C | Nonlinear | Off |
| D | Nonlinear | On |

The full matrix contains 540 runs: four variants, three traction conditions, three payloads, three routes and five noise seeds. Acceleration/braking demands exercise traction while crossing a low-friction patch. Slip reduction is measured rather than assumed, and delivery-time/error/energy tradeoffs remain visible.

## ROS and PCB verification

The workflow runs Ubuntu 24.04, ROS 2 Jazzy/Gazebo Harmonic and KiCad 9/ngspice. ROS tests execute real DDS traffic, controller commands, transforms, a service call, and rosbag record/replay. Gazebo receives wheel effort through `ros_gz_bridge` and compares dry/low-friction contact. The four-controller matrix uses the inspectable mathematical plant; Gazebo contact tests are a separate validation, not identical numerical replicas.

The PCB is a custom Raspberry Pi Pico carrier for external motor drivers. Motor power does not flow through the logic carrier. External drivers provide 0.1 V/A centered current measurements and active-low faults; the PCB filters measurements and latches drive authorization independently of ROS. Part choices, pin assignments, routing and exports are inspectable. Selected RC circuits are modeled in ngspice; the whole assembled board, EMI and embedded timing are not physically validated.

Live runs are wall-clock-paced soft real-time tests on ordinary operating systems. Reports include compute deadline misses and wake-up lateness separately. They do not demonstrate hard real-time scheduling or safety certification.

See `docs/control-derivation.md`, `docs/standards.md`, and the measured `results/` files for model assumptions and scope.

