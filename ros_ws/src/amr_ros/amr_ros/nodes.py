import math
from dataclasses import astuple
import rclpy
from rclpy.node import Node
from std_msgs.msg import Float64MultiArray,String
from nav_msgs.msg import Odometry
from geometry_msgs.msg import TransformStamped,PoseStamped
from sensor_msgs.msg import Imu,JointState
from rosgraph_msgs.msg import Clock
from std_srvs.srv import SetBool,Trigger
from tf2_ros import TransformBroadcaster,StaticTransformBroadcaster
from amr.simulation import Simulation
from amr.control import Controller,Observation

class PlantNode(Node):
    def __init__(self):
        super().__init__("amr_plant")
        for name,value in [("surface","patch"),("payload",0.),("trajectory","curved"),("duration",16.)]:self.declare_parameter(name,value)
        self.reset()
        self.observation=self.create_publisher(Float64MultiArray,"/amr/observation",10)
        self.reference=self.create_publisher(Float64MultiArray,"/reference",10)
        self.odom=self.create_publisher(Odometry,"/odom",10)
        self.pose=self.create_publisher(PoseStamped,"/localization/pose",10)
        self.imu=self.create_publisher(Imu,"/imu/data",10)
        self.wheels=self.create_publisher(JointState,"/wheel_states",10)
        self.truth=self.create_publisher(Odometry,"/sim/ground_truth",10)
        self.status=self.create_publisher(String,"/diagnostics",10)
        self.clock=self.create_publisher(Clock,"/clock",10)
        self.tf=TransformBroadcaster(self);self.static_tf=StaticTransformBroadcaster(self)
        static=TransformStamped();static.header.frame_id="map";static.child_frame_id="odom";static.transform.rotation.w=1.
        self.static_tf.sendTransform(static)
        self.create_subscription(Float64MultiArray,"/drive/wheel_targets",self.targets,10)
        self.create_service(Trigger,"/amr/reset",self.reset_service)
        self.create_timer(.02,self.advance)
    def reset(self):
        p=lambda name:self.get_parameter(name).value
        self.sim=Simulation("D",p("surface"),p("payload"),p("trajectory"),duration=p("duration"),external=True)
    def reset_service(self,request,response):
        self.reset();response.success=True;response.message="simulation reset";return response
    def targets(self,message):
        if len(message.data)==3:
            self.sim.wtargets=tuple(message.data);self.sim.last_external_command=self.sim.t
    def advance(self):
        self.sim.step(20);s=self.sim;obs=s.last_observation
        msg=Float64MultiArray();msg.data=[float(x) for x in astuple(obs)];self.observation.publish(msg)
        ref=Float64MultiArray();ref.data=s.ref.tolist();self.reference.publish(ref)
        stamp=rclpy.time.Time(seconds=s.tick*s.dt).to_msg()
        clk=Clock();clk.clock=stamp;self.clock.publish(clk)
        od=Odometry();od.header.stamp=stamp;od.header.frame_id="odom";od.child_frame_id="base_link"
        od.pose.pose.position.x=obs.x;od.pose.pose.position.y=obs.y
        od.pose.pose.orientation.z=math.sin(obs.yaw/2);od.pose.pose.orientation.w=math.cos(obs.yaw/2)
        od.twist.twist.linear.x=obs.v;od.twist.twist.angular.z=obs.yaw_rate;self.odom.publish(od)
        truth=Odometry();truth.header=od.header;truth.child_frame_id="truth_base"
        truth.pose.pose.position.x=float(s.state[0]);truth.pose.pose.position.y=float(s.state[1])
        truth.pose.pose.orientation.z=math.sin(s.state[2]/2);truth.pose.pose.orientation.w=math.cos(s.state[2]/2)
        truth.twist.twist.linear.x=float(s.state[3]);self.truth.publish(truth)
        pose=PoseStamped();pose.header=od.header;pose.pose=od.pose.pose;self.pose.publish(pose)
        imu=Imu();imu.header.stamp=stamp;imu.header.frame_id="base_link";imu.angular_velocity.z=obs.yaw_rate;self.imu.publish(imu)
        joints=JointState();joints.header.stamp=stamp;joints.name=["left_wheel_joint","right_wheel_joint"]
        joints.position=s.angles.tolist();joints.velocity=[obs.wl,obs.wr];self.wheels.publish(joints)
        tf=TransformStamped();tf.header=od.header;tf.child_frame_id="base_link"
        tf.transform.translation.x=obs.x;tf.transform.translation.y=obs.y;tf.transform.rotation=od.pose.pose.orientation;self.tf.sendTransform(tf)
        self.status.publish(String(data="drive_enabled="+str(s.board.enabled)+"; fault="+s.board.reason))

class ControllerNode(Node):
    def __init__(self):
        super().__init__("amr_controller");self.declare_parameter("nonlinear",True);self.declare_parameter("supervisor",True)
        self.core=Controller("nonlinear" if self.get_parameter("nonlinear").value else "lqr",self.get_parameter("supervisor").value)
        self.ref=[0.,0.,0.,0.,0.];self.pub=self.create_publisher(Float64MultiArray,"/drive/wheel_targets",10)
        self.create_subscription(Float64MultiArray,"/reference",self.reference,10)
        self.create_subscription(Float64MultiArray,"/amr/observation",self.observation,10)
        self.create_service(SetBool,"/controller/use_nonlinear",self.choose)
    def reference(self,message):self.ref=list(message.data)
    def choose(self,request,response):
        self.core=Controller("nonlinear" if request.data else "lqr",self.core.supervisor)
        response.success=True;response.message="controller selected; reset plant for a new comparison run";return response
    def observation(self,message):
        obs=Observation(*message.data[:8],bool(message.data[8]))
        command=self.core.update(obs,self.ref)
        out=Float64MultiArray();out.data=list(command);self.pub.publish(out)

def run(cls):
    rclpy.init();node=cls()
    try:rclpy.spin(node)
    finally:node.destroy_node();rclpy.shutdown()
def plant_main():run(PlantNode)
def controller_main():run(ControllerNode)
