#!/usr/bin/env roseus

(require :hironxjsk-oculus-interface "package://eus_teleop/euslisp/lib/hironxjsk-oculus-interface.l")


(defun oculus-init (&key (lgripper :default) (rgripper :default) (loop-enable t) (ar t))
  (hironxjsk-oculus-init :lgripper lgripper :rgripper rgripper :loop-enable loop-enable :ar t)
  (send *ti* :reset-arm :larm)
  (send *ti* :reset-arm :rarm)
  (send *ri* :wait-interpolation))


(defun init (&key (lgripper :default) (rgripper :default) (loop-enable t) (device-type :oculus) (ar t))
  (ros::roseus "hironxjsk_teleop_main" :anonymous nil)
  (cond
    ((eq device-type :oculus)
     (oculus-init :lgripper lgripper :rgripper rgripper :loop-enable loop-enable :ar ar))
    (t nil))
  (send *irtviewer* :draw-objects)
  (x::window-main-one))


(defun main (&key (head nil) (safe-arm t) (mirror nil) (visualize t)
                  (lgripper :default) (rgripper :default) (loop-enable t) (device-type :oculus) (ar t))
  (init :lgripper lgripper :rgripper rgripper :loop-enable t :device-type device-type :ar t)
  (send *ri* :nod)
  (if (not loop-enable) (send *ti* :disable))
  (cond
    ((eq device-type :oculus)
     (send *ti* :main-loop :head head :torso t :safe-arm safe-arm
           :mirror mirror :visualize visualize
           :enable-button :menu :gripper-button :trigger
           ))
    (t nil)))
