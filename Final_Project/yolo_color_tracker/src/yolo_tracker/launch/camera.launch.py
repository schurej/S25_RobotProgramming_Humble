from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_xml.launch_description_sources import XMLLaunchDescriptionSource  # ? correct import
import os
from ament_index_python.packages import get_package_share_directory

def generate_launch_description():
    cam_pkg    = 'astra_camera'
    xml_file   = 'astro_pro_plus.launch.xml'
    xml_path   = os.path.join(
        get_package_share_directory(cam_pkg),
        'launch',
        xml_file
    )

    return LaunchDescription([
        IncludeLaunchDescription(
            XMLLaunchDescriptionSource(xml_path),
            launch_arguments={
                'display_rgb':   'false',
                'display_depth': 'false',
            }.items()
        )
    ])
