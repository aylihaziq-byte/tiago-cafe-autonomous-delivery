#!/usr/bin/env python3
import rospy
import cv2
from cv_bridge import CvBridge, CvBridgeError
from sensor_msgs.msg import Image
from std_msgs.msg import String

class TiagoQrReader:
    def __init__(self):
        self.bridge = CvBridge()
        self.detector = cv2.QRCodeDetector()
        
        # Subscribe to TIAGo's live head camera RGB feed
        self.image_sub = rospy.Subscriber("/xtion/rgb/image_raw", Image, self.image_callback)
        
        # Publish the decoded string to a dedicated ROS topic for full integration
        self.qr_pub = rospy.Publisher("/cafe_detected_qr", String, queue_size=10)
        
        rospy.loginfo("==========================================")
        rospy.loginfo("📸 ROS QR Reader Node Active & Listening...")
        rospy.loginfo("==========================================")

    def image_callback(self, data):
        try:
            # Convert the incoming raw ROS image frame into standard OpenCV BGR format
            cv_image = self.bridge.imgmsg_to_cv2(data, "bgr8")
        except CvBridgeError as e:
            rospy.logerr(f"CvBridge Conversion Error: {e}")
            return

        # Scan the frame for any valid QR array geometries
        decoded_text, points, _ = self.detector.detectAndDecode(cv_image)
        
        # If a QR code is detected and successfully read
        if decoded_text:
            rospy.loginfo(f"🟢 Successfully Scanned: Content = '{decoded_text}'")
            
            # Broadcast the string data across the ROS ecosystem
            self.qr_pub.publish(decoded_text)
            
            # Draw a green bounding box overlay around the code for your Task Demo video
            if points is not None:
                pts = points.astype(int)
                for i in range(len(pts[0])):
                    cv2.line(cv_image, tuple(pts[0][i]), tuple(pts[0][(i+1) % len(pts[0])]), (0, 255, 0), 3)

        # Spawn a live display window showing what TIAGo is seeing
        cv2.imshow("TIAGo Live Head Camera Scanner Feed", cv_image)
        cv2.waitKey(1)

if __name__ == '__main__':
    try:
        rospy.init_node('cafe_qr_reader_node', anonymous=True)
        reader = TiagoQrReader()
        rospy.spin()
    except rospy.ROSInterruptException:
        pass
    finally:
        cv2.destroyAllWindows()
