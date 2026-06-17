#!/usr/bin/env python3
import rospy
import cv2
<<<<<<< HEAD
import threading  # FIXED: Added missing import to prevent thread-lock crashes!
=======
>>>>>>> abbe373eb140528e3e3930a3de2e5e91690dd96e
from sensor_msgs.msg import Image
from std_msgs.msg import String
from cv_bridge import CvBridge, CvBridgeError
from pyzbar import pyzbar

<<<<<<< HEAD
class CafeRealVisionScanner:
=======
class CafeQRScanner:
>>>>>>> abbe373eb140528e3e3930a3de2e5e91690dd96e
    def __init__(self):
        rospy.init_node('cafe_qr_reader_node', anonymous=True)
        self.bridge = CvBridge()
        
<<<<<<< HEAD
        # Publish directly to your Tkinter UI
        self.qr_pub = rospy.Publisher('/cafe_detected_qr', String, queue_size=10)
        
        # Listen directly to your raw camera pipeline
        self.image_sub = rospy.Subscriber('/xtion/rgb/image_raw', Image, self.image_callback)
        rospy.loginfo("📸 Real Camera Vision Node Initialized. Scanning active pixel arrays...")

    def image_callback(self, data):
        if not hasattr(self, 'is_processing'):
            self.is_processing = False
            
        if self.is_processing:
            return # Ignore incoming frames while processing to prevent UI network flood

        try:
            cv_image = self.bridge.imgmsg_to_cv2(data, "bgr8")
        except CvBridgeError as e:
            rospy.logerr(f"CvBridge Error: {e}")
            return

        barcodes = pyzbar.decode(cv_image)
        for barcode in barcodes:
            qr_data = barcode.data.decode("utf-8")
            rospy.loginfo(f"🏁 REAL QR SCOUTED: {qr_data}")
            
            # Engage the gatekeeper lock immediately
            self.is_processing = True
            self.qr_pub.publish(qr_data)
            
            # Highlight barcode frame on visual monitor window
            (x, y, w, h) = barcode.rect
            cv2.rectangle(cv_image, (x, y), (x + w, y + h), (0, 255, 0), 3)
            
            # Reset the scan gate after 4 seconds to safely allow future orders
            threading.Timer(4.0, self.release_scanner_lock).start()
            break 

        cv2.imshow("QR Scanner", cv_image)
        cv2.waitKey(1)

    def release_scanner_lock(self):
        """Resets scanner lock so the robot can perform subsequent scans later."""
        self.is_processing = False

if __name__ == '__main__':
    try:
        scanner = CafeRealVisionScanner()
        rospy.spin()
    except rospy.ROSInterruptException:
        pass
=======
        # Publisher to notify your Tkinter UI system when a code is spotted
        self.qr_pub = rospy.Publisher('/cafe_detected_qr', String, queue_size=10)
        
        # Subscribing to TIAGo's direct raw camera channel
        self.image_sub = rospy.Subscriber('/xtion/rgb/image_raw', Image, self.image_callback)
        rospy.loginfo("📸 QR Scanner Frame Initialized. Awaiting camera packets...")

    def image_callback(self, data):
        try:
            # Convert the raw ROS Image message into a standard OpenCV BGR frame
            cv_image = self.bridge.imgmsg_to_cv2(data, "bgr8")
        except CvBridgeError as e:
            rospy.logerr(f"CvBridge Conversion Error: {e}")
            return

        # Scan the frame matrix for any physical QR codes
        barcodes = pyzbar.decode(cv_image)
        for barcode in barcodes:
            qr_data = barcode.data.decode("utf-8")
            rospy.loginfo(f"🏁 QR Detected: {qr_data}")
            
            # Broadcast the string value to your state machine dashboard
            self.qr_pub.publish(qr_data)
            
            # Draw a green bounding frame rectangle over the target code on screen
            (x, y, w, h) = barcode.rect
            cv2.rectangle(cv_image, (x, y), (x + w, y + h), (0, 255, 0), 3)
            cv2.putText(cv_image, qr_data, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

        # 📺 MATCHING YOUR FRIEND'S SETUP (From image.png):
        # This creates a native, floating graphical window displaying the camera stream
        cv2.imshow("QR Scanner", cv_image)
        
        # Keeps the window stream refreshing smoothly at 1ms intervals
        cv2.waitKey(1)

if __name__ == '__main__':
    try:
        scanner = CafeQRScanner()
        rospy.spin()
    except rospy.ROSInterruptException:
        rospy.loginfo("Shutting down camera tracking nodes.")
>>>>>>> abbe373eb140528e3e3930a3de2e5e91690dd96e
    finally:
        cv2.destroyAllWindows()
