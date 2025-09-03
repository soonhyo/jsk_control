;; -*- mode: lisp;-*-

(require :sciurus17-interface "package://eus_teleop/euslisp/lib/sciurus17-interface.l")
(require :robot-teleop-interface "package://eus_teleop/euslisp/lib/robot-teleop-interface.l")


;; Method renaming for sciurus17-specific overrides
(if (not (assoc :init-sciurus17-org (send robot-teleop-interface :methods)))
  (rplaca (assoc :init (send robot-teleop-interface :methods)) :init-sciurus17-org))
(if (not (assoc :reset-sciurus17-org (send robot-teleop-interface :methods)))
  (rplaca (assoc :reset (send robot-teleop-interface :methods)) :reset-sciurus17-org))
(if (not (assoc :reset-arm-sciurus17-org (send robot-teleop-interface :methods)))
  (rplaca (assoc :reset-arm (send robot-teleop-interface :methods)) :reset-arm-sciurus17-org))
(if (not (assoc :disable-sciurus17-org (send robot-teleop-interface :methods)))
  (rplaca (assoc :disable (send robot-teleop-interface :methods)) :disable-sciurus17-org))
(if (not (assoc :enable-sciurus17-org (send robot-teleop-interface :methods)))
  (rplaca (assoc :enable (send robot-teleop-interface :methods)) :enable-sciurus17-org))
(if (not (assoc :arm-motion-cb-sciurus17-org (send robot-teleop-interface :methods)))
  (rplaca (assoc :arm-motion-cb (send robot-teleop-interface :methods)) :arm-motion-cb-sciurus17-org))


(defmethod robot-teleop-interface
  (:init (&rest args)
    (prog1
      (send* self :init-sciurus17-org args)
      (send self :set-val 'robot *sciurus17*)
      (send self :set-val 'robot-interface *ri*)
      (send self :set-val 'camera-model *camera-model*)
      (send self :set-val 'rate 10)
      (send self :set-val 'end-coords-pos-diff-thresh 300)
      (send self :set-val 'draw-object-list (list *sciurus17* *background-cube*))
      
      ;; Sciurus17 frame configuration
      (send self :set-val 'base-frame-id "base_link")
      (send self :set-val 'head-frame-id "neck_yaw_link")
      
      ;; Sciurus17 inverse kinematics configuration
      (send self :set-val 'arm-cb-solve-ik true)
      (send self :set-val 'ik-stop-step 10)
      (send self :set-val 'av-tm 300)
      (send self :set-val 'av-scale 3.0)
      (send self :set-val 'min-time 0.3)
      
      ;; Sciurus17 gripper configuration
      (send self :set-val 'grasp-timeout-time 1.5)
      
      ;; Gripper status topics
      (send self :set-arm-val :larm :gripper-status-topic-name
            "/sciurus17/controller/l_gripper_controller/gripper_cmd/status")
      (send self :set-arm-val :rarm :gripper-status-topic-name
            "/sciurus17/controller/r_gripper_controller/gripper_cmd/status")
      
      ;; Sciurus17 hardware configuration
      (send self :set-val 'arm-length 800)
      (send self :set-val 'head->shoulder-x-distance 50)
      (send self :set-val 'head->shoulder-z-distance 30)
      
      ;; Torso control configuration
      (send self :set-val 'torso-av-tm 1000)
      (send self :set-val 'torso-av-scale 2.0)
      (send self :set-val 'torso-min-time 0.5)
      (send self :set-val 'torso-z-thresh 150)
      (send self :set-val 'torso-ik-weight 0.3)))
  (:reset (&key (loop-enable t))
    (send self :reset-sciurus17-org :loop-enable loop-enable :torso true))
  (:reset-arm (arm &key (wait t))
    (send self :reset-arm-sciurus17-org arm :wait wait :reset-pose :reset-teleop-pose))
  (:enable () (send self :enable-sciurus17-org :torso true))
  (:disable () (send self :disable-sciurus17-org :torso true))
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
      coords))
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
             :debug-view nil args)))
  (:start-grasp (arm &rest args)
    (send* robot-interface :start-grasp arm args))
  (:stop-grasp (arm &rest args)
    (send* robot-interface :stop-grasp arm args))
  (:arm-motion-cb (&rest args &key (mirror nil) &allow-other-keys)
    (send* self :arm-motion-cb-sciurus17-org :mirror mirror args))
  )


;; Visualization setup
(defun make-sciurus17-irtviewer (&key (no-window t))
  (if (and no-window
           (string>= (car lisp-implementation-version) "9.28"))
    (make-irtviewer-no-window))
  (objects (list *sciurus17*))
  (send *irtviewer* :change-background (float-vector 1 1 1))
  (send *irtviewer* :draw-floor 100)
  (send *irtviewer* :floor-color #f(0 0 0))
  (setq *background-cube* (make-cube 10 6000 6000))
  (send *background-cube* :set-color #f(1 1 1))
  (send *background-cube* :translate #f(-1000 0 0)))


(defun make-sciurus17-camera-model (&key (no-window t))
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


(provide :sciurus17-teleop-interface)
