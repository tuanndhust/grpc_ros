import grpc
import threading
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import PoseStamped

from grpc_client_pkg import navigation_pb2
from grpc_client_pkg import navigation_pb2_grpc

class GRPCClientNode(Node):

    def __init__(self):
        super().__init__('grpc_client_node')

        # ===== gRPC =====
        self.channel = grpc.insecure_channel('localhost:50052')
        self.stub = navigation_pb2_grpc.RobotServiceStub(self.channel)

        # ===== ROS =====
        self.pub_goal = self.create_publisher(PoseStamped, '/goal_pose', 10)

        self.latest_pose = None
        self.sub_loc = self.create_subscription(
            PoseStamped,
            '/localization_3d',
            self.localization_callback,
            10
        )

        # send localization 
        self.timer = self.create_timer(1.0, self.send_localization)

        # receive goal stream in a separate thread
        threading.Thread(target=self.listen_goal_stream, daemon=True).start()

    # ===== ROS → Proto =====
    def ros_to_proto(self, msg):
        return navigation_pb2.PoseStamped(
            header=navigation_pb2.Header(
                frame_id=msg.header.frame_id,
                sec=msg.header.stamp.sec,
                nanosec=msg.header.stamp.nanosec
            ),
            pose=navigation_pb2.Pose(
                position=navigation_pb2.Point(
                    x=msg.pose.position.x,
                    y=msg.pose.position.y,
                    z=msg.pose.position.z
                ),
                orientation=navigation_pb2.Quaternion(
                    x=msg.pose.orientation.x,
                    y=msg.pose.orientation.y,
                    z=msg.pose.orientation.z,
                    w=msg.pose.orientation.w
                )
            )
        )

    # ===== Proto → ROS =====
    def proto_to_ros(self, msg):
        ros_msg = PoseStamped()
        ros_msg.header.frame_id = msg.header.frame_id
        ros_msg.header.stamp.sec = msg.header.sec
        ros_msg.header.stamp.nanosec = msg.header.nanosec

        ros_msg.pose.position.x = msg.pose.position.x
        ros_msg.pose.position.y = msg.pose.position.y
        ros_msg.pose.position.z = msg.pose.position.z

        ros_msg.pose.orientation.x = msg.pose.orientation.x
        ros_msg.pose.orientation.y = msg.pose.orientation.y
        ros_msg.pose.orientation.z = msg.pose.orientation.z
        ros_msg.pose.orientation.w = msg.pose.orientation.w

        return ros_msg

    def localization_callback(self, msg):
        self.latest_pose = msg

    def send_localization(self):
        self.get_logger().info("Sending localization...")
        if self.latest_pose is None:
            return

        try:
            proto_msg = self.ros_to_proto(self.latest_pose)
            md = (("robot-id", "1"),)  # example metadata, adjust as needed
            self.stub.SendLocalization(proto_msg, metadata=md   , timeout=5.0)
        except Exception as e:
            self.get_logger().error(f"SendLocalization error: {e}")

    def listen_goal_stream(self):
        self.get_logger().info("Received goal!")
        try:
            responses = self.stub.StreamGoal(navigation_pb2.Empty())

            for response in responses:
                ros_goal = self.proto_to_ros(response)
                self.pub_goal.publish(ros_goal)

        except Exception as e:
            self.get_logger().error(f"StreamGoal error: {e}")


def main():
    rclpy.init()
    node = GRPCClientNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()
