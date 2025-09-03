;; -*- mode: lisp;-*-

(require :sciurus17-interface "package://eus_teleop/euslisp/lib/sciurus17-interface.l")
(require :robot-teleop-interface "package://eus_teleop/euslisp/lib/robot-teleop-interface.l")
(require :sciurus17-teleop-interface "package://eus_teleop/euslisp/lib/sciurus17-teleop-interface.l")
(require :robot-tablis-interface "package://eus_teleop/euslisp/lib/robot-tablis-interface.l")


(defclass sciurus17-tablis-interface
  :super robot-tablis-interface
  :slots ())


(defmethod sciurus17-tablis-interface
  (:init (&rest args)
    (prog1
      (send-super* :init args)
      ;; Sciurus17-specific tablis configuration
      (send self :set-val 'scale 3.0))))


(defun sciurus17-tablis-init (&key (lgripper :parallel) (rgripper :parallel) (loop-enable t))
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
  (setq *ti* (instance sciurus17-tablis-interface :init :loop-enable loop-enable
                       :lgripper lgripper :rgripper rgripper))
  (send *ti* :ros-init))

(provide :sciurus17-tablis-interface)
