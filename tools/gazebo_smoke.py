"""Run actual headless Gazebo torque actuation through a ROS/Gazebo bridge."""
import json
import os
from pathlib import Path
import signal
import subprocess
import time
import rclpy
from rclpy.node import Node
from nav_msgs.msg import Odometry
from sensor_msgs.msg import JointState
from std_msgs.msg import Float64
ROOT=Path(__file__).resolve().parents[1]
rclpy.init();results=[]
for case in ["warehouse","warehouse_low_friction"]:
    log=(ROOT/"results"/(case+"_gazebo.log")).open("w")
    server=subprocess.Popen(["gz","sim","-s","-r",str(ROOT/"models"/(case+".sdf"))],stdout=log,stderr=log)
    bridge=None;node=None
    try:
        time.sleep(4)
        topics=subprocess.check_output(["gz","topic","-l"],text=True,timeout=10)
        joints=next(line for line in topics.splitlines() if "joint_state" in line)
        left="/model/rover/joint/left_wheel_joint/cmd_force";right="/model/rover/joint/right_wheel_joint/cmd_force"
        bridge=subprocess.Popen(["ros2","run","ros_gz_bridge","parameter_bridge",
            left+"@std_msgs/msg/Float64@gz.msgs.Double",right+"@std_msgs/msg/Float64@gz.msgs.Double",
            "/model/rover/odometry@nav_msgs/msg/Odometry@gz.msgs.Odometry",
            joints+"@sensor_msgs/msg/JointState@gz.msgs.Model"],stdout=log,stderr=log)
        node=Node("gazebo_verification");samples=[];wheel=[]
        def odom(m):samples.append((m.pose.pose.position.x,m.twist.twist.linear.x))
        def joint(m):wheel.append(list(m.velocity))
        node.create_subscription(Odometry,"/model/rover/odometry",odom,10)
        node.create_subscription(JointState,joints,joint,10)
        pubs=[node.create_publisher(Float64,left,10),node.create_publisher(Float64,right,10)]
        deadline=time.monotonic()+2
        while time.monotonic()<deadline:rclpy.spin_once(node,timeout_sec=.02)
        assert samples,"No Gazebo odometry through bridge"
        x0=samples[-1][0];started=time.monotonic();next_tick=started
        while time.monotonic()-started<1.5:
            for pub in pubs:pub.publish(Float64(data=.8))
            rclpy.spin_once(node,timeout_sec=.02)
            next_tick+=.02
            if time.monotonic()<next_tick:time.sleep(next_tick-time.monotonic())
        for pub in pubs:pub.publish(Float64(data=0.))
        assert wheel and len(samples)>30,"Missing dynamics samples"
        v=samples[-1][1];w=max(abs(x) for x in wheel[-1])
        result={"case":case,"odom_messages":len(samples),"wheel_messages":len(wheel),
            "displacement_m":samples[-1][0]-x0,"body_speed_m_s":v,"wheel_speed_rad_s":w,
            "wheel_body_divergence_m_s":.075*w-abs(v),"ros_gazebo_bridge":True,"effort_nm":.8}
        assert result["displacement_m"]>.05
        results.append(result);print(json.dumps(result),flush=True)
    finally:
        if node:node.destroy_node()
        if bridge:bridge.terminate();bridge.wait(timeout=10)
        server.terminate();server.wait(timeout=10);log.close()
        time.sleep(1)
rclpy.shutdown()
assert results[1]["wheel_body_divergence_m_s"]>results[0]["wheel_body_divergence_m_s"]+.1
(ROOT/"results"/"gazebo_smoke.json").write_text(json.dumps(results,indent=2))

