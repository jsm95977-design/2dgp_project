from pico2d import *

from settings import WIDTH, HEIGHT

# 스프라이트 시트: 1024x1024, 4x4 칸 (한 칸 256x256)
# 한 줄(row)이 액션 하나, 각 줄에 프레임 4개
FRAME_SIZE = 256
FRAMES_PER_ACTION = 4
DRAW_SIZE = 200          # 화면에 그릴 크기
MOVE_SPEED = 300         # 이동 속도 (픽셀/초)
FRAME_TIME = 0.12        # 액션 프레임 한 장당 시간 (초)

ACTION_KEYS = {SDLK_1: 0, SDLK_2: 1, SDLK_3: 2, SDLK_4: 3}
MOVE_KEYS = {
    SDLK_RIGHT: (1, 0), SDLK_d: (1, 0),
    SDLK_LEFT: (-1, 0), SDLK_a: (-1, 0),
    SDLK_UP: (0, 1), SDLK_w: (0, 1),
    SDLK_DOWN: (0, -1), SDLK_s: (0, -1),
}


class Magician:
    def __init__(self):
        self.image = load_image('cube_magician_sheet.png')
        self.x, self.y = WIDTH // 2, HEIGHT // 2
        self.held_keys = set()
        self.face_left = False
        self.action = None       # None이면 기본 자세, 0~3이면 액션 재생 중
        self.frame_timer = 0.0

    def handle_event(self, event):
        if event.type == SDL_KEYDOWN:
            if event.key in ACTION_KEYS:
                self.start_action(ACTION_KEYS[event.key])
            elif event.key in MOVE_KEYS:
                self.held_keys.add(event.key)
        elif event.type == SDL_KEYUP:
            self.held_keys.discard(event.key)

    def start_action(self, action):
        self.action = action
        self.frame_timer = 0.0

    def update(self, dt):
        # 이동 (걷기 애니메이션 없이 위치만 이동)
        dir_x = sum(MOVE_KEYS[k][0] for k in self.held_keys)
        dir_y = sum(MOVE_KEYS[k][1] for k in self.held_keys)
        dir_x = clamp(-1, dir_x, 1)
        dir_y = clamp(-1, dir_y, 1)

        self.x += dir_x * MOVE_SPEED * dt
        self.y += dir_y * MOVE_SPEED * dt
        half = DRAW_SIZE // 2
        self.x = clamp(half, self.x, WIDTH - half)
        self.y = clamp(half, self.y, HEIGHT - half)

        if dir_x < 0:
            self.face_left = True
        elif dir_x > 0:
            self.face_left = False

        # 액션은 4프레임 한 번 재생 후 기본 자세로 복귀
        if self.action is not None:
            self.frame_timer += dt
            if self.frame_timer >= FRAME_TIME * FRAMES_PER_ACTION:
                self.action = None

    def draw(self):
        if self.action is None:
            row, frame = 0, 0
        else:
            row = self.action
            frame = min(int(self.frame_timer / FRAME_TIME), FRAMES_PER_ACTION - 1)

        # pico2d는 왼쪽 아래가 원점이라 위에서부터 row번째 줄의 bottom을 계산
        left = frame * FRAME_SIZE
        bottom = (3 - row) * FRAME_SIZE
        flip = 'h' if self.face_left else ''
        self.image.clip_composite_draw(left, bottom, FRAME_SIZE, FRAME_SIZE,
                                       0, flip, self.x, self.y, DRAW_SIZE, DRAW_SIZE)
