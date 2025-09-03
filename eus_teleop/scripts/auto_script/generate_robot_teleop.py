#!/usr/bin/env python3
"""
Script to generate robot-specific teleop and controller interface files from YAML configuration.
"""

import os
import sys
import yaml
import argparse
from typing import Dict, Any, Optional

class RobotTeleopGenerator:
    def __init__(self, config_path: str):
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        
        self.robot_name = self.config['robot']['name']
        self.robot_name_upper = self.robot_name.upper()
        self.robot_name_title = self.robot_name.title()

    def generate_teleop_interface(self) -> str:
        """Generate robot-specific teleop interface file content."""
        
        robot_config = self.config['robot']
        topics = self.config['topics']
        features = self.config['features']
        hardware = self.config['hardware']
        control = self.config['control']
        
        template = f";; -*- mode: lisp;-*-\n"
        
        # ROS manifest loading
        if robot_config.get('core_msgs_package'):
            template += f'(ros::load-ros-manifest "{robot_config["core_msgs_package"]}")\n'
        template += "\n"
        
        # Require statements
        template += f'(require :{self.robot_name}-interface "package://eus_teleop/euslisp/lib/{self.robot_name}-interface.l")\n'
        template += '(require :robot-teleop-interface "package://eus_teleop/euslisp/lib/robot-teleop-interface.l")\n\n'

        # Method renaming section
        template += f"""
;; Method renaming for {self.robot_name}-specific overrides
(if (not (assoc :init-{self.robot_name}-org (send robot-teleop-interface :methods)))
  (rplaca (assoc :init (send robot-teleop-interface :methods)) :init-{self.robot_name}-org))
(if (not (assoc :reset-{self.robot_name}-org (send robot-teleop-interface :methods)))
  (rplaca (assoc :reset (send robot-teleop-interface :methods)) :reset-{self.robot_name}-org))
(if (not (assoc :reset-arm-{self.robot_name}-org (send robot-teleop-interface :methods)))
  (rplaca (assoc :reset-arm (send robot-teleop-interface :methods)) :reset-arm-{self.robot_name}-org))
(if (not (assoc :disable-{self.robot_name}-org (send robot-teleop-interface :methods)))
  (rplaca (assoc :disable (send robot-teleop-interface :methods)) :disable-{self.robot_name}-org))
(if (not (assoc :enable-{self.robot_name}-org (send robot-teleop-interface :methods)))
  (rplaca (assoc :enable (send robot-teleop-interface :methods)) :enable-{self.robot_name}-org))
(if (not (assoc :arm-motion-cb-{self.robot_name}-org (send robot-teleop-interface :methods)))
  (rplaca (assoc :arm-motion-cb (send robot-teleop-interface :methods)) :arm-motion-cb-{self.robot_name}-org))


(defmethod robot-teleop-interface
  (:init (&rest args)
    (prog1
      (send* self :init-{self.robot_name}-org args)
      (send self :set-val 'robot *{self.robot_name}*)
      (send self :set-val 'robot-interface *ri*)
      (send self :set-val 'camera-model *camera-model*)
      (send self :set-val 'rate {control['rate']})
      (send self :set-val 'end-coords-pos-diff-thresh {control['safety']['end_coords_pos_diff_thresh']})
      (send self :set-val 'draw-object-list (list *{self.robot_name}* *background-cube*))
      
      ;; {self.robot_name_title} frame configuration
      (send self :set-val 'base-frame-id "{topics['frames']['base']}")"""

        if features.get('head_control', False):
            template += f"""
      (send self :set-val 'head-frame-id "{topics['frames']['head']}")"""

        template += f"""
      
      ;; {self.robot_name_title} inverse kinematics configuration
      (send self :set-val 'arm-cb-solve-ik {'t' if control['ik']['solve_ik'] else 'nil'})
      (send self :set-val 'ik-stop-step {control['ik']['stop_step']})
      (send self :set-val 'av-tm {control['motion']['av_tm']})
      (send self :set-val 'av-scale {control['motion']['av_scale']})
      (send self :set-val 'min-time {control['motion']['min_time']})"""

        if features.get('gripper_control', False) and topics['gripper_status']['larm']:
            template += f"""
      
      ;; {self.robot_name_title} gripper configuration
      (send self :set-val 'grasp-timeout-time {control['safety']['grasp_timeout_time']})
      
      ;; Gripper status topics
      (send self :set-arm-val :larm :gripper-status-topic-name
            "{topics['gripper_status']['larm']}")
      (send self :set-arm-val :rarm :gripper-status-topic-name
            "{topics['gripper_status']['rarm']}")"""

        if features.get('collision_detection', False) and topics['collision_status']['larm']:
            template += f"""
      
      ;; Collision detection topics
      (send self :set-arm-val :larm :collision-status-topic-name
            "{topics['collision_status']['larm']}")
      (send self :set-arm-val :rarm :collision-status-topic-name
            "{topics['collision_status']['rarm']}")"""
            
            if robot_config.get('core_msgs_package'):
                template += f"""
      (send self :set-val 'collision-status-topic-type {robot_config['core_msgs_package']}::CollisionDetectionState)"""

        # Hardware configuration
        template += f"""
      
      ;; {self.robot_name_title} hardware configuration
      (send self :set-val 'arm-length {hardware['arm_length']})
      (send self :set-val 'head->shoulder-x-distance {hardware['head_to_shoulder']['x_distance']})
      (send self :set-val 'head->shoulder-z-distance {hardware['head_to_shoulder']['z_distance']})"""

        # Torso configuration if enabled
        if features.get('torso_control', False):
            torso_config = control.get('torso', {})
            template += f"""
      
      ;; Torso control configuration
      (send self :set-val 'torso-av-tm {torso_config.get('av_tm', 1000)})
      (send self :set-val 'torso-av-scale {torso_config.get('av_scale', 2.0)})
      (send self :set-val 'torso-min-time {torso_config.get('min_time', 0.5)})
      (send self :set-val 'torso-z-thresh {torso_config.get('z_thresh', 200)})
      (send self :set-val 'torso-ik-weight {torso_config.get('ik_weight', 0.5)})"""

        template += "))"

        # Reset methods
        torso_enable = 't' if features.get('torso_control', False) else 'nil'
        template += f"""
  (:reset (&key (loop-enable t))
    (send self :reset-{self.robot_name}-org :loop-enable loop-enable :torso {torso_enable}))
  (:reset-arm (arm &key (wait t))
    (send self :reset-arm-{self.robot_name}-org arm :wait wait :reset-pose :reset-teleop-pose))
  (:enable () (send self :enable-{self.robot_name}-org :torso {torso_enable}))
  (:disable () (send self :disable-{self.robot_name}-org :torso {torso_enable}))"""

        # Head control methods
        if features.get('head_control', False):
            template += f"""
  (:move-head (yaw pitch roll)
    (send robot :head-neck-p :joint-angle (rad2deg pitch))
    (send robot :head-neck-y :joint-angle (rad2deg yaw))
    (send self :angle-vector (send robot :angle-vector) av-tm
          :head-controller 0 :min-time min-time :scale av-scale))
  (:get-head-end-coords ()
    (let (coords)
      (send tfl :wait-for-transform base-frame-id head-frame-id (ros::time 0) 0.1)
      (setq coords (send tfl :lookup-transform base-frame-id head-frame-id (ros::time 0)))
      (if coords (send coords :rotate pi/2 :y :world))
      coords))"""

        # Basic motion methods
        template += f"""
  (:angle-vector (&rest args)
    (send* robot-interface :angle-vector-raw args))
  (:inverse-kinematics (arm target-coords &rest args)
    (if (eq arm :arms)
      (send* robot :inverse-kinematics-raw target-coords :rotation-axis (list t t)
             :move-target (list (send robot :larm :end-coords) (send robot :rarm :end-coords))
             :avoid-collision-distance 5 :revert-if-fail nil :stop ik-stop-step
             :debug-view nil args)
      (send* robot :inverse-kinematics-raw target-coords
             :rotation-axis t :move-target (send robot arm :end-coords)
             :avoid-collision-distance 5 :revert-if-fail nil :stop ik-stop-step
             :debug-view nil args)))"""

        # Gripper control methods
        if features.get('gripper_control', False):
            template += f"""
  (:start-grasp (arm &rest args)
    (send* robot-interface :start-grasp arm args))
  (:stop-grasp (arm &rest args)
    (send* robot-interface :stop-grasp arm args))"""

        # Arm motion callback
        template += f"""
  (:arm-motion-cb (&rest args &key (mirror nil) &allow-other-keys)
    (send* self :arm-motion-cb-{self.robot_name}-org :mirror mirror args))
  )"""

        # Visualization functions
        template += f"""


;; Visualization setup
(defun make-{self.robot_name}-irtviewer (&key (no-window t))
  (if (and no-window
           (string>= (car lisp-implementation-version) "9.28"))
    (make-irtviewer-no-window))
  (objects (list *{self.robot_name}*))
  (send *irtviewer* :change-background (float-vector 1 1 1))
  (send *irtviewer* :draw-floor 100)
  (send *irtviewer* :floor-color #f(0 0 0))
  (setq *background-cube* (make-cube 10 6000 6000))
  (send *background-cube* :set-color #f(1 1 1))
  (send *background-cube* :translate #f(-1000 0 0)))


(defun make-{self.robot_name}-camera-model (&key (no-window t))
  (setq *camera-model*
        (if (string>= (car lisp-implementation-version) "9.28")
          (make-camera-from-param
            :pwidth 600 :pheight 600 :fx 400 :fy 400 :cx 319.5 :cy 319.5
            :name "camera" :create-viewer t :no-window no-window)
          (make-camera-from-param
            :pwidth 600 :pheight 600 :fx 400 :fy 400 :cx 319.5 :cy 319.5
            :name "camera" :create-viewer t)))
  (send *camera-model* :translate #f(1500 0 600))
  (send *camera-model* :rotate -pi/2 :y :world)
  (send *camera-model* :rotate -pi/2 :x :world)
  (send *camera-model* :rotate -0.30 :y :world))


;; Signal handling
(defun signal-hook (sig code)
  (if (boundp '*ri*)
    (progn
      (ros::ros-info "cancel larm controller")
      (send *ri* :cancel-angle-vector :controller-type :larm-controller)
      (ros::ros-info "cancel rarm controller")
      (send *ri* :cancel-angle-vector :controller-type :rarm-controller)))
  (reset))


(unix:signal 2 'signal-hook)
(unix:signal 9 'signal-hook)
(unix:signal 15 'signal-hook)


(provide :{self.robot_name}-teleop-interface)
"""

        return template

    def generate_main_file(self) -> str:
        """Generate robot-specific main teleop file content."""
        
        features = self.config['features']
        robot_methods = self.config.get('robot_methods', {})
        controllers = self.config['controllers']
        
        template = f"""#!/usr/bin/env roseus

(require :{self.robot_name}-vive-interface "package://eus_teleop/euslisp/lib/{self.robot_name}-vive-interface.l")
(require :{self.robot_name}-oculus-interface "package://eus_teleop/euslisp/lib/{self.robot_name}-oculus-interface.l")
(require :{self.robot_name}-spacenav-interface "package://eus_teleop/euslisp/lib/{self.robot_name}-spacenav-interface.l")
(require :{self.robot_name}-tablis-interface "package://eus_teleop/euslisp/lib/{self.robot_name}-tablis-interface.l")


(defun vive-init (&key (lgripper :parallel) (rgripper :parallel) (loop-enable t))
  ({self.robot_name}-vive-init :lgripper lgripper :rgripper rgripper :loop-enable loop-enable)
  (send *ti* :reset-arm :larm :wait nil)
  (send *ti* :reset-arm :rarm :wait nil)
  (send *ri* :wait-interpolation)
  (send *ti* :send-joy-feedback :larm)
  (send *ti* :send-joy-feedback :rarm))


(defun oculus-init (&key (lgripper :parallel) (rgripper :parallel) (loop-enable t))
  ({self.robot_name}-oculus-init :lgripper lgripper :rgripper rgripper :loop-enable loop-enable)
  (send *ti* :reset-arm :larm :wait nil)
  (send *ti* :reset-arm :rarm :wait nil)
  (send *ri* :wait-interpolation))


(defun spacenav-init (&key (lgripper :parallel) (rgripper :parallel) (loop-enable t))
  ({self.robot_name}-spacenav-init :lgripper lgripper :rgripper rgripper :loop-enable loop-enable)
  (send *ti* :reset-arm :larm :wait nil)
  (send *ti* :reset-arm :rarm :wait nil)
  (send *ri* :wait-interpolation))


(defun tablis-init (&key (lgripper :parallel) (rgripper :parallel) (loop-enable t))
  ({self.robot_name}-tablis-init :lgripper lgripper :rgripper rgripper :loop-enable loop-enable)
  (send *ti* :reset-arm :larm :wait nil)
  (send *ti* :reset-arm :rarm :wait nil)
  (send *ri* :wait-interpolation)
  (send *ti* :send-joy-feedback :larm)
  (send *ti* :send-joy-feedback :rarm))


(defun init (&key (lgripper :parallel) (rgripper :parallel) (loop-enable t) (device-type :vive))
  (ros::roseus "{self.robot_name}_teleop_main" :anonymous nil)
  (cond
    ((eq device-type :vive)
     (vive-init :lgripper lgripper :rgripper rgripper :loop-enable loop-enable))
    ((eq device-type :oculus)
     (oculus-init :lgripper lgripper :rgripper rgripper :loop-enable loop-enable))
    ((eq device-type :spacenav)
     (spacenav-init :lgripper lgripper :rgripper rgripper :loop-enable loop-enable))
    ((eq device-type :tablis)
     (tablis-init :lgripper lgripper :rgripper rgripper :loop-enable loop-enable))
    (t nil))
  (send *irtviewer* :draw-objects)
  (x::window-main-one))


(defun main (&key (head {'t' if features.get('head_control', False) else 'nil'}) (safe-arm t) (mirror nil) (visualize t)
                  (lgripper :parallel) (rgripper :parallel) (loop-enable t) (device-type :vive))
  (init :lgripper lgripper :rgripper rgripper :loop-enable t :device-type device-type)"""

        if robot_methods.get('nod', False):
            template += f"""
  (send *ri* :nod)"""

        torso_control = 't' if features.get('torso_control', False) else 'nil'
        
        template += f"""
  (if (not loop-enable) (send *ti* :disable))
  (cond"""

        for controller_name, controller_config in controllers.items():
            template += f"""
    ((eq device-type :{controller_name})
     (send *ti* :main-loop :head head :torso {torso_control} :safe-arm safe-arm
           :mirror mirror :visualize visualize
           :enable-button :{controller_config['enable_button']} :gripper-button :{controller_config['gripper_button']}
           ))"""

        template += f"""
    (t nil)))
"""

        return template

    def generate_controller_interface(self, controller_name: str) -> str:
        """Generate controller-specific interface file content."""
        
        robot_config = self.config['robot']
        
        template = f""";; -*- mode: lisp;-*-"""
        
        # Load ROS manifest if core_msgs_package exists
        if robot_config.get('core_msgs_package'):
            template += f"""
(ros::load-ros-manifest "{robot_config['core_msgs_package']}")"""
        
        template += f"""

(require :{self.robot_name}-interface "package://eus_teleop/euslisp/lib/{self.robot_name}-interface.l")
(require :robot-teleop-interface "package://eus_teleop/euslisp/lib/robot-teleop-interface.l")
(require :{self.robot_name}-teleop-interface "package://eus_teleop/euslisp/lib/{self.robot_name}-teleop-interface.l")
(require :robot-{controller_name}-interface "package://eus_teleop/euslisp/lib/robot-{controller_name}-interface.l")


(defclass {self.robot_name}-{controller_name}-interface
  :super robot-{controller_name}-interface
  :slots ())


(defmethod {self.robot_name}-{controller_name}-interface
  (:init (&rest args)
    (prog1
      (send-super* :init args)
      ;; {self.robot_name_title}-specific {controller_name} configuration
      (send self :set-val 'scale 3.0))))


(defun {self.robot_name}-{controller_name}-init (&key (lgripper :parallel) (rgripper :parallel) (loop-enable t))
  ;; Initialize robot (ensure robot model and interface are loaded)
  (init-{self.robot_name})
  
  ;; Robot-specific initialization
  (when *ri*
    (send *ri* :spin-once)
    (when (find-method *{self.robot_name}* :reset-pose)
      (send *ri* :angle-vector (send *{self.robot_name}* :reset-pose) 2000)
      (send *ri* :wait-interpolation)))
  
  ;; Setup visualization
  (make-{self.robot_name}-irtviewer :no-window t)
  (make-{self.robot_name}-camera-model :no-window t)
  
  ;; Create teleop interface instance
  (setq *ti* (instance {self.robot_name}-{controller_name}-interface :init :loop-enable loop-enable
                       :lgripper lgripper :rgripper rgripper))
  (send *ti* :ros-init))

(provide :{self.robot_name}-{controller_name}-interface)
"""
        return template

    def generate_basic_robot_interface(self) -> str:
        """Generate basic robot interface file if it doesn't exist."""
        
        eus_package = self.config['robot']['eus_package']
        
        template = f""";; -*- mode: lisp;-*-
;; Robot interface file for {self.robot_name_title}

;; Load robot description and interface from robot EusLisp package
(require :{self.robot_name} "package://{eus_package}/{self.robot_name}.l")
(require :{self.robot_name}-interface "package://{eus_package}/{self.robot_name}-interface.l")

;; Robot model and interface instances
(defvar *{self.robot_name}* nil "Robot model instance")
(defvar *ri* nil "Robot interface instance")

;; Initialize robot model and interface
(defun init-{self.robot_name} ()
  "Initialize {self.robot_name_title} robot model and interface"
  (unless *{self.robot_name}*
    (setq *{self.robot_name}* ({self.robot_name}))
    (ros::ros-info "Loaded {self.robot_name_title} robot model"))
  
  (unless *ri*
    (setq *ri* (instance {self.robot_name}-interface :init))
    (ros::ros-info "Initialized {self.robot_name_title} robot interface"))
  
  (list *{self.robot_name}* *ri*))

;; Auto-initialize when loading this file
(init-{self.robot_name})

(provide :{self.robot_name}-interface)
"""
        return template

    def create_files(self, output_dir: str):
        """Create all necessary files for the robot teleop interface."""
        
        # Ensure directories exist
        lib_dir = os.path.join(output_dir, 'euslisp', 'lib')
        euslisp_dir = os.path.join(output_dir, 'euslisp')
        
        for directory in [lib_dir, euslisp_dir]:
            os.makedirs(directory, exist_ok=True)
        
        # Check if basic robot interface exists, create if requested in config
        robot_interface_path = os.path.join(lib_dir, f'{self.robot_name}-interface.l')
        created_robot_interface = False
        generation_config = self.config.get('generation', {})
        
        if not os.path.exists(robot_interface_path):
            if generation_config.get('create_robot_interface', True):
                robot_interface_content = self.generate_basic_robot_interface()
                with open(robot_interface_path, 'w') as f:
                    f.write(robot_interface_content)
                print(f"Generated: {robot_interface_path}")
                created_robot_interface = True
            else:
                print(f"Skipping: {robot_interface_path} (create_robot_interface=false)")
        else:
            if generation_config.get('overwrite_existing', False):
                robot_interface_content = self.generate_basic_robot_interface()
                with open(robot_interface_path, 'w') as f:
                    f.write(robot_interface_content)
                print(f"Overwritten: {robot_interface_path}")
                created_robot_interface = True
            else:
                print(f"Using existing: {robot_interface_path}")
        
        # Generate main teleop interface file
        teleop_interface_content = self.generate_teleop_interface()
        teleop_interface_path = os.path.join(lib_dir, f'{self.robot_name}-teleop-interface.l')
        with open(teleop_interface_path, 'w') as f:
            f.write(teleop_interface_content)
        print(f"Generated: {teleop_interface_path}")
        
        # Generate main file
        main_content = self.generate_main_file()
        main_path = os.path.join(euslisp_dir, f'{self.robot_name}-teleop-main.l')
        with open(main_path, 'w') as f:
            f.write(main_content)
        print(f"Generated: {main_path}")
        
        # Generate controller interfaces
        controllers = ['vive', 'oculus', 'spacenav', 'tablis']
        for controller in controllers:
            controller_content = self.generate_controller_interface(controller)
            controller_path = os.path.join(lib_dir, f'{self.robot_name}-{controller}-interface.l')
            with open(controller_path, 'w') as f:
                f.write(controller_content)
            print(f"Generated: {controller_path}")
        
        # Print required files info
        self.print_requirements_info(created_robot_interface)

    def print_requirements_info(self, created_robot_interface: bool = False):
        """Print information about required files and setup steps."""
        
        eus_package = self.config['robot']['eus_package']
        
        print(f"\n{'='*60}")
        print("IMPORTANT: Required Files and Setup")
        print(f"{'='*60}")
        
        if not created_robot_interface:
            print(f"\nUsing existing robot interface files.")
        else:
            print(f"\nRobot interface file created:")
            print(f"   - {self.robot_name}-interface.l (PLACEHOLDER)")
            print(f"   WARNING: You MUST replace the placeholder with your actual robot implementation")
        
        print(f"\nNEXT STEPS:")
        print(f"   1. Ensure your robot EusLisp package ({eus_package}) is properly set up")
        print(f"   2. Implement or link the robot interface files")
        print(f"   3. Update topic names in the YAML config if needed:")
        
        topics = self.config['topics']
        if topics['gripper_status']['larm']:
            print(f"      - Gripper topics: {topics['gripper_status']['larm']}")
        if topics['collision_status']['larm']:
            print(f"      - Collision topics: {topics['collision_status']['larm']}")
        
        print(f"   4. Test the generated files:")
        print(f"      roseus euslisp/{self.robot_name}-teleop-main.l")
        print(f"      (main :device-type :vive)")
        
        print(f"\nTIP: Copy and modify an existing robot's interface files as a starting point")
        print(f"{'='*60}\n")


def main():
    parser = argparse.ArgumentParser(
        description="Generate robot-specific teleop and controller interface files from YAML configuration",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate files for Sciurus17 robot
  python3 generate_robot_teleop.py config/sciurus17.yaml
  
  # Generate with custom output directory
  python3 generate_robot_teleop.py config/sciurus17.yaml -o /path/to/output
        """
    )
    
    parser.add_argument('config_file', help='YAML configuration file path')
    parser.add_argument('-o', '--output-dir', default='.',
                       help='Output directory for generated files (default: current directory)')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.config_file):
        print(f"Error: Configuration file {args.config_file} not found")
        sys.exit(1)
    
    try:
        generator = RobotTeleopGenerator(args.config_file)
        print(f"Generating teleop files for robot: {generator.robot_name}")
        print(f"Output directory: {args.output_dir}")
        print()
        
        generator.create_files(args.output_dir)
        
        print(f"""
Files generated successfully!

Next steps:
1. Review the generated files and modify as needed
2. Ensure your robot interface is properly implemented
3. Test the generated files with your robot setup

Usage:
  roseus euslisp/{generator.robot_name}-teleop-main.l
  (main :device-type :vive)  ; or :oculus, :spacenav, :tablis
        """)
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
