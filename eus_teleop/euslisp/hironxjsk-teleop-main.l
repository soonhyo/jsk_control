#!/usr/bin/env roseus

(require :hironxjsk-oculus-interface "package://eus_teleop/euslisp/lib/hironxjsk-oculus-interface.l")


(defun oculus-init (&key (lgripper :default) (rgripper :default) (loop-enable t))
  (hironxjsk-oculus-init :lgripper lgripper :rgripper rgripper :loop-enable loop-enable)
  (send *ti* :reset-arm :larm :wait nil)
  (send *ti* :reset-arm :rarm :wait nil)
  (send *ri* :wait-interpolation))


(defun init (&key (lgripper :default) (rgripper :default) (loop-enable t) (device-type :oculus))
  (ros::roseus "hironxjsk_teleop_main" :anonymous nil)
  (cond
    ((eq device-type :oculus)
     (oculus-init :lgripper lgripper :rgripper rgripper :loop-enable loop-enable))
    (t nil))
  (send *irtviewer* :draw-objects)
  (x::window-main-one))


(defun main (&key (head nil) (safe-arm t) (mirror nil) (visualize t)
                  (lgripper :default) (rgripper :default) (loop-enable t) (device-type :oculus))
  (init :lgripper lgripper :rgripper rgripper :loop-enable t :device-type device-type)
  (send *ri* :nod)
  (if (not loop-enable) (send *ti* :disable))
  (cond
    ((eq device-type :oculus)
     (send *ti* :main-loop :head head :torso nil :safe-arm safe-arm
           :mirror mirror :visualize visualize
           :enable-button :menu :gripper-button :trigger
           ))
    (t nil)))