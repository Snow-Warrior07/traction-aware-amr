"""Execute actual DDS pub/sub, service calls, TF reception and bag record/replay."""
import json
import signal
import subprocess
import time
from pathlib import Path
import rclpy
from rclpy.node import Node
from rclpy.executors import SingleThreadedExecutor
from std_msgs.msg import Float64MultiArray
from nav_msgs.msg import Odometry
from tf2_msgs.msg import TFMessage
from std_srvs.srv import SetBool
from amr_ros.nodes import PlantNode,ControllerNode

root=Path(__file__).resolve().parents[1]
rclpy.init();plant=PlantNode();controller=ControllerNode();monitor=Node("verification_monitor")
executor=SingleThreadedExecutor()
for node in [plant,controller,monitor]:executor.add_node(node)
counts={"odom":0,"commands":0,"tf":0};positions=[]
def odom(msg):counts["odom"]+=1;positions.append(msg.pose.pose.position.x)
def command(msg):counts["commands"]+=1
def transform(msg):counts["tf"]+=1
monitor.create_subscription(Odometry,"/odom",odom,10)
monitor.create_subscription(Float64MultiArray,"/drive/wheel_targets",command,10)
monitor.create_subscription(TFMessage,"/tf",transform,10)
bag=root/"results"/"ros_bag"
record=subprocess.Popen(["ros2","bag","record","-o",str(bag),"/odom","/reference","/drive/wheel_targets","/tf"])
started=time.monotonic();deadline=started+9
while time.monotonic()<deadline:executor.spin_once(timeout_sec=.02)
client=monitor.create_client(SetBool,"/controller/use_nonlinear")
assert client.wait_for_service(timeout_sec=3)
request=SetBool.Request();request.data=False;future=client.call_async(request)
executor.spin_until_future_complete(future,timeout_sec=3)
assert future.result() is not None and future.result().success
record.send_signal(signal.SIGINT);record.wait(timeout=15)
before=counts["odom"]
executor.remove_node(plant);executor.remove_node(controller)
plant.destroy_node();controller.destroy_node()
replay=subprocess.Popen(["ros2","bag","play",str(bag),"--rate","4"])
deadline=time.monotonic()+8
while time.monotonic()<deadline and replay.poll() is None:executor.spin_once(timeout_sec=.02)
if replay.poll() is None:replay.terminate()
replay.wait(timeout=5)
result={"elapsed_live_s":time.monotonic()-started,"messages":counts,"body_displacement_m":max(positions)-min(positions),
        "service_success":future.result().success,"replayed_odom_messages":counts["odom"]-before,
        "bag_created":(bag/"metadata.yaml").exists()}
assert before>100 and counts["commands"]>100 and counts["tf"]>100
assert result["body_displacement_m"]>.5 and result["replayed_odom_messages"]>50 and result["bag_created"]
(root/"results"/"ros_smoke.json").write_text(json.dumps(result,indent=2))
print(json.dumps(result,indent=2))
monitor.destroy_node();rclpy.shutdown()
