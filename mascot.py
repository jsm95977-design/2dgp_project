"""마스코트: 큐브 마술사(cube_magician_sheet.png)를 상황에 따라 다른 줄로 재생한다.
시트 줄: 0 대기(지팡이), 1 기쁨(큐브 마법), 2 초조(땀), 3 실망(게임오버)"""
import os

from pico2d import load_image

from character import FRAME_SIZE, FRAMES_PER_ACTION
from settings import HEIGHT

ROWS = {'idle': 0, 'happy': 1, 'nervous': 2, 'gameover': 3}
FPS = {'idle': 4, 'happy': 8, 'nervous': 7, 'gameover': 5}
HAPPY_TIME = 1.5
SHEET = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'cube_magician_sheet.png')


class Mascot:
    image = None

    def __init__(self, center_left, center_top, size):
        if Mascot.image is None:
            Mascot.image = load_image(SHEET)
        self.x, self.y = center_left, HEIGHT - center_top
        self.size = size
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

    def draw(self):
        row = ROWS[self.state]
        frame = int(self.frame_timer * FPS[self.state]) % FRAMES_PER_ACTION
        left, bottom = frame * FRAME_SIZE, (3 - row) * FRAME_SIZE
        self.image.clip_draw(left, bottom, FRAME_SIZE, FRAME_SIZE, self.x, self.y, self.size, self.size)
