#!/usr/bin/env python3

from os.path import join
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import ExecuteProcess, IncludeLaunchDescription, RegisterEventHandler, DeclareLaunchArgument
from launch.event_handlers import OnProcessExit
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node
from launch.substitutions import LaunchConfiguration
import xacro

def generate_launch_description():
    # Include the Gazebo launch file
    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(join(get_package_share_directory("gazebo_ros"), "launch", "gazebo.launch.py"))
    )

    use_sim_time = LaunchConfiguration('use_sim_time', default='true')

    xacro_file = join(get_package_share_directory('open_manipulator_gazebo'),
                              'urdf',
                              'open_manipulator_x.urdf.xacro')
    
    rviz_config = join(get_package_share_directory("open_manipulator_x_description"),
                               "rviz",
                               "open_manipulator_x.rviz")

    doc = xacro.parse(open(xacro_file))
    xacro.process_doc(doc)

    robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        output='screen',
        parameters=[{'robot_description': doc.toxml(),
              'use_sim_time': use_sim_time}]
    )

    rviz = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        arguments=['-d', rviz_config],
        output='screen'
    )

    spawn_entity = Node(package='gazebo_ros', executable='spawn_entity.py',
                        arguments=['-topic', 'robot_description',
                                   '-entity', 'omx'],
                        output='screen'
    )

    load_joint_state_controller = ExecuteProcess(
        cmd=['ros2', 'control', 'load_controller', '--set-state', 'start',
             'joint_state_broadcaster'],
        output='screen'
    )

    load_joint_trajectory_controller = ExecuteProcess(
        cmd=['ros2', 'control', 'load_controller', '--set-state', 'start',
             'joint_trajectory_controller'],
        output='screen'
    )

    return LaunchDescription([
        RegisterEventHandler(
            event_handler=OnProcessExit(
                target_action=spawn_entity,
                on_exit=[load_joint_state_controller],
            )
        ),
        RegisterEventHandler(
            event_handler=OnProcessExit(
                target_action=load_joint_state_controller,
                on_exit=[load_joint_trajectory_controller],
            )
        ),
        RegisterEventHandler(
            event_handler=OnProcessExit(
                target_action=load_joint_trajectory_controller,
                on_exit=[rviz],
            )
        ),
        DeclareLaunchArgument('use_sim_time', default_value = use_sim_time),
        gazebo,
        robot_state_publisher,
        spawn_entity,
    ])