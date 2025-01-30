#!/usr/bin/env python3

import rclpy
import math
import time
from rclpy.node import Node
from geometry_msgs.msg import Twist
from turtlesim.srv import SetPen

class PentagramDrawer(Node):
    def __init__(self):
        super().__init__('pentagram_drawer')
        self.publisher = self.create_publisher(Twist, '/turtle1/cmd_vel', 10)
        self.pen_client = self.create_client(SetPen, '/turtle1/set_pen')

        # Wait for the service to be available
        while not self.pen_client.wait_for_service(timeout_sec=1.0):
            self.get_logger().info('Waiting for /turtle1/set_pen service...')

        self.set_pen_color(255, 255, 0, 3)  # Yellow pen with width 3
        time.sleep(1)

        self.draw_pentagram()

    def set_pen_color(self, r, g, b, width):
        """ Set the turtle's pen color """
        request = SetPen.Request()
        request.r = r
        request.g = g
        request.b = b
        request.width = width
        request.off = False
        self.pen_client.call_async(request)
        self.get_logger().info(f'Pen color set to RGB({r}, {g}, {b})')

    def move_forward(self, distance, speed=2.0):
        """ Move forward by a certain distance """
        cmd = Twist()
        cmd.linear.x = speed
        start_time = time.time()
        while time.time() - start_time < distance / speed:
            self.publisher.publish(cmd)
            time.sleep(0.1)
        
        cmd.linear.x = 0.0
        self.publisher.publish(cmd)

    def rotate(self, angle, speed=1.0):
        """ Rotate the turtle by a certain angle (in radians) """
        cmd = Twist()
        cmd.angular.z = speed if angle > 0 else -speed  # Determine rotation direction
        start_time = time.time()
        while time.time() - start_time < abs(angle) / speed:
            self.publisher.publish(cmd)
            time.sleep(0.1)

        cmd.angular.z = 0.0
        self.publisher.publish(cmd)

    def draw_pentagram(self):
        """ Draw a five-pointed star """
        side_length = 2.0  # Length of each star side
        turn_angle = math.radians(144)  # Convert 144 degrees to radians

        for _ in range(5):
            self.move_forward(side_length)
            self.rotate(turn_angle)

        self.get_logger().info("Finished drawing the star!")

def main(args=None):
    rclpy.init(args=args)
    node = PentagramDrawer()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()

