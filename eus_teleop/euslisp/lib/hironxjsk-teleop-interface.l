;; -*- mode: lisp;-*-

(ros::roseus-add-msgs "geometry_msgs")

(require :hironxjsk-interface "package://hrpsys_ros_bridge_tutorials/euslisp/hironxjsk-interface.l")
(require :robot-teleop-interface "package://eus_teleop/euslisp/lib/robot-teleop-interface.l")


(if (not (assoc :init-hironxjsk-org (send robot-teleop-interface :methods)))
  (rplaca (assoc :init (send robot-teleop-interface :methods)) :init-hironxjsk-org))
(if (not (assoc :reset-hironxjsk-org (send robot-teleop-interface :methods)))
  (rplaca (assoc :reset (send robot-teleop-interface :methods)) :reset-hironxjsk-org))
(if (not (assoc :reset-arm-hironxjsk-org (send robot-teleop-interface :methods)))
  (rplaca (assoc :reset-arm (send robot-teleop-interface :methods)) :reset-arm-hironxjsk-org))
(if (not (assoc :disable-hironxjsk-org (send robot-teleop-interface :methods)))
  (rplaca (assoc :disable (send robot-teleop-interface :methods)) :disable-hironxjsk-org))
(if (not (assoc :enable-hironxjsk-org (send robot-teleop-interface :methods)))
  (rplaca (assoc :enable (send robot-teleop-interface :methods)) :enable-hironxjsk-org))
(if (not (assoc :arm-motion-cb-hironxjsk-org (send robot-teleop-interface :methods)))
  (rplaca (assoc :arm-motion-cb (send robot-teleop-interface :methods)) :arm-motion-cb-hironxjsk-org))


(defmethod robot-teleop-interface
  (:init (&rest args)
    (prog1
      (send* self :init-hironxjsk-org args)
      (send self :set-val 'robot *hironxjsk*)
      (send self :set-val 'robot-interface *ri*)
      (send self :set-val 'camera-model *camera-model*)
      (send self :set-val 'rate 10)
      (send self :set-val 'end-coords-pos-diff-thresh 400)
      (send self :set-val 'draw-object-list (list *hironxjsk*))
      ;; hironxjsk frame
      (send self :set-val 'base-frame-id "WAIST")
      (send self :set-val 'head-frame-id "HEAD_JOINT1_Link")
      ;; hironxjsk ik
      (send self :set-val 'arm-cb-solve-ik t)
      (send self :set-val 'ik-stop-step 10)
      (send self :set-val 'av-tm 300)
      (send self :set-val 'av-scale 1.0)
      (send self :set-val 'min-time 0.5)
      ;; hironxjsk gripper
      (send self :set-val 'grasp-timeout-time 1.5)
      ;; hironxjsk hardware configuration
      (send self :set-val 'arm-length 800)
      (send self :set-val 'head->shoulder-x-distance 100)
      (send self :set-val 'head->shoulder-z-distance 50)

      (send self :set-arm-val :larm :gripper-status-topic-name
            "/hironxjsk/l_gripper_controller/status")
      (send self :set-arm-val :rarm :gripper-status-topic-name
            "/hironxjsk/r_gripper_controller/status")))
  (:reset (&key (loop-enable t))
    (send self :reset-hironxjsk-org :loop-enable loop-enable :torso nil))
  (:reset-arm (arm &key (wait t))
    (send self :reset-arm-hironxjsk-org arm :wait wait :reset-pose :reset-teleop-pose))
  (:enable () (send self :enable-hironxjsk-org :torso nil))
  (:disable () (send self :disable-hironxjsk-org :torso nil))
  (:move-head (yaw pitch roll)
    ;; hironxjsk has head pan/tilt joints
    (send robot :head_joint0 :joint-angle (rad2deg yaw))
    (send robot :head_joint1 :joint-angle (rad2deg pitch))
    (send self :angle-vector (send robot :angle-vector) av-tm
          :head-controller 0 :min-time min-time :scale av-scale))
  (:get-head-end-coords ()
    (let (coords)
      (send tfl :wait-for-transform base-frame-id head-frame-id (ros::time 0) 0.1)
      (setq coords (send tfl :lookup-transform base-frame-id head-frame-id (ros::time 0)))
      (if coords (send coords :rotate pi/2 :y :world))
      coords))
  (:angle-vector (&rest args)
    (send* robot-interface :angle-vector args))
  (:inverse-kinematics (arm target-coords &rest args)
    (if (eq arm :arms)
      (send* robot :inverse-kinematics target-coords :rotation-axis (list t t)
             :move-target (list (send robot :larm :end-coords) (send robot :rarm :end-coords))
             :avoid-collision-distance 5 :revert-if-fail nil :stop ik-stop-step
             :debug-view nil args)
      (send* robot :inverse-kinematics target-coords
             :rotation-axis t :move-target (send robot arm :end-coords)
             :avoid-collision-distance 5 :revert-if-fail nil :stop ik-stop-step
             :debug-view nil args)))
  (:start-grasp (arm &rest args)
    (send* robot-interface :start-grasp arm args))
  (:stop-grasp (arm &rest args)
    (send* robot-interface :stop-grasp arm args))
  (:arm-motion-cb (&rest args &key (mirror nil) &allow-other-keys)
    (send* self :arm-motion-cb-hironxjsk-org :mirror mirror args))
  )


(defun make-hironxjsk-irtviewer (&key (no-window t))
  (if (and no-window
           (string>= (car lisp-implementation-version) "9.28"))
    (make-irtviewer-no-window))
  (objects (list *hironxjsk*))
  (send *irtviewer* :change-background (float-vector 1 1 1))
  (send *irtviewer* :draw-floor 100)
  (send *irtviewer* :floor-color #f(0 0 0)))


(defun make-hironxjsk-camera-model (&key (no-window t))
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


(provide :hironxjsk-teleop-interface)