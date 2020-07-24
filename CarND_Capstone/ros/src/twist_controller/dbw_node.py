#!/usr/bin/env python

import rospy
from std_msgs.msg import Bool
from dbw_mkz_msgs.msg import ThrottleCmd, SteeringCmd, BrakeCmd, SteeringReport
from geometry_msgs.msg import TwistStamped
import math

from twist_controller import Controller, Vehicle

'''
You can build this node only after you have built (or partially built) the `waypoint_updater` node.

You will subscribe to `/twist_cmd` message which provides the proposed linear and angular velocities.
You can subscribe to any other message that you find important or refer to the document for list
of messages subscribed to by the reference implementation of this node.

One thing to keep in mind while building this node and the `twist_controller` class is the status
of `dbw_enabled`. While in the simulator, its enabled all the time, in the real car, that will
not be the case. This may cause your PID controller to accumulate error because the car could
temporarily be driven by a human instead of your controller.

We have provided two launch files with this node. Vehicle specific values (like vehicle_mass,
wheel_base) etc should not be altered in these files.

We have also provided some reference implementations for PID controller and other utility classes.
You are free to use them or build your own.

Once you have the proposed throttle, brake, and steer values, publish it on the various publishers
that we have created in the `__init__` function.

'''


class DBWNode(object):
    def __init__(self):
        rospy.init_node('dbw_node')

        self.steer_pub = rospy.Publisher('/vehicle/steering_cmd', SteeringCmd, queue_size=1)
        self.throttle_pub = rospy.Publisher('/vehicle/throttle_cmd', ThrottleCmd, queue_size=1)
        self.brake_pub = rospy.Publisher('/vehicle/brake_cmd', BrakeCmd, queue_size=1)

        self.current_velocity = None
        self.linear = None
        self.angular = None

        self.dbw_enabled = False

        # Create `TwistController` object
        self.controller = Controller(Vehicle())

        # Subscribe to the required topics
        rospy.Subscriber('/vehicle/steering_report', SteeringReport, self.velocity_callback)
        rospy.Subscriber('/twist_cmd', TwistStamped, self.twist_callback)
        rospy.Subscriber('/vehicle/dbw_enabled', Bool, self.dbw_status_callback)

        self.loop()

    def velocity_callback(self, msg):
        self.current_velocity = msg.speed

    def twist_callback(self, msg):
        self.linear = msg.twist.linear.x
        self.angular = msg.twist.angular.z

    def dbw_status_callback(self, msg):
        self.dbw_enabled = msg.data

    def loop(self):
        rate = rospy.Rate(50)  # 50Hz. Maybe change this
        while not rospy.is_shutdown():

            if not self.dbw_enabled:

                self.controller.reset_pids()
            else:
                if None not in (self.current_velocity, self.linear, self.angular):
                    thr, br, st = self.controller.control(self.linear, self.angular, self.current_velocity)
                    self.publish(throttle=thr, brake=br, steer=st)

            rate.sleep()

    def publish(self, throttle, brake, steer):
        tcmd = ThrottleCmd()
        tcmd.enable = True
        tcmd.pedal_cmd_type = ThrottleCmd.CMD_PERCENT
        tcmd.pedal_cmd = throttle
        self.throttle_pub.publish(tcmd)

        scmd = SteeringCmd()
        scmd.enable = True
        scmd.steering_wheel_angle_cmd = steer
        self.steer_pub.publish(scmd)

        bcmd = BrakeCmd()
        bcmd.enable = True
        bcmd.pedal_cmd_type = BrakeCmd.CMD_TORQUE
        bcmd.pedal_cmd = brake
        self.brake_pub.publish(bcmd)


if __name__ == '__main__':
    DBWNode()
