;; -*- mode: lisp;-*-
(require :robot-vive-interface "package://eus_teleop/euslisp/lib/robot-vive-interface.l")
(require :sciurus17-teleop-interface "package://eus_teleop/euslisp/lib/sciurus17-teleop-interface.l")

(defun sciurus17-vive-init (&key (lgripper :parallel) (rgripper :parallel) (loop-enable t))
  (robot-vive-init)
  (send *ri* :spin-once)
  (send *ri* :angle-vector (send *sciurus17* :reset-pose) 2000)
  (send *ri* :wait-interpolation)
  (make-sciurus17-irtviewer :no-window t)
  (make-sciurus17-camera-model :no-window t)
  (setq *ti* (instance robot-teleop-interface :init :loop-enable loop-enable :lgripper lgripper :rgripper rgripper))
  (send *ti* :ros-init)
  (send *ti* :reset :loop-enable loop-enable))

(provide :sciurus17-vive-interface)
