teleop_node.py

이 코드는 ROS 2 기반의 4축 조향(4WS, Four Wheel Steering) 로봇을 키보드로 실시간 제어하기 위한 텔레옵(teleoperation) 프로그램이다.
사용자가 키보드에서 W, A, S, D 키를 누르면 ROS 2의 cmd_vel 토픽으로 Twist 메시지를 발행하여 로봇의 선속도(linear velocity)와 각속도(angular velocity)를 제어한다. 동시에 Tkinter GUI를 이용해 현재 속도와 입력 상태를 실시간으로 시각화한다.

프로그램 구조는 크게 다음 5개 계층으로 구성된다.
ROS 2 통신 계층
키보드 입력 처리 계층
속도 생성 및 가감속 제어 계층
GUI 시각화 계층
멀티스레드 실행 계층
프로그램이 시작되면 먼저 ROS 2 노드인 four_wheel_steering_teleop을 생성한다. 이 노드는 ROS 2 네트워크 상에서 하나의 독립 실행 단위로 동작하며, 내부적으로 cmd_vel이라는 토픽에 Twist 메시지를 publish하는 역할을 한다.

Twist 메시지는 모바일 로봇에서 가장 표준적으로 사용하는 속도 명령 메시지이며 구조는 다음과 같다.
Twist
 ├── linear
 │    ├── x
 │    ├── y
 │    └── z
 └── angular
      ├── x
      ├── y
      └── z
이 코드에서는 실제로 다음 두 값만 사용한다.

linear.x → 전진/후진 속도
angular.z → 좌우 회전 속도

즉 차량 모델 기준으로 보면:
x축 → 전후 이동
z축 회전 → yaw 회전

그 다음 코드에서는 ROS 2 파라미터를 선언한다.
같은 부분은 ROS 2 런타임에서 동적으로 조정 가능한 설정값을 등록하는 과정이다.

즉 이 프로그램은:
최대 선속도
최대 회전속도
가속도
publish 주기
등을 런타임에서 변경할 수 있도록 설계되어 있다.

이 구조는 ROS 2의 중요한 특징 중 하나인 Parameter Server 구조를 활용한 것이다.
예를 들어 launch 파일에서:max_linear_speed: 2.0
처럼 바꾸면 코드 수정 없이 속도 특성을 변경 가능하다.

이후 create_publisher()를 이용해 cmd_vel 토픽 발행자를 만든다.
self.publisher = self.create_publisher(Twist, 'cmd_vel', 10)의 의미는:
메시지 타입:Twist
토픽 이름:cmd_vel
QoS queue depth:10
이다.
여기서 queue depth 10은 네트워크 지연이나 subscriber 처리 지연이 발생했을 때 최대 10개의 메시지를 버퍼링하겠다는 의미다.

프로그램 내부에는 현재 속도와 목표 속도를 분리하는 중요한 제어 구조가 존재한다.
self.current_v
self.target_v

이 방식은 산업용 모션 제어에서 매우 흔히 사용하는 “속도 램핑(speed ramping)” 구조다.
만약 키를 누르자마자:0 → 1.0 m/s
로 순간 변화하면 실제 로봇에서는 다음 문제가 발생한다.
모터 과전류
기구 충격
슬립 발생
제어 불안정
감속기 백래시 충격
따라서 이 코드에서는 목표 속도(target)와 현재 속도(current)를 분리하고 _ramp() 함수로 천천히 접근시킨다.
즉 실제 속도 변화는:
0
0.02
0.04
0.06
...
1.0
처럼 부드럽게 증가한다. 이는 1차 시스템의 rate limiter와 거의 동일한 구조다.

키보드 입력은 pynput 라이브러리를 이용한다.
self.listener = keyboard.Listener(...)
부분이 백그라운드 스레드에서 키보드 이벤트를 감시한다.
사용자가:
w
a
s
d
를 누르면 해당 키를 set() 자료구조에 저장한다.
self.keys_pressed
는 현재 눌려 있는 키들의 집합이다.
예를 들어:W + A
를 동시에 누르면:{'w', 'a'}
가 저장된다.
이 구조 덕분에 대각선 이동이나 회전 조합이 가능하다.

그 다음 update_target() 함수에서 현재 눌린 키 상태를 바탕으로 목표 속도를 계산한다.
예를 들어:W
target_v = +max_v
target_w = 0
이 된다.

반대로:A
target_v = 0
target_w = +max_w
가 된다.

그리고:W + A
target_v = +max_v
target_w = +max_w
가 되어 전진하면서 좌회전하게 된다.
즉 차동구동 모바일 로봇의 기본 teleop 구조와 동일하다.

실제 주기 제어는 ROS 2 타이머로 수행된다.
self.timer = self.create_timer(1.0 / self.rate, self.update)
부분이 핵심이다.

만약 publish rate가 50Hz이면:주기 = 1 / 50 = 0.02초
즉 20ms마다 update() 함수가 자동 호출된다.
이 함수는 사실상 메인 제어 루프(control loop)다.

update() 함수 내부에서는 먼저 _ramp() 함수를 사용해 현재 속도를 목표 속도 방향으로 조금씩 이동시킨다.

이것은 다음 수식과 유사하다.
<img width="387" height="344" alt="image" src="https://github.com/user-attachments/assets/4e0a702d-2965-4a58-aeac-d561271b8acf" />


즉 이 코드는 단순 키보드 입력 프로그램이 아니라 실제 산업용 모션 제어에서 사용하는 가속도 제한 개념을 포함한 구조다.

속도 계산이 끝나면 Twist 메시지를 생성
twist.linear.x = self.current_v
twist.angular.z = self.current_w
를 설정하고:self.publisher.publish(twist)
를 통해 ROS 2 네트워크로 송신한다.

그러면:
Gazebo 시뮬레이터
실제 로봇 드라이버 노드
모터 제어 노드
등이 이 토픽을 subscribe하여 로봇을 움직이게 된다.

동시에 GUI도 갱신된다.

Tkinter를 이용해:
현재 선속도
현재 회전속도
눌린 키
현재 상태
를 실시간 표시한다.
예를 들어:
linear.x : 0.542 m/s
angular.z : 0.213 rad/s
같은 형태로 표시된다.

GUI와 ROS를 동시에 실행하기 위해 멀티스레드 구조를 사용한다.
ROS의:rclpy.spin(node)

은 블로킹 함수다.
즉 단독 실행 시 GUI가 멈춘다.
따라서 코드에서는:threading.Thread(target=ros_spin, daemon=True)
를 이용해 ROS를 별도 스레드에서 실행한다.

구조는 다음과 같다.
메인 스레드
 └── Tkinter GUI loop
백그라운드 스레드
 └── ROS 2 spin

이 방식 덕분에:
GUI 렌더링
키보드 입력
ROS 통신
이 동시에 동작한다.

프로그램 종료 시에는 on_closing() 함수가 호출된다.
이 함수는 매우 중요하다.
stop = Twist()
self.publisher.publish(stop)
를 수행하여 모든 속도를 0으로 만든다.
즉 로봇 정지 명령을 먼저 송신한다.
산업용 로봇에서 이런 “safe stop” 구조는 필수다.
만약 이 코드가 없다면:마지막 속도 명령 유지로봇 계속 주행runaway 상태가 발생할 수 있다.

결론적으로 이 프로그램은 단순 키보드 입력 코드가 아니라 다음 기술들이 결합된 ROS 2 기반 실시간 로봇 텔레옵 시스템이다.
Linux Event Input
+ ROS 2 Publisher
+ Real-time Control Loop
+ Velocity Ramp Generator
+ GUI Monitoring
+ Multithreading
+ Safe Shutdown
구조적으로는 실제 모바일 로봇 개발에서 사용하는 teleop architecture와 거의 동일한 설계다.

---------------------------------------------------------------------------------------------------------------------
kinematics_node.py

이 코드는 ROS 2 기반 4륜 독립 조향(4WIS, Four Wheel Independent Steering) 로봇의 핵심 기구학(Kinematics) 노드다.
역할은 매우 명확하다.
cmd_vel (속도 명령)
        ↓
차량 기구학 계산
        ↓
각 바퀴의:
- 조향각
- 구동 속도계산
        ↓
모터 제어기로 전달

즉 이 노드는 로봇의 “운동학 변환기(Kinematic Converter)”다.
조금 더 정확히 말하면:
차체 기준 속도(body velocity)→휠 단위 제어 명령(wheel command) 으로 변환하는 역할이다.

전체 시스템 구조
이 코드가 시스템에서 어디에 위치하는지 먼저 이해해야 한다.
전체 구조는 다음과 같다.
[사용자 키보드]
        ↓
Teleop Node
(cmd_vel publish)
        ↓
Kinematics Node  ← 현재 코드
        ↓
wheel_speeds
steering_angles
        ↓
모터 드라이버 노드
        ↓
실제 바퀴 회전

즉 이전에 작성한 teleop 노드는 단순히:
"앞으로 가라"
"좌회전해라"
같은 “차체 기준 명령”만 생성한다.

하지만 실제 로봇은:
앞왼쪽 바퀴 각도
앞오른쪽 바퀴 각도
뒤왼쪽 바퀴 각도
뒤오른쪽 바퀴 각도
를 각각 계산해야 움직일 수 있다.
그 계산을 수행하는 것이 이 Kinematics Node다.

이 코드의 핵심 기능
이 노드는 크게 4가지 역할을 수행한다.
1. cmd_vel 수신
2. Ackermann 기구학 계산
3. Dynamixel 조향값 변환
4. 휠 속도 계산 및 publish


1. cmd_vel 수신
먼저 이 노드는 ROS Subscriber를 생성한다.
self.subscription = self.create_subscription(
    Twist,
    'cmd_vel',
    self.vel_callback,
    10
)
cmd_vel 토픽을 계속 감시하다가
새로운 Twist 메시지가 오면
vel_callback() 실행

즉 teleop 노드에서:
twist.linear.x
twist.angular.z
를 publish하면 이 노드가 그것을 받아 처리한다.

2. 차체 속도 → 바퀴 기구학 변환
이 부분이 코드의 핵심이다.
입력값Teleop 노드로부터 들어오는 값은 단 두 개다.
v = msg.linear.x
w = msg.angular.z
즉:
전진 속도
회전 속도
뿐이다.
하지만 실제 4WS 차량은:
FL 조향각
FR 조향각
RL 조향각
RR 조향각
FL 속도
FR 속도
RL 속도
RR 속도
총 8개 명령이 필요하다.
따라서 이 노드는 차량 기구학 수식을 이용해 이를 계산한다.

차량 기하학
코드에서:
self.L = 0.685
self.W = 0.58719
는 차량 geometry다.
각 의미는:
L = Wheelbase (축거)
W = Track Width (윤거)
        Front
   FL -------- FR
      |      |
      |      |   ← L
      |      |
   RL -------- RR

        ← W →

직진 상황
만약:w == 0

이면 회전이 없는 상태다.
즉 차량이 직진 또는 후진 중이다.
이 경우: wheel_speeds = [speed] * 4
로 모든 바퀴 속도를 동일하게 설정한다.
그리고: steering_angles = initial_positions
로 모든 조향을 정면으로 맞춘다.
즉:
모든 바퀴 직진
모든 바퀴 같은 속도
가 된다.
가장 단순한 상태다.

회전 상황
블록부터 실제 Ackermann 기구학 계산이 시작된다

Ackermann Steering Geometry
자동차는 회전할때 모든 바퀴가 같은 각도로 꺾이면 안 된다.
왜냐하면 각 바퀴가 서로 다른 원 궤적을 따라가기 때문이다.
예를 들어 좌회전 시:
안쪽 바퀴:작은 원
바깥쪽 바퀴:큰 원
을 따라간다.

따라서:
안쪽 바퀴는 더 많이 꺾여야 하고
바깥쪽 바퀴는 덜 꺾여야 한다.
이 원리를 Ackermann Steering이라 한다.

<img width="573" height="505" alt="image" src="https://github.com/user-attachments/assets/53bdbbe3-1e32-4e81-ba5f-e890f0d98025" />


역상 조향의 장점
이 방식은:
회전반경 감소
제자리 회전에 가까운 기동
AGV/AMR에서 높은 기동성
을 얻을 수 있다.
즉 일반 자동차가 아니라:
자율주행 플랫폼
물류 로봇
AGV
에 가까운 구조다.


왜 바퀴 속도도 다르나?
회전 시 바깥쪽 바퀴는 더 긴 거리를 이동한다.
따라서 더 빠르게 회전해야 한다.
이를 위해:
<img width="245" height="95" alt="image" src="https://github.com/user-attachments/assets/20faaa32-62d9-4c04-948f-b07b82fb3645" />
바깥 바퀴:속도 증가
안쪽 바퀴:속도 감소

Dynamixel Tick 변환
조향 모터는 실제로 각도를 직접 받지 않는다.
Dynamixel은 내부적으로 encoder tick 기반 위치제어를 한다.
따라서:
조향각(rad)
→ degree
→ tick

Tick 변환
코드에서:self.TICKS_PER_DEG = 4096 / 360
<img width="404" height="121" alt="image" src="https://github.com/user-attachments/assets/f1c9012b-e0c7-4ca1-ab9b-f6d5819e31a7" />

초기 위치가 중요한 이유
self.initial_positions
는 각 모터의 기계적 영점(offset)이다.
실제 조립에서는:
혼 위치
기어 체결 위치
링크 길이
때문에 완벽한 중앙이 다 다르다.
따라서 각 바퀴마다 기준 tick을 따로 저장한다.
이것은 산업용 서보 시스템에서도 매우 일반적이다.



wheel_speeds[1] = -wheel_speeds[1]
wheel_speeds[2] = -wheel_speeds[2]
wheel speed 반전
이 부분:은 매우 현실적인 하드웨어 보정 코드다.
왜 필요하냐면:실제 좌우 모터는 물리적으로 반대 방향으로 설치되는 경우가 많다.
왼쪽 모터:
정방향 회전 = 전진
오른쪽 모터:
역방향 회전 = 전진

최종 Publish
최종적으로 이 노드는:
wheel_speeds
steering_angles
산업 관점에서 보면

이 구조는 실제:
AGV
AMR
물류로봇
자율주행 플랫폼
4WS 전기차
에서 사용하는 구조와 매우 유사하다.


--------------------------------------------------------------------------------------------------------------



























