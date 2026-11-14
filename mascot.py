"""마스코트: 고른 캐릭터(큐브봇·박스냥·젤리)의 픽셀 시트를 상황에 따라 재생한다.
시트는 상태마다 한 장(128x128 프레임 4개 가로): idle 평소, happy 줄 삭제, nervous 초조, gameover 게임오버"""
import characters
from settings import HEIGHT
from ui import img

FRAME = 128
FRAMES = 4
FPS = {'idle': 6, 'happy': 8, 'nervous': 8, 'gameover': 6}
HAPPY_TIME = 1.5


class Mascot:
    def __init__(self, center_left, center_top, size, key=None):
        self.x, self.y = center_left, HEIGHT - center_top
        self.size = size
        self.key = key or characters.load()
        self.color = None          # 젤리만 쓰는 색 (None이면 기본색)
        self.state = 'idle'
        self.frame_timer = 0.0
        self.happy_timer = 0.0
        self.nervous = False
        self.gameover = False

    def cheer(self):
        self.happy_timer = HAPPY_TIME

    def update(self, dt):
        self.happy_timer = max(0.0, self.happy_timer - dt)
        if self.gameover:
            state = 'gameover'
        elif self.happy_timer > 0:
            state = 'happy'
        elif self.nervous:
            state = 'nervous'
        else:
            state = 'idle'
        if state != self.state:
            self.state, self.frame_timer = state, 0.0
        self.frame_timer += dt

    def frame(self):
        n = int(self.frame_timer * FPS[self.state])
        if self.state == 'gameover':     # 게임오버는 쓰러진 뒤 마지막 두 프레임을 반복
            return n if n < FRAMES else FRAMES - 2 + n % 2
        return n % FRAMES

    def draw(self):
        sheet = img(characters.sheet_path(self.key, self.state, self.color))
        sheet.clip_draw(self.frame() * FRAME, 0, FRAME, FRAME, self.x, self.y, self.size, self.size)
