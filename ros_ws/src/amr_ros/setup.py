from setuptools import setup
from glob import glob
setup(name="amr_ros",version="0.1.0",packages=["amr_ros"],
      data_files=[("share/ament_index/resource_index/packages",["resource/amr_ros"]),
                  ("share/amr_ros",["package.xml"]),("share/amr_ros/launch",glob("launch/*.py"))],
      entry_points={"console_scripts":["plant=amr_ros.nodes:plant_main","controller=amr_ros.nodes:controller_main"]})
