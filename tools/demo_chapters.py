"""Measured-demo storyboard. No new GitHub operations or test runs."""
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
CHAPTERS=[
dict(key='intro',title='Traction-aware warehouse rover',phase='PROJECT DEMO',minimum=12,
 narration='This is a fully virtual warehouse rover project. It combines linear and nonlinear control, a friction-sensitive robot model, real ROS two messaging, and an editable controller PCB. This demonstration uses recorded measurements. No physical hardware is required.',
 caption='A software-only engineering prototype. Recorded measurements throughout.'),
dict(key='architecture',title='Model, sensors and control loop',phase='PHASES 1 + 2',minimum=15,
 narration='The real-world problem is loss of traction when a loaded warehouse rover crosses a slippery patch. Independent wheel and body dynamics model that difference. A delayed pose sensor, encoders, and an IMU feed the controller. Physics runs at one kilohertz, wheel control at two hundred hertz, and trajectory control at fifty hertz.',
 caption='Separate wheel/body dynamics. Delayed, noisy sensor estimates enter the controller.'),
dict(key='linear',title='Linear control: LQR and wheel PI',phase='PHASE 4',minimum=20,
 narration='The linear controller uses an L Q R trajectory loop and inner wheel P I control with anti-windup. This is a replay of the recorded sixteen second curved-route run. The rover follows the reference through the traction challenge. The moving-reference design is controllable and stable, and the worst dry-floor lateral error in the matrix is under nine millimeters R M S.',
 caption='A: LQR, supervisor off. Replay of an actual recorded 16-second run.'),
dict(key='nonlinear',title='Nonlinear control and traction supervision',phase='PHASE 5',minimum=20,
 narration='The nonlinear controller uses heading-dependent sine and cosine terms. Its supervisor estimates slip from wheel speed and independent ground-speed estimates. Persistent slip reduces acceleration and torque, then hysteresis allows recovery. Here, both runs use the same reference and noise seed. The supervisor is active only when the sensor-based traction estimate calls for it.',
 caption='C versus D: same route and seed. The state indicator shows when supervision is active.'),
dict(key='comparison',title='540 matched simulations',phase='PHASES 4 + 5 + 7',minimum=15,
 narration='The comparison contains four controllers, three traction conditions, three payloads, three routes, and five noise seeds. All five hundred and forty runs completed. Supervision reduced low-traction integrated slip by eighteen point eight percent with L Q R and eighteen point five percent with nonlinear control. The planned twenty percent hypothesis was not met.',
 caption='All 540 routes completed. The 20% slip-reduction hypothesis was not met.'),
dict(key='ros',title='Actual ROS 2 graph and bag replay',phase='PHASE 3',minimum=16,
 narration='The ROS test executed real publishers, subscribers, transforms, and a controller-selection service. It recorded and replayed a ROS bag, receiving four hundred and thirty replayed odometry messages. This diagram explains the tested graph; it is not a live ROS screen recording. The corrected Gazebo model also received real wheel torque through the ROS bridge. Both dry and low-friction cases moved the body, with increased wheel and body divergence on the slippery surface.',
 caption='Actual ROS traffic and Gazebo torque/contact checks passed. Graph is an explanatory diagram.'),
dict(key='pcb',title='Local KiCad 10: virtual carrier PCB',phase='PHASE 6',minimum=23,
 narration='These are actual three-dimensional renders from the installed KiCad ten application. The custom, two-layer Pico carrier connects external motor drivers, encoders, an IMU, current filters, and a latched drive authorization gate. It has twenty-nine components and twenty-nine nets. The repaired schematic and board have zero electrical rule violations, zero layout rule violations, and zero unconnected items. Library keepouts, copper clearance, and drill spacing are respected. The editable project and exports are included on the desktop and website.',
 caption='Actual KiCad 10.0.6 render. ERC: 0. DRC: 0. Unconnected items: 0.'),
dict(key='circuit',title='Analog sensing and virtual I/O',phase='PHASE 6',minimum=15,
 narration='Ngspice measured the current-sense filter time constant as one point zero zero one milliseconds, close to the one millisecond design value. The external driver signal is centered at one point six five volts. The virtual board includes signed twelve-bit current sensing, PWM quantization, command delay, an independent overcurrent trip, and a latched watchdog.',
 caption='Measured ngspice transient plus behavioral I/O. Whole-board electrical behavior is not simulated.'),
dict(key='faults',title='Fault response: disable and coast',phase='PHASE 7',minimum=18,
 narration='Five fault cases disable the drive: overcurrent, command timeout, encoder dropout, stale localization, and IMU bias. The faults start at five seconds. Qualification and timeout delays range from zero to one hundred and forty milliseconds. Cutting drive power does not stop motion instantly: the modeled rover coasts between one point one zero and one point four four meters. It has no emergency brake model.',
 caption='Drive disable is verified. Coasting distance is modeled; no industrial safe-stop claim.'),
dict(key='live',title='Measured soft real-time pacing',phase='PHASE 7',minimum=16,
 narration='Four local wall-clock-paced tests each ran for approximately sixteen seconds. All met the twenty millisecond compute budget, with no compute deadline misses. The worst ninety-ninth percentile compute time was two point one three milliseconds. Compute duration and operating-system wake-up lateness are measured separately. These are soft real-time results on a normal Windows host.',
 caption='Four recorded local live runs. 20 ms compute budget; zero misses. Soft real-time only.'),
dict(key='phases',title='Result of every phase',phase='PHASES 1-8',minimum=19,
 narration='Requirements, linear control, nonlinear control, ROS integration, and software testing have executed evidence. The plant model passes its mathematical checks and its separate Gazebo torque and contact test. The editable PCB passes local KiCad rule checks and its current filter passes circuit simulation. The GitHub demo website includes interactive measured replays, comparisons, project downloads, and a profile link. GitHub verification tests remain manual at your request.',
 caption='All eight phases have evidence for their stated virtual-project scope. The 20 percent hypothesis was not met.'),
dict(key='outro',title='Demo, website and project delivered',phase='DELIVERABLES',minimum=12,
 narration='The video, phase report, and interactive demo website are delivered through your GitHub project. The editable KiCad project is also on your desktop. The report includes the measured comparison, live timing, fault results, PCB findings, and reproducible commands. The project demonstrates control-engineering methods and industry design intent. It does not establish safety certification, manufacturing readiness, or physical robot performance.',
 caption='GitHub demo website, video, PDF report, transcript and editable Desktop KiCad project.')]

if __name__=='__main__':
    folder=ROOT/'.tools/demo';folder.mkdir(parents=True,exist_ok=True)
    (folder/'chapters.json').write_text(json.dumps(CHAPTERS,indent=2),encoding='utf-8')
    print(f'{len(CHAPTERS)} chapters prepared')
