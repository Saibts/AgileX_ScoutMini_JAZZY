import os
from pathlib import Path

from ament_index_python.packages import get_package_share_directory, PackageNotFoundError
from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    ExecuteProcess,
    IncludeLaunchDescription,
    SetEnvironmentVariable
)
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import EnvironmentVariable, LaunchConfiguration, PythonExpression
from launch_ros.actions import Node


def generate_launch_description():
    pkg_name = 'assem2_robot'
    package_path = get_package_share_directory(pkg_name)
    package_share_path = os.path.dirname(package_path)

    urdf_path = os.path.join(package_path, 'urdf', 'Assem2.SLDASM.urdf')
    rviz_civil_path = os.path.join(package_path, 'config', 'civil_display.rviz')
    rviz_path = rviz_civil_path if os.path.exists(rviz_civil_path) else os.path.join(package_path, 'config', 'display.rviz')
    ekf_config_path = os.path.join(package_path, 'config', 'ekf.yaml')
    slam_config_path = os.path.join(package_path, 'config', 'slam_toolbox.yaml')
    nav2_config_path = os.path.join(package_path, 'config', 'nav2_params.yaml')
    default_map_path = os.path.join(package_path, 'maps', 'civil_map.yaml')

    with open(urdf_path, 'r') as f:
        robot_description_content = f.read()

    world_path = os.path.join(package_path, 'worlds', 'civil_world.sdf')

    use_sim_time = LaunchConfiguration('use_sim_time', default='true')
    use_ekf = LaunchConfiguration('use_ekf', default='true')
    use_slam = LaunchConfiguration('use_slam', default='false')
    use_nav = LaunchConfiguration('use_nav', default='false')
    use_gui = LaunchConfiguration('use_gui', default='false')
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

    declare_use_gui = DeclareLaunchArgument(
        'use_gui',
        default_value='false',
        description='Launch AgileX Interactive Civil Navigation Ground Station GUI'
    )

    declare_map = DeclareLaunchArgument(
        'map',
        default_value=default_map_path,
        description='Full path to map YAML file for Nav2'
    )

    declare_world = DeclareLaunchArgument(
        'world',
        default_value=world_path,
        description='Path to Gazebo civil world SDF file'
    )

    # Direct Gazebo Harmonic execution with civil_world.sdf
    gazebo = ExecuteProcess(
        cmd=['gz', 'sim', '-r', world_path],
        output='screen'
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

    # ROS-Gazebo Parameter Bridge for actuators, odometry, and integrated sensors
    bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        output='screen',
        arguments=[
            # Actuation & Teleop (One-way ROS -> Gazebo)
            '/cmd_vel@geometry_msgs/msg/Twist]gz.msgs.Twist',
            # Odometry & Joint States & Clock
            '/odom@nav_msgs/msg/Odometry[gz.msgs.Odometry',
            '/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock',
            '/joint_states@sensor_msgs/msg/JointState[gz.msgs.Model',
            # 2D LiDAR (Navigation & Obstacle Avoidance)
            '/scan@sensor_msgs/msg/LaserScan[gz.msgs.LaserScan',
            # IMU
            '/imu@sensor_msgs/msg/Imu[gz.msgs.IMU',
            # Forward Color Camera (Ground Station Live POV Feed)
            '/camera/image@sensor_msgs/msg/Image[gz.msgs.Image',
            '/camera/camera_info@sensor_msgs/msg/CameraInfo[gz.msgs.CameraInfo',
        ],
        remappings=[
            ('/camera/image', '/camera/image_raw')
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
        SetEnvironmentVariable(name='ROS_DOMAIN_ID', value='19'),
        SetEnvironmentVariable(name='ROS_LOCALHOST_ONLY', value='1'),
        SetEnvironmentVariable(name='ROS_AUTOMATIC_DISCOVERY_RANGE', value='LOCALHOST'),
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
        declare_use_gui,
        declare_map,
        declare_world,
        gazebo,
        robot_state_publisher,
        bridge,
        rviz
    ]

    # When neither SLAM nor Nav2 is active, broadcast a static map -> odom transform
    # so RViz (defaulted to Fixed Frame: map) renders without TF errors.
    static_map_to_odom = Node(
        package='tf2_ros',
        executable='static_transform_publisher',
        name='static_map_to_odom',
        arguments=['--frame-id', 'map', '--child-frame-id', 'odom'],
        parameters=[{'use_sim_time': use_sim_time}],
        condition=IfCondition(PythonExpression(["'", use_slam, "' != 'true' and '", use_nav, "' != 'true'"]))
    )
    nodes_to_launch.append(static_map_to_odom)

    # Interactive Civil Ground Station GUI Node
    gui_node = Node(
        package='assem2_robot',
        executable='civil_interactive_nav',
        name='civil_interactive_nav',
        output='screen',
        parameters=[{'use_sim_time': use_sim_time}],
        condition=IfCondition(use_gui)
    )
    nodes_to_launch.append(gui_node)

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
