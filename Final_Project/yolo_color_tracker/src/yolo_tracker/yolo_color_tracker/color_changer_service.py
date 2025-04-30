import rclpy
from rclpy.node import Node
from my_robot_interfaces.srv import SetLedColor
from std_msgs.msg import ColorRGBA
from geometry_msgs.msg import Vector3


class LedBarService(Node):
    def __init__(self):
        super().__init__('set_led_color_service')

        self.srv = self.create_service(
            SetLedColor,
            'set_led_color',
            self.cb_set_color
        )

        self.pub = self.create_publisher(ColorRGBA, 'led_bar_color', 10)

        self.sub = self.create_subscription(
            Vector3,
            'object_distance',
            self.distance_callback,
            10
        )

        red_msg = ColorRGBA()
        self.set_red(red_msg)
        self.pub.publish(red_msg)
        self.get_logger().info('LED bar defaulted to RED; waiting for distance msgs?')

    def cb_set_color(self, request, response):
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
        msg = ColorRGBA()
        if dist.x == 0.0 and dist.y == 0.0 and dist.z == 0.0:
            self.set_red(msg)
            self.get_logger().info('No object detected ? RED')
        else:
            self.set_rgba_with_alpha(msg, dist.x, dist.y, dist.z)
            self.get_logger().info(f"Obj detected ? alpha={msg.a:.2f} with set_rgba_with_alpha")

        self.pub.publish(msg)

    def set_rgba_with_alpha(self, msg: ColorRGBA, x: float, y: float, z: float) -> None:
        msg.r = 0.0
        msg.g = 1.0
        msg.b = 0.0
        s = abs(x) + abs(y) + abs(z)
        alpha = 1.0 - (s / 3.0)
        msg.a = max(0.0, min(alpha, 1.0))

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

