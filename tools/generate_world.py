from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def world(mu=.8):
    wheel=''
    for side,y in [("left",.19),("right",-.19)]:
        wheel+=f'''<link name="{side}_wheel"><pose>0 {y} .075 1.57079632679 0 0</pose>
        <inertial><mass>.25</mass><inertia><ixx>.0004</ixx><iyy>.0004</iyy><izz>.0007</izz></inertia></inertial>
        <collision name="collision"><geometry><cylinder><radius>.075</radius><length>.04</length></cylinder></geometry><surface><friction><ode><mu>1</mu><mu2>1</mu2></ode></friction></surface></collision>
        <visual name="visual"><geometry><cylinder><radius>.075</radius><length>.04</length></cylinder></geometry><material><diffuse>.1 .1 .1 1</diffuse></material></visual></link>
        <joint name="{side}_wheel_joint" type="revolute"><parent>base_link</parent><child>{side}_wheel</child><axis><xyz expressed_in="__model__">0 1 0</xyz><limit><lower>-1e16</lower><upper>1e16</upper></limit><dynamics><damping>.003</damping></dynamics></axis></joint>
        <plugin filename="gz-sim-apply-joint-force-system" name="gz::sim::systems::ApplyJointForce"><joint_name>{side}_wheel_joint</joint_name></plugin>'''
    return f'''<?xml version="1.0"?><sdf version="1.9"><world name="warehouse">
    <physics name="physics" type="ignored"><max_step_size>.001</max_step_size><real_time_factor>1</real_time_factor></physics>
    <plugin filename="gz-sim-physics-system" name="gz::sim::systems::Physics"/>
    <plugin filename="gz-sim-user-commands-system" name="gz::sim::systems::UserCommands"/>
    <plugin filename="gz-sim-scene-broadcaster-system" name="gz::sim::systems::SceneBroadcaster"/>
    <gravity>0 0 -9.81</gravity>
    <light name="sun" type="directional"><pose>0 0 10 0 0 0</pose><diffuse>1 1 1 1</diffuse><direction>-.5 .1 -1</direction></light>
    <model name="floor"><static>true</static><link name="link"><collision name="collision"><geometry><plane><normal>0 0 1</normal><size>30 20</size></plane></geometry><surface><friction><ode><mu>{mu}</mu><mu2>{mu}</mu2></ode></friction></surface></collision><visual name="visual"><geometry><plane><normal>0 0 1</normal><size>30 20</size></plane></geometry><material><diffuse>.4 .45 .5 1</diffuse></material></visual></link></model>
    <model name="rover"><link name="base_link"><pose>0 0 .18 0 0 0</pose><inertial><mass>11.4</mass><inertia><ixx>.15</ixx><iyy>.22</iyy><izz>.5</izz></inertia></inertial>
    <collision name="body"><geometry><box><size>.44 .30 .12</size></box></geometry></collision><visual name="body"><geometry><box><size>.44 .30 .12</size></box></geometry><material><diffuse>.05 .4 .65 1</diffuse></material></visual>
    <visual name="virtual_pcb"><pose>0 0 .071 0 0 0</pose><geometry><box><size>.096 .096 .0016</size></box></geometry><material><diffuse>.05 .55 .2 1</diffuse></material></visual></link>
    <link name="caster"><pose>-.17 0 .035 0 0 0</pose><inertial><mass>.1</mass><inertia><ixx>.0001</ixx><iyy>.0001</iyy><izz>.0001</izz></inertia></inertial><collision name="collision"><geometry><sphere><radius>.035</radius></sphere></geometry><surface><friction><ode><mu>.001</mu><mu2>.001</mu2></ode></friction></surface></collision></link>
    <joint name="caster_joint" type="fixed"><parent>base_link</parent><child>caster</child></joint>
    {wheel}<plugin filename="gz-sim-odometry-publisher-system" name="gz::sim::systems::OdometryPublisher"><odom_frame>odom</odom_frame><robot_base_frame>base_link</robot_base_frame><odom_publish_frequency>50</odom_publish_frequency><dimensions>3</dimensions><odom_topic>/model/rover/odometry</odom_topic></plugin>
    <plugin filename="gz-sim-joint-state-publisher-system" name="gz::sim::systems::JointStatePublisher"/>
    </model></world></sdf>'''
if __name__=="__main__":
    out=ROOT/"models";out.mkdir(exist_ok=True)
    for name,mu in [("warehouse",.8),("warehouse_low_friction",.1)]:
        (out/(name+".sdf")).write_text(world(mu))

