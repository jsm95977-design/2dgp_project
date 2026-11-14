"""모드 선택: 무한 모드 / 스테이지 모드"""
from pico2d import SDL_KEYDOWN, SDLK_ESCAPE

import game_framework
from mascot import Mascot
from ui import img, draw_tl, Button

BUTTON_LEFT = (1280 - 416) // 2
endless_button = stage_button = back_button = None
mascot = None


def go_back():
    import title_mode
    game_framework.change_mode(title_mode)


def init():
    global endless_button, stage_button, back_button, mascot
    endless_button = Button('buttons/btn_endless', BUTTON_LEFT, 340)
    stage_button = Button('buttons/btn_stage', BUTTON_LEFT, 476)
    back_button = Button('buttons/icon_back', 16, 16, hit_h=64)
    mascot = Mascot(1130, 560, 190)


def finish():
    pass


def pause():
    pass


def resume():
    pass


def handle_events(events):
    for event in events:
        if event.type == SDL_KEYDOWN and event.key == SDLK_ESCAPE:
            go_back()
            return
        if back_button.handle_event(event):
            go_back()
            return
        if endless_button.handle_event(event):
            import play_mode
            play_mode.stage = None     # 무한 모드
            game_framework.change_mode(play_mode)
            return
        if stage_button.handle_event(event):
            import stage_select_mode
            game_framework.change_mode(stage_select_mode)
            return


def update(dt):
    mascot.update(dt)


def draw():
    draw_tl(img('board/play_bg'), 0, 0)
    draw_tl(img('title/logo'), 280, 0)
    endless_button.draw()
    stage_button.draw()
    back_button.draw()
    mascot.draw()
