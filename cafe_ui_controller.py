#!/usr/bin/env python3
import rospy
import actionlib
import threading
import queue
import tkinter as tk
from tkinter import ttk
from move_base_msgs.msg import MoveBaseAction, MoveBaseGoal
from std_msgs.msg import String

# Target Coordinate Dictionary
CHECKPOINTS = {
    "Rest Point":    {"x":  0.164, "y":  6.586, "z": -0.687, "w":  0.727},
    "Counter Zone 1":{"x": -2.667, "y":  6.365, "z":  0.742, "w":  0.670}, 
    "Counter Zone 2":{"x": -4.051, "y":  6.336, "z":  0.727, "w":  0.686}, 
    "Table 1":       {"x":  1.147, "y": -1.422, "z":  0.951, "w": -0.309},
    "Table 2":       {"x": -0.920, "y": -5.525, "z":  0.001, "w":  1.000}
}

class TiagoCafeUI:
    def __init__(self, window):
        self.window = window
        self.window.title("TIAGo Cafe Autonomous Control Panel")
        self.window.geometry("450x620")
        self.window.configure(bg="#2E3440")
        
        self.gui_queue = queue.Queue()
        self.is_navigating = False
        self.last_executed_command = None
        self.current_location = "Rest Point" 
        self.active_goal_name = None
        
        rospy.loginfo("Connecting to move_base action server...")
        self.client = actionlib.SimpleActionClient('move_base', MoveBaseAction)
        
        self.qr_sub = rospy.Subscriber("/cafe_detected_qr", String, self.qr_instruction_callback)
        
        header = tk.Label(window, text="TIAGo CAFE DASHBOARD", font=("Helvetica", 16, "bold"), fg="#88C0D0", bg="#2E3440")
        header.pack(pady=10)
        
        self.status_label = tk.Label(window, text="Status: Idling at Rest Point", font=("Helvetica", 12, "italic"), fg="#A3BE8C", bg="#3B4252", width=38, height=2, relief="groove")
        self.status_label.pack(pady=5)
        
        self.verification_label = tk.Label(window, text="System Ready.", font=("Helvetica", 11, "bold"), fg="#D8DEE9", bg="#4C566A", width=38, height=2, relief="sunken")
        self.verification_label.pack(pady=5)

        # === THE STEP-BY-STEP FLOW BUTTONS ===
        self.counter1_btn = tk.Button(window, text="Send to Counter 1 (Table 1)", font=("Helvetica", 11, "bold"), bg="#5E81AC", fg="#ECEFF4", height=2, command=lambda: self.start_nav_thread("Counter Zone 1"))
        self.counter1_btn.pack(fill="x", pady=5, padx=20)

        self.counter2_btn = tk.Button(window, text="Send to Counter 2 (Table 2)", font=("Helvetica", 11, "bold"), bg="#5E81AC", fg="#ECEFF4", height=2, command=lambda: self.start_nav_thread("Counter Zone 2"))
        self.counter2_btn.pack(fill="x", pady=5, padx=20)

        self.return_btn = tk.Button(window, text="Return to Rest Point", font=("Helvetica", 12, "bold"), bg="#A3BE8C", fg="#2E3440", height=2, state="disabled", command=lambda: self.start_nav_thread("Rest Point"))
        self.return_btn.pack(fill="x", pady=10, padx=20)
        
        # Manual Overrides Frame
        btn_frame = tk.LabelFrame(window, text=" Manual Overrides ", font=("Helvetica", 10, "bold"), fg="#EBCB8B", bg="#2E3440", padx=10, pady=5)
        btn_frame.pack(pady=5, fill="both", expand=True, padx=20)
        
        for name in CHECKPOINTS.keys():
            btn = tk.Button(btn_frame, text=f"Force {name}", font=("Helvetica", 9, "bold"), bg="#4C566A", fg="#ECEFF4", height=1, command=lambda n=name: self.start_nav_thread(n))
            btn.pack(fill="x", pady=1)
            
        cancel_btn = tk.Button(window, text="EMERGENCY STOP", font=("Helvetica", 11, "bold"), bg="#BF616A", fg="#ECEFF4", height=1, command=self.cancel_goal)
        cancel_btn.pack(fill="x", pady=10, padx=20)

        self.process_gui_queue()

    def process_gui_queue(self):
        try:
            while True:
                msg = self.gui_queue.get_nowait()
                msg_type = msg[0]
                
                if msg_type == "STATUS":
                    self.status_label.config(text=f"Status: {msg[1]}", fg=msg[2])
                elif msg_type == "VERIFY":
                    self.verification_label.config(text=f"{msg[1]}", fg=msg[2])
                elif msg_type == "BUTTON_STATES":
                    self.counter1_btn.config(state=msg[1])
                    self.counter2_btn.config(state=msg[2])
                    self.return_btn.config(state=msg[3])
        except queue.Empty:
            pass
        self.window.after(100, self.process_gui_queue)

    def qr_instruction_callback(self, msg):
        instruction = msg.data.strip()
        
        if self.is_navigating:
            return
            
        if "Counter Zone" not in self.current_location:
            self.gui_queue.put(("VERIFY", "Ignored QR: Robot not at Counter Stations!", "#EBCB8B"))
            return
            
        if instruction not in CHECKPOINTS:
            self.gui_queue.put(("VERIFY", f"Ignored Unknown Instruction: {instruction}", "#BF616A"))
            return
            
        if instruction == self.last_executed_command:
            return
            
        self.last_executed_command = instruction
        self.gui_queue.put(("VERIFY", f"QR Match: {instruction} Verified!", "#A3BE8C"))
        
        self.start_nav_thread(instruction)

    def start_nav_thread(self, name):
        self.is_navigating = True
        self.active_goal_name = name
        self.gui_queue.put(("BUTTON_STATES", "disabled", "disabled", "disabled"))
        
        nav_thread = threading.Thread(target=self.send_autonomous_goal, args=(name,))
        nav_thread.daemon = True
        nav_thread.start()

    def send_autonomous_goal(self, name):
        name = str(name).strip()
        self.active_goal_name = name
        
        if name not in CHECKPOINTS:
            rospy.logerr(f" CRITICAL: '{name}' is missing from UI Key Dictionary!")
            self.gui_queue.put(("STATUS", f"Error: Key '{name}' not found", "#BF616A"))
            self.is_navigating = False
            return

        if not self.client.wait_for_server(timeout=rospy.Duration(5.0)):
            self.gui_queue.put(("STATUS", "Error: move_base offline!", "#BF616A"))
            self.is_navigating = False
            return
            
        self.gui_queue.put(("STATUS", f"Driving to {name}...", "#81A1C1"))
        
        goal = MoveBaseGoal()
        goal.target_pose.header.frame_id = "map"
        goal.target_pose.header.stamp = rospy.Time(0)
        
        goal.target_pose.pose.position.x = CHECKPOINTS[name]["x"]
        goal.target_pose.pose.position.y = CHECKPOINTS[name]["y"]
        goal.target_pose.pose.orientation.z = CHECKPOINTS[name]["z"]
        goal.target_pose.pose.orientation.w = CHECKPOINTS[name]["w"]
        
        rospy.loginfo(f"🚀 Sending clean stamped goal to move_base for target: {name}")
        self.client.send_goal(goal, done_cb=self.done_callback)
        
    def done_callback(self, status, result):
        self.is_navigating = False
        if status == actionlib.GoalStatus.SUCCEEDED:
            self.current_location = self.active_goal_name
            self.gui_queue.put(("STATUS", f"Arrived at {self.current_location}!", "#A3BE8C"))
            
            if "Counter Zone" in self.current_location:
                self.gui_queue.put(("BUTTON_STATES", "disabled", "disabled", "disabled"))
                self.gui_queue.put(("VERIFY", "Standing at station. Awaiting QR code input...", "#88C0D0"))
                
            elif self.current_location in ["Table 1", "Table 2"]:
                self.gui_queue.put(("BUTTON_STATES", "disabled", "disabled", "normal"))
                self.gui_queue.put(("VERIFY", "Food Delivered. Click button to return to base.", "#EBCB8B"))
                
            elif self.current_location == "Rest Point":
                self.gui_queue.put(("BUTTON_STATES", "normal", "normal", "disabled"))
                self.gui_queue.put(("VERIFY", "Idling at Rest Point. Ready for next order.", "#D8DEE9"))
                self.last_executed_command = None 
        else:
            self.gui_queue.put(("STATUS", "Navigation failed or stopped.", "#BF616A"))
            self.gui_queue.put(("BUTTON_STATES", "normal", "normal", "normal"))

    def cancel_goal(self):
        self.client.cancel_all_goals()
        self.is_navigating = False
        self.last_executed_command = None
        self.gui_queue.put(("STATUS", "E-Stop Activated.", "#EBCB8B"))
        self.gui_queue.put(("BUTTON_STATES", "normal", "normal", "normal"))

if __name__ == '__main__':
    try:
        rospy.init_node('tiago_cafe_ui_controller', anonymous=True)
        root = tk.Tk()
        app = TiagoCafeUI(root)
        root.mainloop()
    except rospy.ROSInterruptException:
        pass
