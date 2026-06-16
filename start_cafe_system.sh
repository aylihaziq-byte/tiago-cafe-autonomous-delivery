#!/bin/bash

# Fix for VirtualBox Gazebo camera rendering freeze bug
export SVGA_VGPU10=0
export LIBGL_ALWAYS_SOFTWARE=0
# 1. Clean up any stale or crashed background processes cleanly
echo "=========================================="
echo "🧹 1/5: Clearing out old simulation caches..."
echo "=========================================="
killall -9 roscore rosmaster gazebo gzserver gzclient rviz python3 2>/dev/null
sleep 2

# 2. Launch the TIAGo Café Simulation package
echo "=========================================="
echo "🚀 2/5: Launching TIAGo Café Navigation Simulation..."
echo "=========================================="
source ~/tiago_public_ws/devel/setup.bash
roslaunch tiago_2dnav_gazebo tiago_navigation.launch public_sim:=true world:=worldcafe arm:=false end_effector:=false map:=$HOME/.pal/tiago_maps/configurations/cafe_perfect lost:=true gzpose:="-x 0.164 -y 6.586 -z 0.1 -R 0.0 -P 0.0 -Y -1.513" &

# 3. Wait for the simulation and RViz graphic window to fully load
echo "=========================================="
echo "⏳ 3/5: Waiting 35s for AMCL localization to initialize..."
echo "=========================================="
sleep 35

# 4. Programmatically seed the initial coordinate frames
echo "=========================================="
echo "🟢 4/5: Syncing laser scans & Spawning 3D QR Array..."
echo "=========================================="
source /opt/ros/noetic/setup.bash
rostopic pub -1 /initialpose geometry_msgs/PoseWithCovarianceStamped "{header: {frame_id: 'map'}, pose: {pose: {position: {x: 0.164, y: 6.586, z: 0.0}, orientation: {x: 0.0, y: 0.0, z: -0.687, w: 0.727}}, covariance: [0.05, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.05, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.01]}}"
sleep 2

# === SPAWNING THE MULTI-POINT QR CODE ARRAY (FINALIZED COORDINATES) ===

# 1. QR Table 1 placed at the Counter Zone
rosrun gazebo_ros spawn_model -file ~/.gazebo/models/qr_table_1/model.sdf -sdf -model qr_table_1_counter -x -2.906 -y 7.329 -z 1.523 -R 0.0 -P 0.0 -Y 1.628 &
sleep 0.5

# 2. QR Table 2 placed at the Counter Zone
rosrun gazebo_ros spawn_model -file ~/.gazebo/models/qr_table_2/model.sdf -sdf -model qr_table_2_counter -x -2.409 -y 7.335 -z 1.523 -R 0.0 -P 0.0 -Y 1.628 &
sleep 0.5

# 3. QR Counter Zone placed at Table 1
rosrun gazebo_ros spawn_model -file ~/.gazebo/models/qr_counter_zone/model.sdf -sdf -model qr_counter_at_t1 -x 0.956 -y -1.422 -z 1.073 -R 0.0 -P 0.0 -Y 0.0 &
sleep 0.5

# 4. QR Counter Zone placed at Table 2
rosrun gazebo_ros spawn_model -file ~/.gazebo/models/qr_counter_zone/model.sdf -sdf -model qr_counter_at_t2 -x -1.042 -y -5.525 -z 1.069 -R 0.0 -P 0.0 -Y 0.0 &
sleep 1.0

# Streams a continuous 10Hz heartbeat message to execute the localization sweep
echo "🔄 Executing intensive 1080-degree sensor convergence spin..."
timeout 10 rostopic pub -r 10 /mobile_base_controller/cmd_vel geometry_msgs/Twist "{linear: {x: 0.0, y: 0.0, z: 0.0}, angular: {x: 0.0, y: 0.0, z: 2.0}}" > /dev/null &
sleep 10.5

# Flush out residual obstacle arrays for a completely clean path environment
rosservice call /move_base/clear_costmaps "{}"
sleep 1

# Launch the live head camera vision node automatically in the background
echo "=========================================="
echo "📸 4.5/5: Initiating Vision Tracking Stack..."
echo "=========================================="
python3 ~/tiago_public_ws/src/cafe_qr_reader.py &
sleep 1

# 5. Bring up your custom Python Tkinter Dashboard
echo "=========================================="
echo "💻 5/5: Launching Custom Control Panel UI..."
echo "=========================================="
python3 ~/tiago_public_ws/src/cafe_ui_controller.py
