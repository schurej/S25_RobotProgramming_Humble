from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        Node(
            package='yolo_color_tracker',
            executable='detection_node',
            name='detection_node',
            parameters=[{
                'target_object': 'apple',
                'image_topic':   '/camera/color/image_raw',
            }],
        ),
        Node(
            package='yolo_tracker',
            executable='detection_3d_node',
            name='detection_3d_node',
        ),
        Node(
            package='yolo_tracker',
            executable='wheelodom_tf',
            name='wheelodom_tf',
        ),

        Node(
            package='yolo_tracker',
            executable='color_changer_service',
            name='color_changer_service',
        ),

        Node(
            package='yolo_tracker',
            executable='tracking_node',
            name='tracking_node',
        ),
    ])

