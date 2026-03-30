import time
import grpc
from concurrent import futures

import navigation_pb2
import navigation_pb2_grpc


class RobotServiceServicer(navigation_pb2_grpc.RobotServiceServicer):

    # Stream goal xuống client
    def StreamGoal(self, request, context):
        while True:
            goal = navigation_pb2.PoseStamped(
                header=navigation_pb2.Header(
                    frame_id="3dmap",
                    sec=0,
                    nanosec=0
                ),
                pose=navigation_pb2.Pose(
                    position=navigation_pb2.Point(x=1.0, y=2.0, z=0.0),
                    orientation=navigation_pb2.Quaternion(x=0, y=0, z=0, w=1)
                )
            )

            print(">>> Send goal to client")
            yield goal
            time.sleep(3)

    # Nhận localization từ client
    def SendLocalization(self, request, context):
        print("<<< Received localization:")
        print(f"x={request.pose.position.x}, y={request.pose.position.y}")
        return navigation_pb2.Empty()


def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=5))
    navigation_pb2_grpc.add_RobotServiceServicer_to_server(
        RobotServiceServicer(), server
    )

    server.add_insecure_port('[::]:50051')
    server.start()

    print("🚀 Mock server running...")
    server.wait_for_termination()


if __name__ == '__main__':
    serve()