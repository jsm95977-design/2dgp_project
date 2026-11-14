"""타이틀: 로고, 천천히 돌아가는 큐브, 게임 시작 버튼"""
from pico2d import SDL_KEYDOWN, SDLK_ESCAPE, SDLK_RETURN, SDLK_SPACE

import game_framework
import play_mode
from cube_view import CubeView
from settings import HEIGHT
from ui import img, draw_tl, Button

CUBE_CENTER, CUBE_SCALE = (640, 400), 52
SPIN_SPEED = 0.5        # 라디안/초
TURN_INTERVAL = 1.4     # 이 간격마다 층 하나를 돌린다

start_button = None
cube_view = None
turn_timer = 0.0


def init():
    global start_button, cube_view, turn_timer
    start_button = Button('title/btn_start', 480, 548)
    cube_view = CubeView(center=(CUBE_CENTER[0], HEIGHT - CUBE_CENTER[1]), scale=CUBE_SCALE)
    cube_view.enabled = False
    cube_view.scramble(20)
    turn_timer = 0.0


def finish():
    global cube_view
    cube_view = None


def pause():
    pass


def resume():
    pass


def handle_events(events):
    for event in events:
        if event.type == SDL_KEYDOWN and event.key == SDLK_ESCAPE:
            game_framework.quit()
            return
        if start_button.handle_event(event) or (event.type == SDL_KEYDOWN and event.key in (SDLK_RETURN, SDLK_SPACE)):
            game_framework.change_mode(play_mode)
            return


def update(dt):
    global turn_timer
    cube_view.orbit(SPIN_SPEED * dt, 0)
    turn_timer += dt
    if turn_timer >= TURN_INTERVAL and not cube_view.busy:
        turn_timer = 0.0
        cube_view.queue_random_turns(1)
    cube_view.update(dt)


def draw():
    draw_tl(img('board/play_bg'), 0, 0)
    cube_view.draw()
    draw_tl(img('title/logo'), 280, 0)
    start_button.draw()
