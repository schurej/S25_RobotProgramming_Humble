import rclpy
from rclpy.node import Node
from rclpy.time import Time
from sensor_msgs.msg import Image
from geometry_msgs.msg import PoseStamped
from cv_bridge import CvBridge
import cv2, numpy as np, os
from ament_index_python.packages import get_package_share_directory

class DetectionNode(Node):
    def __init__(self):
        super().__init__('detection_node')
        self.declare_parameter('target_object', 'apple')
        self.target = self.get_parameter('target_object') \
                          .get_parameter_value().string_value

        self.declare_parameter('image_topic', '/camera/color/image_raw')
        self.img_topic = self.get_parameter('image_topic') \
                             .get_parameter_value().string_value

        cfg = os.path.join(get_package_share_directory('yolo_tracker'), 'config', 'yolov4-tiny.cfg')
        wts = os.path.join(get_package_share_directory('yolo_tracker'), 'config', 'yolov4-tiny.weights')
        names = os.path.join(get_package_share_directory('yolo_tracker'), 'config', 'coco.names')

        self.net = cv2.dnn.readNetFromDarknet(cfg, wts)
        ln = self.net.getLayerNames()
        self.ln = [ln[i - 1] for i in self.net.getUnconnectedOutLayers()]

        with open(names) as f:
            self.classes = [l.strip() for l in f]

        self.allowed_classes = ['person', 'banana', 'apple', 'chair', 'tv', 'laptop', 'bottle']

        self.bridge = CvBridge()
        self.last_image = None

        from rclpy.qos import QoSProfile, QoSReliabilityPolicy
        qos = QoSProfile(depth=1, reliability=QoSReliabilityPolicy.BEST_EFFORT)
        self.image_sub = self.create_subscription(Image, self.img_topic, self.image_callback, qos)
        
        self.timer = self.create_timer(0.2, self.process_image)  

        self.pub_goal = self.create_publisher(PoseStamped, 'detections/goal_pixel', 10)
        self.pub_obs = self.create_publisher(PoseStamped, 'detections/obstacle_pixel', 10)
        self.image_pub = self.create_publisher(Image, 'detection/image_annotated', 10)

    def image_callback(self, msg):
        self.last_image = msg

        now = self.get_clock().now()
        img_time = Time.from_msg(msg.header.stamp)
        delay = (now - img_time).nanoseconds / 1e9
        self.get_logger().warn(f"Image lag: {delay:.2f} sec")

    def process_image(self):
        if self.last_image is None:
            return

        frame = self.bridge.imgmsg_to_cv2(self.last_image, desired_encoding='bgr8')

        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        h, s, v = cv2.split(hsv)
        s = cv2.add(s, 5)
        v = cv2.add(v, 70)
        s = np.clip(s, 0, 255).astype(np.uint8)
        v = np.clip(v, 0, 255).astype(np.uint8)
        hsv = cv2.merge((h, s, v))
        frame = cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)

        h, w = frame.shape[:2]
        blob = cv2.dnn.blobFromImage(frame, 1/255.0, (320, 320), swapRB=True, crop=False)
        self.net.setInput(blob)
        outs = self.net.forward(self.ln)

        boxes, confs, cids = [], [], []
        for out in outs:
            for det in out:
                scores = det[5:]
                cid = int(np.argmax(scores))
                conf = float(scores[cid])
                if conf < 0.5:
                    continue
                cx, cy, bw, bh = (det[0:4] * [w, h, w, h]).astype(int)
                x = max(0, cx - bw // 2)
                y = max(0, cy - bh // 2)
                boxes.append([x, y, bw, bh])
                confs.append(conf)
                cids.append(cid)

        idxs = cv2.dnn.NMSBoxes(boxes, confs, 0.5, 0.4)
        if len(idxs) > 0:
            for i in idxs.flatten():
                x, y, bw, bh = boxes[i]
                cls = self.classes[cids[i]]
                if cls not in self.allowed_classes:
                    continue

                color = (0, 255, 0) if cls == self.target else (0, 0, 255)
                cv2.rectangle(frame, (x, y), (x + bw, y + bh), color, 2)
                cv2.putText(frame, f"{cls}:{confs[i]:.2f}", (x, y - 5),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

                ps = PoseStamped()
                ps.header = self.last_image.header
                ps.pose.position.x = x + bw / 2
                ps.pose.position.y = y + bh / 2
                ps.pose.orientation.w = 1.0
                if cls == self.target:
                    self.pub_goal.publish(ps)
                else:
                    self.pub_obs.publish(ps)

        msg = self.bridge.cv2_to_imgmsg(frame, encoding='bgr8')
        msg.header = self.last_image.header
        self.image_pub.publish(msg)

def main(args=None):
    rclpy.init(args=args)
    node = DetectionNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()

