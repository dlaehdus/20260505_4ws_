#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import math

# ====================== 설정값 ======================
L = 0.685      # 축거 (y)
W = 0.58719    # 윤거 (x)

DXL_CENTER = 12285
TICKS_PER_DEG = 4096.0 / 360.0

SPEED_MAX = 100.0
SPEED_MIN = -100.0


def map_value(x, in_min, in_max, out_min, out_max):
    x = max(in_min, min(x, in_max))
    return out_min + (x - in_min) * (out_max - out_min) / (in_max - in_min)


def calculate_kinematics(v, w):
    print(f"\n{'='*95}")
    print(f"【 입력 】 v (linear.x) = {v:.4f} | w (angular.z) = {w:.4f}")
    print(f"{'='*95}")

    x = W
    y = L

    if w == 0:        # 직진 모드
        print("【 직진 모드 】")
        speed = map_value(v, -1.0, 1.0, SPEED_MIN, SPEED_MAX)
        dxl = float(DXL_CENTER)
        
        print(f"→ 모든 바퀴 동일 (Offset: 0)")
        wheel_speeds = [speed] * 4
        steering_angles = [int(dxl)] * 4
        offsets = [0] * 4

    else:                      # 회전 모드
        print("【 회전 모드 - 4WS Opposite Phase 】")
        
        alpha_deg = map_value(w, -1.0, 1.0, -45.0, 45.0)
        alpha_rad = math.radians(alpha_deg)
        
        print(f"1. alpha_deg     : {alpha_deg:8.3f} °")
        print(f"   alpha_rad     : {alpha_rad:8.4f} rad")


        R = abs((y/(2.0*math.tan(alpha_rad)))) + (x / 2.0)
        print(f"2. R (회전반경)  : {R:8.4f} m")

        speed = map_value(v, -1.0, 1.0, SPEED_MIN, SPEED_MAX)
        print('속도 맵핑',speed)
        # 조향각 계산
        if w > 0:   # 좌회전
            steer_fl_rad = alpha_rad
            steer_rl_rad = -alpha_rad
            steer_fr_rad = math.atan(y/((2*R)+x)) if (R + x/2.0) != 0 else alpha_rad
            steer_rr_rad = -steer_fr_rad
            # 속도 계산
            vel_fr = (speed * math.sqrt((R + x/2.0)**2 + (y/2.0)**2))/R if R != 0 else speed
            vel_fl = (speed * math.sqrt((R - x/2.0)**2 + (y/2.0)**2))/R if R != 0 else speed
        else:       # 우회전
            steer_fr_rad = alpha_rad
            steer_rr_rad = -alpha_rad
            steer_rl_rad = math.atan(y/((2*R)+x)) if (R + x/2.0) != 0 else alpha_rad
            steer_fl_rad = -steer_rl_rad
            # 속도 계산
            vel_fl = (speed * math.sqrt((R + x/2.0)**2 + (y/2.0)**2))/R if R != 0 else speed
            vel_fr = (speed * math.sqrt((R - x/2.0)**2 + (y/2.0)**2))/R if R != 0 else speed

        print(f"\n3. DXL 변환 상세 (Center: {DXL_CENTER}):")
        
        def get_dxl_info(name, rad):
            deg = math.degrees(rad)
            deg_clamped = max(-45.0, min(45.0, deg))
            offset = deg_clamped * TICKS_PER_DEG
            final_dxl = DXL_CENTER + offset
            print(f"   {name:5}: {deg:7.2f}° -> Offset: {offset:+8.2f} -> Final: {int(round(final_dxl))}")
            return int(round(final_dxl)), int(round(offset))

        # 각 바퀴별 계산 및 출력
        fl_dxl, fl_off = get_dxl_info("FL(1)", steer_fl_rad)
        fr_dxl, fr_off = get_dxl_info("FR(2)", steer_fr_rad)
        rl_dxl, rl_off = get_dxl_info("RL(3)", steer_rl_rad)
        rr_dxl, rr_off = get_dxl_info("RR(4)", steer_rr_rad)

        steering_angles = [fl_dxl, fr_dxl, rl_dxl, rr_dxl]
        offsets = [fl_off, fr_off, rl_off, rr_off]
        
        wheel_speeds = [
            vel_fl,
            vel_fr,
            vel_fl,
            vel_fr
        ]

    # ==================== 최종 발행값 ====================
    print(f"\n【 최종 결과 요약 】")
    print(f"Wheel Speeds   : {wheel_speeds}")
    print(f"Steering DXL   : {steering_angles}")
    print(f"DXL Offsets    : [{offsets[0]:+5}, {offsets[1]:+5}, {offsets[2]:+5}, {offsets[3]:+5}] (Center: {DXL_CENTER})")
    print(f"{'='*95}")


# ====================== 실행 ======================
if __name__ == "__main__":
    print("4WS Kinematics 상세 Offset 계산 스크립트")
    print("v w 입력 (예: 0.5 0.2) → 종료: q\n")

    while True:
        try:
            user_input = input("v w → ").strip()
            if user_input.lower() in ['q', 'quit', 'exit']:
                break
            v, w = map(float, user_input.split())
            calculate_kinematics(v, w)
        except ValueError:
            print("입력 형식 오류! 예시: 0.5 0.3")
        except KeyboardInterrupt:
            break