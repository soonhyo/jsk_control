;; -*- mode: lisp;-*-
(ros::load-ros-manifest "hironxjsk")

(require :hironxjsk-interface "package://hrpsys_ros_bridge_tutorials/euslisp/hironxjsk-interface.l")
(require :robot-teleop-interface "package://eus_teleop/euslisp/lib/robot-teleop-interface.l")
(require :hironxjsk-teleop-interface "package://eus_teleop/euslisp/lib/hironxjsk-teleop-interface.l")
(require :robot-oculus-interface "package://eus_teleop/euslisp/lib/robot-oculus-interface.l")


(defclass hironxjsk-oculus-interface
  :super robot-oculus-interface
  :slots (larm-thumb-open
          rarm-thumb-open))


(defmethod hironxjsk-oculus-interface
  (:init (&key (ar nil) &rest args)
    (prog1
      (send-super* :init args)
      ;; for oculus
      (send self :set-val 'scale 1.0)  ;; Changed to 1:1 scale
      (send self :set-val 'hmd-pose-topic-name "/oculus/hmd/pose_stamped")
      (send self :set-val 'left-controller-pose-topic-name "/left_wrist_target_pose")
      (send self :set-val 'right-controller-pose-topic-name "/right_wrist_target_pose")
      (send self :set-val 'ar-mode ar)
      (if ar
          (send self :set-val 'scale 1.0)
          (send self :set-val 'head nil)
          (send self :set-val 'mirror nil) ;; Thre is no head and mirror option in ar mode.
          )
      ))
  
  ;; Override inverse-kinematics to use hand coords instead of end-coords
  (:inverse-kinematics (arm target-coords &rest args)
    (if (eq arm :arms)
      (send* robot :inverse-kinematics target-coords :rotation-axis (list t t)
             :move-target (list (send robot :larm :end-coords :parent) (send robot :rarm :end-coords :parent))
             :link-list (list (send robot :link-list (send robot :larm :end-coords :parent))
                              (send robot :link-list (send robot :rarm :end-coords :parent)))
             :revert-if-fail nil :stop ik-stop-step :debug-view nil args)
      (if (eq arm :larm)
        (send* robot :inverse-kinematics target-coords :rotation-axis t
               :move-target (send robot :larm :end-coords :parent)
               :link-list (send robot :link-list (send robot :larm :end-coords :parent))
               :revert-if-fail nil :stop ik-stop-step :debug-view nil args)
        (send* robot :inverse-kinematics target-coords :rotation-axis t
               :move-target (send robot :rarm :end-coords :parent)
               :link-list (send robot :link-list (send robot :rarm :end-coords :parent))
               :revert-if-fail nil :stop ik-stop-step :debug-view nil args))))
  )


(defun hironxjsk-oculus-init (&key (lgripper :default) (rgripper :default) (loop-enable t) (ar nil))
  ;; Note: hironxjsk-init should be called when hrpsys_ros_bridge_tutorials package is available
  ;; (hironxjsk-init :lgripper lgripper :rgripper rgripper)
  (make-hironxjsk-irtviewer :no-window nil)
  (setq *ti* (instance hironxjsk-oculus-interface :init :loop-enable loop-enable
                       :lgripper lgripper :rgripper rgripper :ar ar))
  (send *ti* :ros-init))
