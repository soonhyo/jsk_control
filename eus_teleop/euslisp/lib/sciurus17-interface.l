;; -*- mode: lisp;-*-
;; Robot interface file for Sciurus17

;; Load robot description and interface from robot EusLisp package
(require :sciurus17 "package://sciurus17eus/sciurus17.l")
(require :sciurus17-interface "package://sciurus17eus/sciurus17-interface.l")

;; Robot model and interface instances
(defvar *sciurus17* nil "Robot model instance")
(defvar *ri* nil "Robot interface instance")

;; Initialize robot model and interface
(defun init-sciurus17 ()
  "Initialize Sciurus17 robot model and interface"
  (unless *sciurus17*
    (setq *sciurus17* (sciurus17))
    (ros::ros-info "Loaded Sciurus17 robot model"))
  
  (unless *ri*
    (setq *ri* (instance sciurus17-interface :init))
    (ros::ros-info "Initialized Sciurus17 robot interface"))
  
  (list *sciurus17* *ri*))

;; Auto-initialize when loading this file
(init-sciurus17)

(provide :sciurus17-interface)
