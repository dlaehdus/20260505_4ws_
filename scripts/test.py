import time
from dynamixel_sdk import *

# --- 설정 (제공해주신 경로 사용) ---
ADDR_BUTTON = 26
BAUDRATE = 57600
DEVICENAME = '/dev/serial/by-id/usb-CM-900_ROBOTIS_Virtual_COM_Port-if00'
PROTOCOL_VERSION = 2.0 
CONTROLLER_ID = 200 # CM-900의 기본 ID

portHandler = PortHandler(DEVICENAME)
packetHandler = PacketHandler(PROTOCOL_VERSION)

def test_button():
    # 포트 열기
    if not portHandler.openPort():
        print("포트를 열 수 없습니다. 경로를 확인하세요.")
        return

    # 보드레이트 설정
    if not portHandler.setBaudRate(BAUDRATE):
        print("보드레이트 설정에 실패했습니다.")
        return

    print("연결 성공 버튼을 눌러보세요. (종료: Ctrl+C)")
    
    last_state = -1
    
    try:
        while True:
            # 버튼 데이터 읽기 (1바이트)
            # read1ByteTxRx(포트, ID, 주소)
            btn_state, dxl_result, dxl_error = packetHandler.read1ByteTxRx(portHandler, CONTROLLER_ID, ADDR_BUTTON)
            
            if dxl_result != COMM_SUCCESS:
                # 통신 실패 시 에러 출력 (연결 불량 등)
                pass 
            elif dxl_error != 0:
                pass
            else:
                # 상태가 변했을 때만 출력
                if btn_state != last_state:
                    if btn_state == 1:
                        print("🔴 [입력 발생] 버튼 누름!")
                    else:
                        print("⚪ [입력 해제] 버튼 뗌.")
                    last_state = btn_state
            
            time.sleep(0.05) # 50ms 간격으로 확인

    except KeyboardInterrupt:
        print("\n테스트를 종료합니다.")
        portHandler.closePort()

if __name__ == '__main__':
    test_button()