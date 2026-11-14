# 밸런스 수치 모음 (플레이테스트로 조정)
import os

COLORS = ('red', 'orange', 'yellow', 'green', 'blue', 'white')

BOARD_SIZE = 8
MIN_PIECE_CELLS = 3            # 이보다 작은 블록은 놓을 수 없다

# 점수
PLACE_SCORE = 10               # 블록 칸 수² × 10
LINE_SCORE = 100               # 동시 삭제 줄 수² × 100
COMBO_STEP = 0.5               # 연속 턴 삭제마다 배율 +0.5

# 회전 에너지 (무한 모드)
ENERGY_START = 20
ENERGY_MAX = 30
ENERGY_LOW = 5                 # 이하이면 경고(게이지 깜빡임, 마스코트 초조)
ENERGY_GAIN = {1: 5, 2: 12, 3: 20}   # 3줄 이상은 3과 같다

# 방해 블록
PASS_OBSTACLES = 2             # 패스 패널티
DURABLE_FROM_TURN = 21         # 이 턴부터 내구도 블록이 섞여 나온다
DURABLE_CHANCE = 0.3
NORMAL_HP, DURABLE_HP = 1, 2


def obstacles_for_turn(turn):
    if turn <= 10:
        return 1
    if turn <= 30:
        return 2
    return 3


def shuffles_for_turn(turn):
    return 2 if turn > 30 else 1


START_SCRAMBLE = 25            # 시작할 때 큐브를 섞는 횟수

HIGHSCORE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'highscore.txt')
