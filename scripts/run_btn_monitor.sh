#!/bin/bash
# 5초 정도 대기 (시스템 서비스들이 완전히 로드될 시간을 줍니다)
sleep 5

# 1. ROS 2 Humble 기본 환경 로드
source /opt/ros/humble/setup.bash

# 2. 본인의 워크스페이스(colcon build 한 곳) 로드
# 만약 build/install 과정이 완료된 상태라면 아래 경로를 추가하세요.
source /home/gadget/dev/repos/ros2_doyeon/install/setup.bash

# 3. 파이썬 스크립트 실행
/usr/bin/python3 /home/gadget/dev/repos/ros2_doyeon/scripts/btn_monitor.py
