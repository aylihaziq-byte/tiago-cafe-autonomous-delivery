#!/usr/bin/env python3
import rospy
import cv2
import threading  # FIXED: Added missing import to prevent thread-lock crashes!
from sensor_msgs.msg import Image
from std_msgs.msg import String
from cv_bridge import CvBridge, CvBridgeError
from pyzbar import pyzbar

class CafeRealVisionScanner:
    def __init__(self):
        rospy.init_node('cafe_qr_reader_node', anonymous=True)
        self.bridge = CvBridge()
        
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
    finally:
        cv2.destroyAllWindows()
