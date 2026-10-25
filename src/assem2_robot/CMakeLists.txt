cmake_minimum_required(VERSION 3.8)
project(assem2_robot)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

find_package(ament_cmake REQUIRED)

install(
  DIRECTORY config launch maps meshes urdf worlds
  DESTINATION share/${PROJECT_NAME}
)

install(
  PROGRAMS scripts/patrol_mission.py
  DESTINATION lib/${PROJECT_NAME}
  RENAME patrol_mission
)

install(
  PROGRAMS scripts/patrol_mission.py
  DESTINATION lib/${PROJECT_NAME}
)

install(
  PROGRAMS scripts/civil_patrol_mission.py
  DESTINATION lib/${PROJECT_NAME}
  RENAME civil_patrol_mission
)

install(
  PROGRAMS scripts/civil_patrol_mission.py
  DESTINATION lib/${PROJECT_NAME}
)

install(
  PROGRAMS scripts/civil_interactive_nav.py
  DESTINATION lib/${PROJECT_NAME}
  RENAME civil_interactive_nav
)

install(
  PROGRAMS scripts/civil_interactive_nav.py
  DESTINATION lib/${PROJECT_NAME}
)

install(
  PROGRAMS scripts/civil_teleop.py
  DESTINATION lib/${PROJECT_NAME}
  RENAME civil_teleop
)

install(
  PROGRAMS scripts/civil_teleop.py
  DESTINATION lib/${PROJECT_NAME}
)

ament_package()
