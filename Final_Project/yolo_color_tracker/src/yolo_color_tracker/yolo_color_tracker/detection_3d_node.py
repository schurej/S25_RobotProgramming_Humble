import rclpy
from rclpy.node import Node
from sensor_msgs.msg import PointCloud2
from geometry_msgs.msg import PoseStamped
from sensor_msgs_py import point_cloud2
import numpy as np

class Detection3DNode(Node):
    def __init__(self):
        super().__init__('detection_3d_node')
        self.declare_parameter('points_topic', '/camera/depth/points')
        pts = self.get_parameter('points_topic').value

        self.create_subscription(PointCloud2, pts, self.cb_pc, 10)
        self.create_subscription(PoseStamped, 'detections/goal_pixel',     self.cb_goal, 10)
        self.create_subscription(PoseStamped, 'detections/obstacle_pixel', self.cb_obs,  10)

        self.pub_goal = self.create_publisher(PoseStamped, 'detected_goal_pose',      10)
        self.pub_obs  = self.create_publisher(PoseStamped, 'detected_obstacle_pose', 10)

        self.latest_pc = None
        self.get_logger().info(f"Listening for PointCloud2 on '{pts}'")

    def cb_pc(self, msg: PointCloud2):
        if self.latest_pc is None:
            self.get_logger().info("First PointCloud2 received")
        self.latest_pc = msg

    def _project(self, pix: PoseStamped, pub, label):
        if self.latest_pc is None:
            return

        u = int(pix.pose.position.x)
        v = int(pix.pose.position.y)

        pts = []
        for du in (-1, 0, 1):
            for dv in (-1, 0, 1):
                try:
                    gen = point_cloud2.read_points(
                        self.latest_pc,
                        field_names=('x','y','z'),
                        skip_nans=True,
                        uvs=[(u+du, v+dv)]
                    )
                    X_cam, Y_cam, Z_cam = next(gen)
                    if 0.05 < Z_cam < 5.0:
                        pts.append((X_cam, Y_cam, Z_cam))
                except StopIteration:
                    pass

        if not pts:
            self.get_logger().warn(f"[{label}] no valid points around (u={u},v={v})")
            return

        X_cam, Y_cam, Z_cam = np.mean(pts, axis=0)

        out = PoseStamped()
        out.header = pix.header
        out.pose.position.x = Z_cam # forward
        out.pose.position.y = X_cam # rightward
        out.pose.position.z = Y_cam # downward
        out.pose.orientation.w = 1.0

        self.get_logger().info(
            f"[{label}] remapped (X={Z_cam:.2f}, Y={X_cam:.2f}, Z={Y_cam:.2f})"
        )
        pub.publish(out)

    def cb_goal(self, msg):
        self._project(msg, self.pub_goal, 'GOAL')

    def cb_obs(self, msg):
        self._project(msg, self.pub_obs, 'OBST')

def main(args=None):
    rclpy.init(args=args)
    node = Detection3DNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__=='__main__':
    main()

