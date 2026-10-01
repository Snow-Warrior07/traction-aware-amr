# Video transcript

## 00:00 - Traction-aware warehouse rover

This is a fully virtual warehouse rover project. It combines linear and nonlinear control, a friction-sensitive robot model, real ROS two messaging, and an editable controller PCB. This demonstration uses recorded measurements. No physical hardware is required.

## 00:20 - Model, sensors and control loop

The real-world problem is loss of traction when a loaded warehouse rover crosses a slippery patch. Independent wheel and body dynamics model that difference. A delayed pose sensor, encoders, and an IMU feed the controller. Physics runs at one kilohertz, wheel control at two hundred hertz, and trajectory control at fifty hertz.

## 00:43 - Linear control: LQR and wheel PI

The linear controller uses an L Q R trajectory loop and inner wheel P I control with anti-windup. This is a replay of the recorded sixteen second curved-route run. The rover follows the reference through the traction challenge. The moving-reference design is controllable and stable, and the worst dry-floor lateral error in the matrix is under nine millimeters R M S.

## 01:08 - Nonlinear control and traction supervision

The nonlinear controller uses heading-dependent sine and cosine terms. Its supervisor estimates slip from wheel speed and independent ground-speed estimates. Persistent slip reduces acceleration and torque, then hysteresis allows recovery. Here, both runs use the same reference and noise seed. The supervisor is active only when the sensor-based traction estimate calls for it.

## 01:34 - 540 matched simulations

The comparison contains four controllers, three traction conditions, three payloads, three routes, and five noise seeds. All five hundred and forty runs completed. Supervision reduced low-traction integrated slip by eighteen point eight percent with L Q R and eighteen point five percent with nonlinear control. The planned twenty percent hypothesis was not met.

## 02:00 - Actual ROS 2 graph and bag replay

The ROS test executed real publishers, subscribers, transforms, and a controller-selection service. It recorded and replayed a ROS bag, receiving four hundred and thirty replayed odometry messages. This diagram explains the tested graph; it is not a live ROS screen recording. The corrected Gazebo model also received real wheel torque through the ROS bridge. Both dry and low-friction cases moved the body, with increased wheel and body divergence on the slippery surface.

## 02:35 - Local KiCad 10: virtual carrier PCB

These are actual three-dimensional renders from the installed KiCad ten application. The custom, two-layer Pico carrier connects external motor drivers, encoders, an IMU, current filters, and a latched drive authorization gate. It has twenty-nine components and twenty-nine nets. The repaired schematic and board have zero electrical rule violations, zero layout rule violations, and zero unconnected items. Library keepouts, copper clearance, and drill spacing are respected. The editable project and exports are included on the desktop and website.

## 03:14 - Analog sensing and virtual I/O

Ngspice measured the current-sense filter time constant as one point zero zero one milliseconds, close to the one millisecond design value. The external driver signal is centered at one point six five volts. The virtual board includes signed twelve-bit current sensing, PWM quantization, command delay, an independent overcurrent trip, and a latched watchdog.

## 03:40 - Fault response: disable and coast

Five fault cases disable the drive: overcurrent, command timeout, encoder dropout, stale localization, and IMU bias. The faults start at five seconds. Qualification and timeout delays range from zero to one hundred and forty milliseconds. Cutting drive power does not stop motion instantly: the modeled rover coasts between one point one zero and one point four four meters. It has no emergency brake model.

## 04:10 - Measured soft real-time pacing

Four local wall-clock-paced tests each ran for approximately sixteen seconds. All met the twenty millisecond compute budget, with no compute deadline misses. The worst ninety-ninth percentile compute time was two point one three milliseconds. Compute duration and operating-system wake-up lateness are measured separately. These are soft real-time results on a normal Windows host.

## 04:36 - Result of every phase

Requirements, linear control, nonlinear control, ROS integration, and software testing have executed evidence. The plant model passes its mathematical checks and its separate Gazebo torque and contact test. The editable PCB passes local KiCad rule checks and its current filter passes circuit simulation. The GitHub demo website includes interactive measured replays, comparisons, project downloads, and a profile link. GitHub verification tests remain manual at your request.

## 05:10 - Demo, website and project delivered

The video, phase report, and interactive demo website are delivered through your GitHub project. The editable KiCad project is also on your desktop. The report includes the measured comparison, live timing, fault results, PCB findings, and reproducible commands. The project demonstrates control-engineering methods and industry design intent. It does not establish safety certification, manufacturing readiness, or physical robot performance.