import os
from pathlib import Path

from ament_index_python.packages import get_package_share_directory, PackageNotFoundError
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, SetEnvironmentVariable
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import EnvironmentVariable, LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    pkg_name = 'assem2_robot'
    package_path = get_package_share_directory(pkg_name)
    package_share_path = os.path.dirname(package_path)

    urdf_path = os.path.join(package_path, 'urdf', 'Assem2.SLDASM.urdf')
    rviz_path = os.path.join(package_path, 'config', 'display.rviz')
    ekf_config_path = os.path.join(package_path, 'config', 'ekf.yaml')
    slam_config_path = os.path.join(package_path, 'config', 'slam_toolbox.yaml')
    nav2_config_path = os.path.join(package_path, 'config', 'nav2_params.yaml')
    default_map_path = os.path.join(package_path, 'maps', 'amr_world_map.yaml')

    with open(urdf_path, 'r') as f:
        robot_description_content = f.read()

    world_path = os.path.join(package_path, 'worlds', 'amr_world.sdf')

    use_sim_time = LaunchConfiguration('use_sim_time', default='true')
    use_ekf = LaunchConfiguration('use_ekf', default='true')
    use_slam = LaunchConfiguration('use_slam', default='false')
    use_nav = LaunchConfiguration('use_nav', default='false')
    map_file = LaunchConfiguration('map', default=default_map_path)
    world = LaunchConfiguration('world', default=world_path)

    declare_use_sim_time = DeclareLaunchArgument(
        'use_sim_time',
        default_value='true',
        description='Use simulation (Gazebo) clock if true'
    )

    declare_use_ekf = DeclareLaunchArgument(
        'use_ekf',
        default_value='true',
        description='Enable EKF sensor fusion (robot_localization)'
    )

    declare_use_slam = DeclareLaunchArgument(
        'use_slam',
        default_value='false',
        description='Enable SLAM mapping (slam_toolbox)'
    )

    declare_use_nav = DeclareLaunchArgument(
        'use_nav',
        default_value='false',
        description='Enable Nav2 autonomous navigation stack'
    )

    declare_map = DeclareLaunchArgument(
        'map',
        default_value=default_map_path,
        description='Full path to map YAML file for Nav2'
    )

    declare_world = DeclareLaunchArgument(
        'world',
        default_value=world_path,
        description='Path to Gazebo world SDF file'
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
        launch_arguments={'gz_args': ['-r ', world]}.items()
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

    # Spawn Robot in Gazebo (single instance, no auto-duplication)
    spawn_robot = Node(
        package='ros_gz_sim',
        executable='create',
        output='screen',
        arguments=[
            '-name', 'assem2_robot',
            '-string', robot_description_content,
            '-allow_renaming', 'false',
            '-x', '0.0',
            '-y', '0.0',
            '-z', '0.02'
        ]
    )

    # ROS-Gazebo Parameter Bridge for actuators, odometry, and integrated sensors
    bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        output='screen',
        arguments=[
            # Actuation & Teleop
            '/cmd_vel@geometry_msgs/msg/Twist@gz.msgs.Twist',
            # Odometry & Joint States & Clock
            '/odom@nav_msgs/msg/Odometry[gz.msgs.Odometry',
            '/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock',
            '/joint_states@sensor_msgs/msg/JointState[gz.msgs.Model',
            # 2D LiDAR
            '/scan@sensor_msgs/msg/LaserScan[gz.msgs.LaserScan',
            # IMU
            '/imu@sensor_msgs/msg/Imu[gz.msgs.IMU',
            # RGB-D / Depth Camera
            '/camera/image_raw@sensor_msgs/msg/Image[gz.msgs.Image',
            '/camera/camera_info@sensor_msgs/msg/CameraInfo[gz.msgs.CameraInfo',
            '/camera/depth_image@sensor_msgs/msg/Image[gz.msgs.Image',
            '/camera/points@sensor_msgs/msg/PointCloud2[gz.msgs.PointCloudPacked',
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

    nodes_to_launch = [
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
        declare_use_ekf,
        declare_use_slam,
        declare_use_nav,
        declare_map,
        declare_world,
        gazebo,
        robot_state_publisher,
        spawn_robot,
        bridge,
        rviz
    ]

    try:
        get_package_share_directory('robot_localization')
        robot_localization_node = Node(
            package='robot_localization',
            executable='ekf_node',
            name='ekf_filter_node',
            output='screen',
            parameters=[
                ekf_config_path,
                {'use_sim_time': use_sim_time}
            ],
            remappings=[
                ('odometry/filtered', '/odometry/filtered')
            ],
            condition=IfCondition(use_ekf)
        )
        nodes_to_launch.append(robot_localization_node)
    except PackageNotFoundError:
        pass

    try:
        get_package_share_directory('slam_toolbox')
        slam_launch = IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                os.path.join(
                    get_package_share_directory('slam_toolbox'),
                    'launch',
                    'online_async_launch.py'
                )
            ),
            launch_arguments={
                'use_sim_time': use_sim_time,
                'slam_params_file': slam_config_path,
                'autostart': 'true'
            }.items(),
            condition=IfCondition(use_slam)
        )
        nodes_to_launch.append(slam_launch)
    except PackageNotFoundError:
        pass

    try:
        get_package_share_directory('nav2_bringup')
        nav2_launch = IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                os.path.join(
                    get_package_share_directory('nav2_bringup'),
                    'launch',
                    'bringup_launch.py'
                )
            ),
            launch_arguments={
                'map': map_file,
                'use_sim_time': use_sim_time,
                'params_file': nav2_config_path,
                'autostart': 'true'
            }.items(),
            condition=IfCondition(use_nav)
        )
        nodes_to_launch.append(nav2_launch)
    except PackageNotFoundError:
        pass

    return LaunchDescription(nodes_to_launch)
