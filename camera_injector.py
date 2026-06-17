#!/usr/bin/env python3
import rospy
import cv2
import os
from sensor_msgs.msg import Image
from geometry_msgs.msg import PoseWithCovarianceStamped
from cv_bridge import CvBridge
import math

class CameraInjectNode:
    def __init__(self):
        rospy.init_node('camera_injector_node', anonymous=True)
        self.bridge = CvBridge()
        
        # Publish directly onto TIAGo's silent raw camera feed topic
        self.image_pub = rospy.Publisher('/xtion/rgb/image_raw', Image, queue_size=10)
        self.pose_sub = rospy.Subscriber('/amcl_pose', PoseWithCovarianceStamped, self.pose_callback)
        
        # Define target locations and the local paths to their respective QR image assets
        self.base_path = os.path.expanduser('~/tiago_public_ws/src/')
        self.zones = [
            {"name": "Counter_T1", "x": -2.667, "y": 6.365, "img": "table_1.png"},
            {"name": "Counter_T2", "x": -4.051, "y": 6.336, "img": "table_2.png"},
        ]
        
        self.current_x = 0.0
        self.current_y = 0.0
        rospy.loginfo("🛰️ Camera Injector Engine Online. Monitoring location arrays...")

    def pose_callback(self, msg):
        self.current_x = msg.pose.pose.position.x
        self.current_y = msg.pose.pose.position.y

    def broadcast_stream(self):
        rate = rospy.Rate(5) # Publish at 5 Hz to keep things lightweight
        while not rospy.is_shutdown():
            active_image_file = None
            
            # Check if TIAGo is standing directly in front of any QR targets
            for zone in self.zones:
                dist = math.sqrt((self.current_x - zone["x"])**2 + (self.current_y - zone["y"])**2)
                if dist < 0.65: # Within scanning distance
                    active_image_file = zone["img"]
                    break
            
            # If a match is found, load the real physical PNG and pump it into the ROS network
            if active_image_file:
                full_path = os.path.join(self.base_path, active_image_file)
                if os.path.exists(full_path):
                    cv_img = cv2.imread(full_path)
                    # Resize slightly to mimic a standard camera aspect frame
                    cv_img = cv2.resize(cv_img, (640, 480))
                    try:
                        ros_img = self.bridge.cv2_to_imgmsg(cv_img, "bgr8")
                        self.image_pub.publish(ros_img)
                    except Exception as e:
                        pass
            rate.sleep()

if __name__ == '__main__':
    try:
        injector = CameraInjectNode()
        injector.broadcast_stream()
    except rospy.ROSInterruptException:
        pass
