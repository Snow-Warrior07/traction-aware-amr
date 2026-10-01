from launch import LaunchDescription
from launch_ros.actions import Node
def generate_launch_description():
    return LaunchDescription([Node(package="amr_ros",executable="plant",output="screen"),
                              Node(package="amr_ros",executable="controller",output="screen")])
