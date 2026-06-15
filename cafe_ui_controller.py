#!/usr/bin/env python3
import rospy
import actionlib
import threading
import queue
import tkinter as tk
from tkinter import ttk
from move_base_msgs.msg import MoveBaseAction, MoveBaseGoal
from std_msgs.msg import String

# Safe coordinate registry
CHECKPOINTS = {
    "Table 1":       {"x":  1.147, "y": -1.422, "z":  0.951, "w": -0.309},
    "Counter Zone":  {"x": -3.354, "y":  6.825, "z": -0.717, "w":  0.697},
    "Table 2":       {"x": -0.920, "y": -5.525, "z":  0.001, "w":  1.000}
}

class TiagoCafeUI:
    def __init__(self, window):
        self.window = window
        self.window.title("TIAGo Cafe Autonomous Control Panel")
        self.window.geometry("450x455")
        self.window.configure(bg="#2E3440")
        
        self.gui_queue = queue.Queue()
        self.current_target = None
        
        # ROS Communication Setup
        rospy.loginfo("Connecting to move_base action server...")
        self.client = actionlib.SimpleActionClient('move_base', MoveBaseAction)
        
        # Subscribe to the vision node's decoded output topic
        self.qr_sub = rospy.Subscriber("/cafe_detected_qr", String, self.qr_callback)
        
        # Graphical Layout Elements
        header = tk.Label(window, text="TIAGo CAFE DASHBOARD", font=("Helvetica", 16, "bold"), fg="#88C0D0", bg="#2E3440")
        header.pack(pady=15)
        
        self.status_label = tk.Label(window, text="Status: Ready & Awaiting Goal", font=("Helvetica", 12, "italic"), fg="#A3BE8C", bg="#3B4252", width=38, height=2, relief="groove")
        self.status_label.pack(pady=10)
        
        # Verification Status Frame (Requirement: Vision Verification Update)
        self.verification_label = tk.Label(window, text="QR Verification: No Scan Detected", font=("Helvetica", 11, "bold"), fg="#D8DEE9", bg="#4C566A", width=38, height=2, relief="sunken")
        self.verification_label.pack(pady=5)
        
        btn_frame = tk.LabelFrame(window, text=" Select Destination ", font=("Helvetica", 10, "bold"), fg="#EBCB8B", bg="#2E3440", padx=10, pady=10)
        btn_frame.pack(pady=10, fill="both", expand=True, padx=20)
        
        for name in CHECKPOINTS.keys():
            btn = tk.Button(btn_frame, text=f"Go to {name}", font=("Helvetica", 11, "bold"), bg="#4C566A", fg="#ECEFF4", activebackground="#81A1C1", height=2, command=lambda n=name: self.start_nav_thread(n))
            btn.pack(fill="x", pady=4)
            
        cancel_btn = tk.Button(window, text="EMERGENCY STOP", font=("Helvetica", 11, "bold"), bg="#BF616A", fg="#ECEFF4", activebackground="#D8DEE9", height=2, command=self.cancel_goal)
        cancel_btn.pack(fill="x", pady=15, padx=20)

        self.process_gui_queue()

    def process_gui_queue(self):
        """Processes pending visualization updates directly inside the primary thread loop."""
        try:
            while True:
                msg_type, text, color = self.gui_queue.get_nowait()
                if msg_type == "STATUS":
                    self.status_label.config(text=f"Status: {text}", fg=color)
                elif msg_type == "VERIFY":
                    self.verification_label.config(text=f"QR: {text}", fg=color)
        except queue.Empty:
            pass
        self.window.after(100, self.process_gui_queue)

    def start_nav_thread(self, name):
        self.current_target = name
        self.gui_queue.put(("VERIFY", "Awaiting Location Arrival...", "#EBCB8B"))
        nav_thread = threading.Thread(target=self.send_autonomous_goal, args=(name,))
        nav_thread.daemon = True
        nav_thread.start()

    def send_autonomous_goal(self, name):
        if not self.client.wait_for_server(timeout=rospy.Duration(2.0)):
            self.gui_queue.put(("STATUS", "Error: move_base offline!", "#BF616A"))
            return
            
        self.gui_queue.put(("STATUS", f"Navigating to {name}...", "#81A1C1"))
        
        goal = MoveBaseGoal()
        goal.target_pose.header.frame_id = "map"
        goal.target_pose.header.stamp = rospy.Time.now()
        
        goal.target_pose.pose.position.x = CHECKPOINTS[name]["x"]
        goal.target_pose.pose.position.y = CHECKPOINTS[name]["y"]
        goal.target_pose.pose.orientation.z = CHECKPOINTS[name]["z"]
        goal.target_pose.pose.orientation.w = CHECKPOINTS[name]["w"]
        
        self.client.send_goal(goal, done_cb=self.done_callback)
        
    def done_callback(self, status, result):
        if status == actionlib.GoalStatus.SUCCEEDED:
            self.gui_queue.put(("STATUS", "Goal Reached Successfully!!!", "#A3BE8C"))
            self.gui_queue.put(("VERIFY", f"Scanning for '{self.current_target}' QR Code...", "#88C0D0"))
        elif status == actionlib.GoalStatus.PREEMPTED:
            self.gui_queue.put(("STATUS", "Goal Aborted: E-Stop Used!", "#EBCB8B"))
            self.gui_queue.put(("VERIFY", "Scan Cancelled", "#BF616A"))
        else:
            self.gui_queue.put(("STATUS", "Failed to reach goal. Path blocked!", "#BF616A"))

    def qr_callback(self, msg):
        """Triggers automatically when the camera scans any QR code."""
        scanned_content = msg.data.strip()
        if self.current_target and scanned_content.lower() == self.current_target.lower():
            # Perfect verification match
            self.gui_queue.put(("VERIFY", f"Verified Location: {scanned_content} Match!!!", "#A3BE8C"))
        else:
            # Mismatched barcode exception warning handling
            self.gui_queue.put(("VERIFY", f"Warning: Found '{scanned_content}' (Expected '{self.current_target}')", "#BF616A"))

    def cancel_goal(self):
        self.client.cancel_all_goals()
        self.gui_queue.put(("STATUS", "Stopping Robot...", "#EBCB8B"))

if __name__ == '__main__':
    try:
        rospy.init_node('tiago_cafe_ui_controller', anonymous=True)
        root = tk.Tk()
        app = TiagoCafeUI(root)
        root.mainloop()
    except rospy.ROSInterruptException:
        pass
