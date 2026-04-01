#!/usr/bin/env python3
"""
Send one PoseStamped to the fleet backend via RobotService.SendLocalization.
 
Requires backend navigation gRPC exposed (default host:50052), e.g. docker-compose maps 50052:50052.
 
Example:
  python3 inject_navigation_pose.py --host localhost --port 50052 --robot-id 1
"""
 
from __future__ import annotations
 
import argparse
import sys
import time
from pathlib import Path
 
_root = Path(__file__).resolve().parent
sys.path.insert(0, str(_root))
sys.path.insert(0, str(_root / "proto"))
 
import grpc  # noqa: E402
import navigation_pb2  # noqa: E402
import navigation_pb2_grpc  # noqa: E402
 
 
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", default="localhost", help="Fleet backend host")
    ap.add_argument("--port", type=int, default=50052, help="ROBOT_NAVIGATION_PORT (SendLocalization)")
    ap.add_argument("--robot-id", required=True, help="Must match sensor_store key (e.g. 1 or test-001)")
    args = ap.parse_args()
 
    target = f"{args.host}:{args.port}"
    msg = navigation_pb2.PoseStamped()
    msg.header.frame_id = "map"
    now = time.time()
    msg.header.sec = int(now)
    msg.header.nanosec = int((now - int(now)) * 1e9)
    msg.pose.position.x = 1.0
    msg.pose.position.y = 2.0
    msg.pose.position.z = 0.0
    msg.pose.orientation.w = 1.0
 
    ch = grpc.insecure_channel(target)
    stub = navigation_pb2_grpc.RobotServiceStub(ch)
    md = (("robot-id", str(args.robot_id)),)
    stub.SendLocalization(msg, metadata=md, timeout=5.0)
    print(f"OK SendLocalization -> {target} robot-id={args.robot_id}")
 
 
if __name__ == "__main__":
    main()