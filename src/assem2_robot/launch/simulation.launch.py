import os
from pathlib import Path

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, SetEnvironmentVariable
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import EnvironmentVariable, LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    pkg_name = 'assem2_robot'
    package_path = get_package_share_directory(pkg_name)
    package_share_path = os.path.dirname(package_path)

    urdf_path = os.path.join(package_path, 'urdf', 'Assem2.SLDASM.urdf')
    rviz_path = os.path.join(package_path, 'config', 'display.rviz')

    with open(urdf_path, 'r') as f:
        robot_description_content = f.read()

    use_sim_time = LaunchConfiguration('use_sim_time', default='true')

    declare_use_sim_time = DeclareLaunchArgument(
        'use_sim_time',
        default_value='true',
        description='Use simulation (Gazebo) clock if true'
    )

    # Gazebo Sim launch (Gazebo Harmonic / Gz Sim)
    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(
                get_package_share_directory('ros_gz_sim'),
                'launch',
                'gz_sim.launch.py'
            )
        ),
        launch_arguments={'gz_args': '-r empty.sdf'}.items()
    )

    # Robot State Publisher
    robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        name='robot_state_publisher',
        output='screen',
        parameters=[
            {'robot_description': robot_description_content},
            {'use_sim_time': use_sim_time}
        ]
    )

    # Spawn Robot in Gazebo
    spawn_robot = Node(
        package='ros_gz_sim',
        executable='create',
        output='screen',
        arguments=[
            '-name', 'assem2_robot',
            '-string', robot_description_content,
            '-z', '0.25'
        ]
    )

    # ROS-Gazebo Parameter Bridge
    bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        output='screen',
        arguments=[
            '/cmd_vel@geometry_msgs/msg/Twist@gz.msgs.Twist',
            '/odom@nav_msgs/msg/Odometry[gz.msgs.Odometry',
            '/tf@tf2_msgs/msg/TFMessage[gz.msgs.Pose_V',
            '/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock',
            '/joint_states@sensor_msgs/msg/JointState[gz.msgs.Model',
        ],
        parameters=[{'use_sim_time': use_sim_time}]
    )

    # RViz2 Node
    rviz = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        output='screen',
        arguments=['-d', rviz_path] if os.path.exists(rviz_path) else [],
        parameters=[{'use_sim_time': use_sim_time}]
    )

    return LaunchDescription([
        # Ensure Gazebo Sim can find robot mesh packages
        SetEnvironmentVariable(
            name='GZ_SIM_RESOURCE_PATH',
            value=[
                package_share_path,
                ':',
                EnvironmentVariable('GZ_SIM_RESOURCE_PATH', default_value='')
            ]
        ),
        SetEnvironmentVariable(
            name='IGN_GAZEBO_RESOURCE_PATH',
            value=[
                package_share_path,
                ':',
                EnvironmentVariable('IGN_GAZEBO_RESOURCE_PATH', default_value='')
            ]
        ),
        declare_use_sim_time,
        gazebo,
        robot_state_publisher,
        spawn_robot,
        bridge,
        rviz
    ])
