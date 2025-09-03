;; -*- mode: lisp;-*-

(require :sciurus17-interface "package://eus_teleop/euslisp/lib/sciurus17-interface.l")
(require :robot-teleop-interface "package://eus_teleop/euslisp/lib/robot-teleop-interface.l")
(require :sciurus17-teleop-interface "package://eus_teleop/euslisp/lib/sciurus17-teleop-interface.l")
(require :robot-vive-interface "package://eus_teleop/euslisp/lib/robot-vive-interface.l")


(defclass sciurus17-vive-interface
  :super robot-vive-interface
  :slots ())


(defmethod sciurus17-vive-interface
  (:init (&rest args)
    (prog1
      (send-super* :init args)
      ;; Sciurus17-specific vive configuration
      (send self :set-val 'scale 3.0))))


(defun sciurus17-vive-init (&key (lgripper :parallel) (rgripper :parallel) (loop-enable t))
  ;; Initialize robot (ensure robot model and interface are loaded)
  (init-sciurus17)
  
  ;; Robot-specific initialization
  (when *ri*
    (send *ri* :spin-once)
    (when (find-method *sciurus17* :reset-pose)
      (send *ri* :angle-vector (send *sciurus17* :reset-pose) 2000)
      (send *ri* :wait-interpolation)))
  
  ;; Setup visualization
  (make-sciurus17-irtviewer :no-window t)
  (make-sciurus17-camera-model :no-window t)
  
  ;; Create teleop interface instance
  (setq *ti* (instance sciurus17-vive-interface :init :loop-enable loop-enable
                       :lgripper lgripper :rgripper rgripper))
  (send *ti* :ros-init))

(provide :sciurus17-vive-interface)
