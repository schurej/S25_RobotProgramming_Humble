#!/usr/bin/env python3
import rclpy
from rclpy.node import Node

from my_robot_interfaces.srv import SetLedColor
from std_msgs.msg import ColorRGBA
from geometry_msgs.msg import Vector3


class LedBarService(Node):
    def __init__(self):
        super().__init__('set_led_color_service')

        # 1) service to allow explicit overrides if you still want it
        self.srv = self.create_service(
            SetLedColor,
            'set_led_color',
            self.cb_set_color
        )

        # 2) publisher that actually drives the LED bar
        self.pub = self.create_publisher(ColorRGBA, 'led_bar_color', 10)

        # 3) subscriber for continuous distance updates
        self.sub = self.create_subscription(
            Vector3,
            'object_distance',
            self.distance_callback,
            10
        )

        # 4) immediately default to red on startup
        red_msg = ColorRGBA()
        self.set_red(red_msg)
        self.pub.publish(red_msg)
        self.get_logger().info('🟥 LED bar defaulted to RED; waiting for distance msgs…')

    def cb_set_color(self, request, response):
        # legacy service handler if you still call it
        msg = ColorRGBA()
        msg.r = request.r / 255.0
        msg.g = request.g / 255.0
        msg.b = request.b / 255.0
        msg.a = 1.0
        self.pub.publish(msg)

        response.success = True
        response.message = f"Set color to R{request.r} G{request.g} B{request.b}"
        self.get_logger().info(response.message)
        return response

    def distance_callback(self, dist: Vector3):
        # dist.x, dist.y, dist.z ∈ [-1,1] or zero if no detection
        msg = ColorRGBA()

        if dist.x == 0.0 and dist.y == 0.0 and dist.z == 0.0:
            # no object → solid red
            self.set_red(msg)
            self.get_logger().info('No object detected → RED')
        else:
            # object detected → choose one mapping below:

            # 1) modulate opacity via alpha
            self.set_rgba_with_alpha(msg, dist.x, dist.y, dist.z)
            self.get_logger().info(
                f"Obj detected → alpha={msg.a:.2f} with set_rgba_with_alpha")

            # 2) (alternative) modulate green level by sum:
            # self.set_green_by_sum(msg, dist.x, dist.y, dist.z)
            # self.get_logger().info(
            #     f"Obj detected → green={msg.g*255:.0f} with set_green_by_sum")

        self.pub.publish(msg)

    def set_rgba_with_alpha(self, msg: ColorRGBA, x: float, y: float, z: float) -> None:
        # always full green color, but alpha fades out as |x|+|y|+|z|→3
        msg.r = 0.0
        msg.g = 1.0
        msg.b = 0.0

        s = abs(x) + abs(y) + abs(z)      # in [0,3]
        alpha = 1.0 - (s / 3.0)           # map 0→3 to 1→0
        msg.a = max(0.0, min(alpha, 1.0))

    def set_green_by_sum(self, msg: ColorRGBA, x: float, y: float, z: float) -> None:
        # opacity always 1, but green ramps from 70→255 as |x|+|y|+|z|→3
        s = abs(x) + abs(y) + abs(z)
        t = max(0.0, min(s / 3.0, 1.0))

        green = 70 + t * (255 - 70)
        msg.r = 0.0
        msg.g = green / 255.0
        msg.b = 0.0
        msg.a = 1.0

    def set_red(self, msg: ColorRGBA) -> None:
        msg.r = 1.0
        msg.g = 0.0
        msg.b = 0.0
        msg.a = 1.0


def main(args=None):
    rclpy.init(args=args)
    node = LedBarService()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
