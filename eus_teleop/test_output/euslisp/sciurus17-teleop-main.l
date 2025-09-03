#!/usr/bin/env roseus

(require :sciurus17-vive-interface "package://eus_teleop/euslisp/lib/sciurus17-vive-interface.l")
(require :sciurus17-oculus-interface "package://eus_teleop/euslisp/lib/sciurus17-oculus-interface.l")
(require :sciurus17-spacenav-interface "package://eus_teleop/euslisp/lib/sciurus17-spacenav-interface.l")
(require :sciurus17-tablis-interface "package://eus_teleop/euslisp/lib/sciurus17-tablis-interface.l")


(defun vive-init (&key (lgripper :parallel) (rgripper :parallel) (loop-enable t))
  (sciurus17-vive-init :lgripper lgripper :rgripper rgripper :loop-enable loop-enable)
  (send *ti* :reset-arm :larm :wait nil)
  (send *ti* :reset-arm :rarm :wait nil)
  (send *ri* :wait-interpolation)
  (send *ti* :send-joy-feedback :larm)
  (send *ti* :send-joy-feedback :rarm))


(defun oculus-init (&key (lgripper :parallel) (rgripper :parallel) (loop-enable t))
  (sciurus17-oculus-init :lgripper lgripper :rgripper rgripper :loop-enable loop-enable)
  (send *ti* :reset-arm :larm :wait nil)
  (send *ti* :reset-arm :rarm :wait nil)
  (send *ri* :wait-interpolation))


(defun spacenav-init (&key (lgripper :parallel) (rgripper :parallel) (loop-enable t))
  (sciurus17-spacenav-init :lgripper lgripper :rgripper rgripper :loop-enable loop-enable)
  (send *ti* :reset-arm :larm :wait nil)
  (send *ti* :reset-arm :rarm :wait nil)
  (send *ri* :wait-interpolation))


(defun tablis-init (&key (lgripper :parallel) (rgripper :parallel) (loop-enable t))
  (sciurus17-tablis-init :lgripper lgripper :rgripper rgripper :loop-enable loop-enable)
  (send *ti* :reset-arm :larm :wait nil)
  (send *ti* :reset-arm :rarm :wait nil)
  (send *ri* :wait-interpolation)
  (send *ti* :send-joy-feedback :larm)
  (send *ti* :send-joy-feedback :rarm))


(defun init (&key (lgripper :parallel) (rgripper :parallel) (loop-enable t) (device-type :vive))
  (ros::roseus "sciurus17_teleop_main" :anonymous nil)
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


(defun main (&key (head true) (safe-arm t) (mirror nil) (visualize t)
                  (lgripper :parallel) (rgripper :parallel) (loop-enable t) (device-type :vive))
  (init :lgripper lgripper :rgripper rgripper :loop-enable t :device-type device-type)
  (if (not loop-enable) (send *ti* :disable))
  (cond
    ((eq device-type :vive)
     (send *ti* :main-loop :head head :torso true :safe-arm safe-arm
           :mirror mirror :visualize visualize
           :enable-button :menu :gripper-button :trigger
           ))
    ((eq device-type :oculus)
     (send *ti* :main-loop :head head :torso true :safe-arm safe-arm
           :mirror mirror :visualize visualize
           :enable-button :menu :gripper-button :trigger
           ))
    ((eq device-type :spacenav)
     (send *ti* :main-loop :head head :torso true :safe-arm safe-arm
           :mirror mirror :visualize visualize
           :enable-button :right :gripper-button :left
           ))
    ((eq device-type :tablis)
     (send *ti* :main-loop :head head :torso true :safe-arm safe-arm
           :mirror mirror :visualize visualize
           :enable-button :menu :gripper-button :trigger
           ))
    (t nil)))
