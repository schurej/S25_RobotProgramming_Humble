import rclpy
from rclpy.node import Node
from my_robot_interfaces.srv import SetLedColor
from geometry_msgs.msg import PoseStamped
import numpy as np

class TrackingNode(Node):
    def __init__(self):
        super().__init__('tracking_node')

        self.declare_parameter('att_gain', 1.25)
        self.declare_parameter('rep_gain', 0.8)
        self.declare_parameter('rep_rad', 0.55)
        self.declare_parameter('stop_thresh', 0.35)

        self.att_gain    = self.get_parameter('att_gain').value
        self.rep_gain    = self.get_parameter('rep_gain').value
        self.obj_rep_rad = self.get_parameter('rep_rad').value
        self.stop_thresh = self.get_parameter('stop_thresh').value


        self.goal = None    
        self.obs  = None

        self.create_subscription(
            PoseStamped, 'detected_goal_pose', self.cb_goal, 10)
        self.create_subscription(
            PoseStamped, 'detected_obstacle_pose', self.cb_obs, 10)

        self.cli = self.create_client(SetLedColor, 'set_led_color')
        while not self.cli.wait_for_service(timeout_sec=1.0):
            self.get_logger().warn('service not available, waiting...')

        self.create_timer(0.05, self.on_timer)

        self.get_logger().info(
            f"TrackingNode ready (led service client up, "
            f"att={self.att_gain}, rep={self.rep_gain})"
        )

    def cb_goal(self, msg: PoseStamped):
        self.goal = np.array([
            msg.pose.position.x,
            msg.pose.position.y
        ])

    def cb_obs(self, msg: PoseStamped):
        self.obs = np.array([
            msg.pose.position.x,
            msg.pose.position.y
        ])

    def compute_color(self):

        if self.goal is None or self.obs is None:
            return (255, 0, 0)

        dist = np.linalg.norm(self.obs)
        t = max(0.0, min(dist / self.obj_rep_rad, 1.0))
        g = int((1.0 - t) * 255)
        return (0, g, 0)

    def on_timer(self):
        r, g, b = self.compute_color()

        req = SetLedColor.Request()
        req.r = r
        req.g = g
        req.b = b
        self.cli.call_async(req)

    def destroy_node(self):
        super().destroy_node()
        self.get_logger().info("TrackingNode shut down.")

def main(args=None):
    rclpy.init(args=args)
    node = TrackingNode()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__=='__main__':
    main()

