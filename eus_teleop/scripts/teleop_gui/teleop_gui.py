#!/usr/bin/env python3
"""
Simple Robot Teleop Launcher GUI - Simplified Version
"""

import os
import sys
import subprocess
import yaml
import signal
from pathlib import Path
from typing import Dict, List

try:
    import tkinter as tk
    from tkinter import ttk, messagebox
    TKINTER_AVAILABLE = True
except ImportError:
    TKINTER_AVAILABLE = False


class TeleopLauncher:
    def __init__(self):
        if not TKINTER_AVAILABLE:
            raise ImportError("tkinter is required for GUI")
        
        self.root = tk.Tk()
        self.root.title("Robot Teleop Launcher")
        self.root.geometry("800x1000")
        
        # Data
        self.base_path = Path(__file__).parent.parent.parent
        self.robots = {}
        self.controllers = ["vive", "oculus", "spacenav", "tablis"]
        
        # Variables
        self.selected_robot = tk.StringVar()
        self.selected_controller = tk.StringVar(value="vive")
        self.head_enable = tk.BooleanVar(value=True)
        self.safe_arm = tk.BooleanVar(value=True)
        self.mirror_mode = tk.BooleanVar(value=False)
        self.visualize = tk.BooleanVar(value=True)
        self.loop_enable = tk.BooleanVar(value=True)
        self.lgripper = tk.StringVar(value="parallel")
        self.rgripper = tk.StringVar(value="parallel")
        
        # Simple process tracking
        self.launched_processes = []
        
        # Setup signal handlers for clean shutdown
        self.setup_signal_handlers()
        
        self.setup_ui()
        self.scan_robots()
        
        # Setup cleanup on window close
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
    def setup_signal_handlers(self):
        """Setup signal handlers to terminate child processes"""
        def signal_handler(sig, frame):
            print(f"Received signal {sig}, cleaning up processes...")
            self.force_cleanup_all()
            sys.exit(0)
        
        # Handle common termination signals
        signal.signal(signal.SIGINT, signal_handler)   # Ctrl+C
        signal.signal(signal.SIGTERM, signal_handler)  # kill command
        
    def force_cleanup_all(self):
        """Force cleanup of all processes without user interaction"""
        active_processes = [p for p in self.launched_processes if p['process'].poll() is None]
        
        # Find orphaned roseus processes
        try:
            result = subprocess.run(['pgrep', '-f', 'roseus.*teleop'], 
                                   capture_output=True, text=True)
            orphaned_pids = []
            if result.returncode == 0:
                for pid_str in result.stdout.split():
                    if pid_str.strip():
                        pid = int(pid_str.strip())
                        is_tracked = any(p['pid'] == pid for p in active_processes)
                        if not is_tracked:
                            orphaned_pids.append(pid)
        except:
            orphaned_pids = []
        
        total_processes = len(active_processes) + len(orphaned_pids)
        if total_processes == 0:
            return
        
        print(f"Force terminating {total_processes} teleop processes...")
        
        # Kill tracked processes
        for p in active_processes:
            try:
                os.killpg(p['pgid'], signal.SIGTERM)
                print(f"Terminated process group {p['pgid']} ({p['robot']} {p['controller']})")
            except:
                try:
                    p['process'].terminate()
                    print(f"Terminated process {p['pid']} ({p['robot']} {p['controller']})")
                except:
                    pass
        
        # Kill orphaned processes
        for pid in orphaned_pids:
            try:
                os.kill(pid, signal.SIGTERM)
                print(f"Terminated orphaned process {pid}")
            except:
                pass
        
        # Wait a moment for processes to terminate
        import time
        time.sleep(1)
        
        # Force kill any remaining processes
        for p in active_processes:
            try:
                if p['process'].poll() is None:
                    os.killpg(p['pgid'], signal.SIGKILL)
            except:
                try:
                    p['process'].kill()
                except:
                    pass
        
        for pid in orphaned_pids:
            try:
                os.kill(pid, signal.SIGKILL)
            except:
                pass
        
        self.launched_processes.clear()
        print("Process cleanup completed.")
        
    def setup_ui(self):
        """Setup GUI layout"""
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(fill="both", expand=True)
        
        # Title
        title_label = ttk.Label(main_frame, text="Robot Teleop Launcher", 
                               font=("TkDefaultFont", 16, "bold"))
        title_label.pack(pady=(0, 20))
        
        # Robot Selection
        robot_frame = ttk.LabelFrame(main_frame, text="1. Select Robot", padding="10")
        robot_frame.pack(fill="x", pady=(0, 15))
        
        self.robot_listbox = tk.Listbox(robot_frame, height=6)
        self.robot_listbox.pack(fill="x")
        self.robot_listbox.bind('<<ListboxSelect>>', self.on_robot_select)
        
        # Robot info
        self.robot_info_label = ttk.Label(robot_frame, text="Select a robot to see details")
        self.robot_info_label.pack(anchor="w", pady=(5, 0))
        
        # Controller Selection  
        controller_frame = ttk.LabelFrame(main_frame, text="2. Select Controller", padding="10")
        controller_frame.pack(fill="x", pady=(0, 15))
        
        self.controller_listbox = tk.Listbox(controller_frame, height=4)
        self.controller_listbox.pack(fill="x")
        self.controller_listbox.bind('<<ListboxSelect>>', self.on_controller_select)
        
        # Arguments Configuration
        args_frame = ttk.LabelFrame(main_frame, text="3. Configure Arguments", padding="10")
        args_frame.pack(fill="x", pady=(0, 15))
        
        # Checkboxes for boolean arguments
        checkbox_frame = ttk.Frame(args_frame)
        checkbox_frame.pack(fill="x", pady=(0, 10))
        
        ttk.Checkbutton(checkbox_frame, text="head", variable=self.head_enable).grid(row=0, column=0, sticky="w")
        ttk.Checkbutton(checkbox_frame, text="safe-arm", variable=self.safe_arm).grid(row=0, column=1, sticky="w", padx=(20, 0))
        ttk.Checkbutton(checkbox_frame, text="mirror", variable=self.mirror_mode).grid(row=1, column=0, sticky="w")
        ttk.Checkbutton(checkbox_frame, text="visualize", variable=self.visualize).grid(row=1, column=1, sticky="w", padx=(20, 0))
        ttk.Checkbutton(checkbox_frame, text="loop-enable", variable=self.loop_enable).grid(row=2, column=0, sticky="w")
        
        # Gripper selection
        gripper_frame = ttk.Frame(args_frame)
        gripper_frame.pack(fill="x", pady=(10, 0))
        
        ttk.Label(gripper_frame, text="lgripper:").grid(row=0, column=0, sticky="w")
        lgripper_combo = ttk.Combobox(gripper_frame, textvariable=self.lgripper, 
                                     values=["parallel", "softhand-v2"], width=12, state="readonly")
        lgripper_combo.grid(row=0, column=1, sticky="w", padx=(5, 20))
        
        ttk.Label(gripper_frame, text="rgripper:").grid(row=0, column=2, sticky="w")
        rgripper_combo = ttk.Combobox(gripper_frame, textvariable=self.rgripper, 
                                     values=["parallel", "softhand-v2"], width=12, state="readonly")
        rgripper_combo.grid(row=0, column=3, sticky="w", padx=5)
        
        # Command preview
        preview_frame = ttk.LabelFrame(main_frame, text="4. Command Preview", padding="10")
        preview_frame.pack(fill="x", pady=(0, 15))
        
        self.command_text = tk.Text(preview_frame, height=4, wrap="word", 
                                   font=("Courier", 9), background="#f0f0f0")
        self.command_text.pack(fill="x")
        
        # Launch button
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill="x")
        
        ttk.Button(button_frame, text="Refresh Robots", 
                  command=self.scan_robots).pack(side="left")
        
        ttk.Button(button_frame, text="Show Active Processes", 
                  command=self.show_active_processes).pack(side="left", padx=(10,0))
        
        self.launch_button = ttk.Button(button_frame, text="🚀 Launch Teleop", 
                                       command=self.launch_teleop, state="disabled")
        self.launch_button.pack(side="right")
        
        # Bind events to update command preview
        for var in [self.selected_robot, self.selected_controller, self.head_enable, 
                   self.safe_arm, self.mirror_mode, self.visualize, self.loop_enable, 
                   self.lgripper, self.rgripper]:
            var.trace("w", self.update_command_preview)
    
    def scan_robots(self):
        """Scan for available robots"""
        self.robots.clear()
        self.robot_listbox.delete(0, tk.END)
        
        # Look for teleop main files
        euslisp_dir = self.base_path / "euslisp"
        if euslisp_dir.exists():
            for teleop_file in euslisp_dir.glob("*-teleop-main.l"):
                robot_name = teleop_file.stem.replace("-teleop-main", "")
                self.robots[robot_name] = {
                    "teleop_file": str(teleop_file),
                    "config": None,
                    "available_controllers": []
                }
        
        # Load robot configs if available
        config_dir = self.base_path / "config"
        if config_dir.exists():
            for config_file in config_dir.glob("*.yaml"):
                if config_file.name == "robot_template.yaml":
                    continue
                try:
                    with open(config_file, 'r') as f:
                        config = yaml.safe_load(f)
                        robot_name = config.get('robot', {}).get('name')
                        if robot_name and robot_name in self.robots:
                            self.robots[robot_name]["config"] = config
                except Exception:
                    pass
        
        # Check for available controllers
        lib_dir = self.base_path / "euslisp" / "lib"
        if lib_dir.exists():
            for robot_name in self.robots:
                available_controllers = []
                for controller in self.controllers:
                    controller_file = lib_dir / f"{robot_name}-{controller}-interface.l"
                    if controller_file.exists():
                        available_controllers.append(controller)
                self.robots[robot_name]["available_controllers"] = available_controllers
        
        # Update robot list
        for robot_name in sorted(self.robots.keys()):
            status = "✓" if self.robots[robot_name]["available_controllers"] else "⚠"
            self.robot_listbox.insert(tk.END, f"{status} {robot_name}")
        
        if self.robots:
            self.robot_listbox.selection_set(0)
            self.on_robot_select()
    
    def on_robot_select(self, event=None):
        """Handle robot selection"""
        selection = self.robot_listbox.curselection()
        if not selection:
            return
        
        # Get selected robot name
        robot_item = self.robot_listbox.get(selection[0])
        robot_name = robot_item.split(" ", 1)[1]  # Remove status symbol
        self.selected_robot.set(robot_name)
        
        if robot_name in self.robots:
            robot_info = self.robots[robot_name]
            
            # Update robot info
            info_text = f"Robot: {robot_name}"
            if robot_info["config"]:
                config = robot_info["config"]
                eus_pkg = config.get('robot', {}).get('eus_package', 'N/A')
                info_text += f" | Package: {eus_pkg}"
                
                # Update options based on config
                features = config.get('features', {})
                self.head_enable.set(features.get('head_control', True))
            
            self.robot_info_label.config(text=info_text)
            
            # Update controller list
            self.update_controller_list(robot_info["available_controllers"])
    
    def update_controller_list(self, available_controllers: List[str]):
        """Update available controllers list"""
        self.controller_listbox.delete(0, tk.END)
        
        controller_names = {
            "vive": "VR Headset (HTC Vive)",
            "oculus": "VR Headset (Oculus)",
            "spacenav": "SpaceNavigator Mouse",
            "tablis": "Tablet Interface"
        }
        
        for controller in available_controllers:
            display_name = controller_names.get(controller, controller)
            self.controller_listbox.insert(tk.END, f"{controller} - {display_name}")
        
        if available_controllers:
            self.controller_listbox.selection_set(0)
            self.selected_controller.set(available_controllers[0])
            self.launch_button.config(state="normal")
        else:
            self.launch_button.config(state="disabled")
            
        self.on_controller_select()
    
    def on_controller_select(self, event=None):
        """Handle controller selection"""
        selection = self.controller_listbox.curselection()
        if selection:
            controller_item = self.controller_listbox.get(selection[0])
            controller_name = controller_item.split(" - ")[0]
            self.selected_controller.set(controller_name)
    
    def update_command_preview(self, *args):
        """Update command preview"""
        robot_name = self.selected_robot.get()
        controller = self.selected_controller.get()
        
        if not robot_name or not controller:
            self.command_text.delete(1.0, tk.END)
            return
        
        # Build command
        if robot_name in self.robots:
            teleop_file = self.robots[robot_name]["teleop_file"]
            
            # Build arguments
            args = []
            args.append(f":device-type :{controller}")
            args.append(f":head {'t' if self.head_enable.get() else 'nil'}")
            args.append(f":safe-arm {'t' if self.safe_arm.get() else 'nil'}")
            args.append(f":mirror {'t' if self.mirror_mode.get() else 'nil'}")
            args.append(f":visualize {'t' if self.visualize.get() else 'nil'}")
            args.append(f":loop-enable {'t' if self.loop_enable.get() else 'nil'}")
            args.append(f":lgripper :{self.lgripper.get()}")
            args.append(f":rgripper :{self.rgripper.get()}")
            
            # Format command
            cmd_text = f"Command:\nroseus {teleop_file}\n\n"
            cmd_text += f"EusLisp:\n(main {' '.join(args)})"
            
            self.command_text.delete(1.0, tk.END)
            self.command_text.insert(1.0, cmd_text)
    
    def launch_teleop(self):
        """Launch the selected teleop"""
        robot_name = self.selected_robot.get()
        controller = self.selected_controller.get()
        
        if not robot_name or not controller:
            messagebox.showwarning("Warning", "Please select robot and controller!")
            return
        
        if robot_name not in self.robots:
            messagebox.showerror("Error", f"Robot {robot_name} not found!")
            return
        
        try:
            teleop_file = self.robots[robot_name]["teleop_file"]
            
            # Build EusLisp command
            args = []
            args.append(f":device-type :{controller}")
            args.append(f":head {'t' if self.head_enable.get() else 'nil'}")
            args.append(f":safe-arm {'t' if self.safe_arm.get() else 'nil'}")
            args.append(f":mirror {'t' if self.mirror_mode.get() else 'nil'}")
            args.append(f":visualize {'t' if self.visualize.get() else 'nil'}")
            args.append(f":loop-enable {'t' if self.loop_enable.get() else 'nil'}")
            args.append(f":lgripper :{self.lgripper.get()}")
            args.append(f":rgripper :{self.rgripper.get()}")
            
            lisp_command = f"(main {' '.join(args)})"
            
            # Show confirmation
            msg = f"Launch teleop for {robot_name} with {controller}?\n\n"
            msg += f"Command: {lisp_command}"
            
            if messagebox.askyesno("Confirm Launch", msg):
                # Simple terminal launch with process group
                terminal_cmd = [
                    "gnome-terminal", "--", "bash", "-c",
                    f"roseus {teleop_file} -c '{lisp_command}'"
                ]
                
                # Launch with new process group for easy cleanup
                process = subprocess.Popen(terminal_cmd, preexec_fn=os.setsid)
                
                # Track the process
                proc_info = {
                    'process': process,
                    'robot': robot_name,
                    'controller': controller,
                    'pid': process.pid,
                    'pgid': process.pid  # Process group ID
                }
                
                self.launched_processes.append(proc_info)
                
                messagebox.showinfo("Launched", f"Teleop launched for {robot_name}!\nPID: {process.pid}")
        
        except Exception as e:
            messagebox.showerror("Launch Error", f"Failed to launch teleop: {e}")
    
    def show_active_processes(self):
        """Show active processes and allow manual termination"""
        # Clean up finished processes first
        active_processes = [p for p in self.launched_processes if p['process'].poll() is None]
        self.launched_processes = active_processes
        
        # Find any roseus processes
        try:
            result = subprocess.run(['pgrep', '-f', 'roseus.*teleop'], 
                                   capture_output=True, text=True)
            orphaned_pids = []
            if result.returncode == 0:
                for pid_str in result.stdout.split():
                    if pid_str.strip():
                        pid = int(pid_str.strip())
                        # Check if already tracked
                        is_tracked = any(p['pid'] == pid for p in active_processes)
                        if not is_tracked:
                            orphaned_pids.append(pid)
        except:
            orphaned_pids = []
        
        total_processes = len(active_processes) + len(orphaned_pids)
        
        if total_processes == 0:
            messagebox.showinfo("Active Processes", "No active teleop processes found.")
            return
        
        # Simple message with process info
        msg = f"Active processes ({total_processes} total):\n\n"
        
        for p in active_processes:
            msg += f"[Tracked] {p['robot']} ({p['controller']}) - PID {p['pid']}\n"
        
        for pid in orphaned_pids:
            msg += f"[Orphaned] roseus process - PID {pid}\n"
        
        msg += f"\nDo you want to terminate all processes?"
        
        if messagebox.askyesno("Active Processes", msg):
            terminated = 0
            
            # Kill tracked processes
            for p in active_processes:
                try:
                    os.killpg(p['pgid'], signal.SIGTERM)  # Kill process group
                    terminated += 1
                except:
                    try:
                        p['process'].terminate()
                        terminated += 1
                    except:
                        pass
            
            # Kill orphaned processes
            for pid in orphaned_pids:
                try:
                    os.kill(pid, signal.SIGTERM)
                    terminated += 1
                except:
                    pass
            
            messagebox.showinfo("Success", f"Terminated {terminated} processes")
            self.launched_processes.clear()
    
    def cleanup_processes(self):
        """Clean up all launched processes"""
        active_processes = [p for p in self.launched_processes if p['process'].poll() is None]
        
        if not active_processes:
            return
        
        # Ask user for confirmation
        msg = f"There are {len(active_processes)} active teleop processes. Terminate them?"
        
        if messagebox.askyesno("Active Processes", msg):
            for p in active_processes:
                try:
                    os.killpg(p['pgid'], signal.SIGTERM)  # Kill process group
                except:
                    try:
                        p['process'].terminate()
                    except:
                        pass
        
        self.launched_processes.clear()
    
    def on_closing(self):
        """Handle window close event"""
        try:
            self.cleanup_processes()
        except Exception as e:
            print(f"Error during cleanup: {e}")
        finally:
            self.root.destroy()
    
    def run(self):
        """Start the GUI"""
        self.root.mainloop()


def main():
    if not TKINTER_AVAILABLE:
        print("Error: tkinter not available. Install with: sudo apt-get install python3-tk")
        return 1
    
    try:
        app = TeleopLauncher()
        app.run()
        return 0
    except Exception as e:
        print(f"Error: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())
