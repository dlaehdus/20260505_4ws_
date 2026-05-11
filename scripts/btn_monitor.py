#!/usr/bin/env python3

# 1. 파이썬 파일 실행 권한 부여
    # 터미널을 열고 파일에 실행 권한을 줍니다.
    # chmod +x /home/gadget/dev/repos/ros2_doyeon/scripts/btn_monitor.py
# 2. 자동 로그인 설정 (비밀번호 생략)
# 제슨 올인(Ubuntu) 환경에서 화면 잠금을 풀지 않아도 프로그램이 돌아가게 하려면 자동 로그인이 필수입니다.
    # Settings (설정) -> Users (사용자)로 이동합니다.
    # 오른쪽 상단의 Unlock 버튼을 눌러 비밀번호를 입력합니다.
    # Automatic Login 스위치를 ON으로 켭니다.
# 3. 시작 애플리케이션에 등록 (핵심)
# 부팅 직후 터미널을 열지 않아도 백그라운드에서 버튼 신호를 기다리게 만듭니다.
    # 메뉴에서 Startup Applications (시작 애플리케이션)를 실행합니다.
    # Add 버튼을 누르고 아래와 같이 입력합니다.
        # Name: DYNAMIXEL Button Monitor
        # Command: python3 /home/gadget/dev/repos/ros2_doyeon/scripts/btn_monitor.py
        # Comment: ROS2 Toggle with CM-900 Button
    # Save를 눌러 저장합니다.



import time
import subprocess
import signal
import os
from dynamixel_sdk import *

# --- 설정 ---
ADDR_BUTTON = 26
BAUDRATE = 57600
DEVICENAME = '/dev/serial/by-id/usb-CM-900_ROBOTIS_Virtual_COM_Port-if00'
PROTOCOL_VERSION = 2.0 
CONTROLLER_ID = 200

# 실행할 명령어 정의 (ROS2 빌드 및 런치)
# .bashrc의 doyeon() 함수를 직접 호출하기보다 경로를 명시하는 것이 정확합니다.
LAUNCH_COMMAND = (
    "source /opt/ros/humble/setup.bash && " # 본인의 ROS 버전에 맞게 수정 (foxy, humble 등)
    "cd /home/gadget/dev/repos/ros2_doyeon && "
    "colcon build --packages-select four_wheel_robot && "
    "source install/local_setup.bash && "
    "ros2 launch four_wheel_robot four_wheel_robot.launch.py"
)

portHandler = PortHandler(DEVICENAME)
packetHandler = PacketHandler(PROTOCOL_VERSION)

class ROSLauncher:
    def __init__(self):
        self.process = None

    def toggle(self):
        if self.process is None or self.process.poll() is not None:
            # 프로세스가 없거나 종료된 상태 -> 실행
            print("[시스템] ROS 2 빌드 및 실행을 시작합니다...")
            # shell=True와 preexec_fn을 사용하여 프로세스 그룹 전체를 제어할 수 있게 합니다.
            self.process = subprocess.Popen(
                LAUNCH_COMMAND, 
                shell=True, 
                executable="/bin/bash",
                preexec_fn=os.setsid 
            )
        else:
            # 프로세스가 실행 중 -> 종료
            print("[시스템] 프로세스를 종료합니다.")
            os.killpg(os.getpgid(self.process.pid), signal.SIGINT) # 그룹 전체 종료 (Ctrl+C 효과)
            self.process = None

def test_button():
    if not portHandler.openPort():
        print("포트를 열 수 없습니다.")
        return
    if not portHandler.setBaudRate(BAUDRATE):
        print("보드레이트 설정 실패.")
        return

    launcher = ROSLauncher()
    last_state = 0
    print("준비 완료. 버튼을 눌러 제어하세요.")
    
    try:
        while True:
            btn_state, dxl_result, dxl_error = packetHandler.read1ByteTxRx(portHandler, CONTROLLER_ID, ADDR_BUTTON)
            
            if dxl_result == COMM_SUCCESS:
                # 버튼을 누르는 순간(Rising Edge)에만 동작
                if btn_state == 1 and last_state == 0:
                    launcher.toggle()
                last_state = btn_state
            
            time.sleep(0.1) # CPU 점유율 방지

    except KeyboardInterrupt:
        if launcher.process:
            os.killpg(os.getpgid(launcher.process.pid), signal.SIGINT)
        portHandler.closePort()

if __name__ == '__main__':
    test_button()


