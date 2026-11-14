"""일시정지: 플레이 화면 위에 push_mode로 띄운다"""
from pico2d import SDL_KEYDOWN, SDLK_ESCAPE

import game_framework
from ui import img, draw_tl, Button

WINDOW = (400, 152)
resume_button = title_button = None


def init():
    global resume_button, title_button
    resume_button = Button('buttons/btn_resume', WINDOW[0] + 72, WINDOW[1] + 152)
    title_button = Button('buttons/btn_title', WINDOW[0] + 72, WINDOW[1] + 264)


def finish():
    pass


def pause():
    pass


def resume():
    pass


def handle_events(events):
    for event in events:
        if event.type == SDL_KEYDOWN and event.key == SDLK_ESCAPE:
            game_framework.pop_mode()
            return
        if resume_button.handle_event(event):
            game_framework.pop_mode()
            return
        if title_button.handle_event(event):
            import title_mode
            game_framework.change_mode(title_mode)
            return


def update(dt):
    pass


def draw():
    draw_tl(img('windows/dim'), 0, 0)
    draw_tl(img('windows/pause_window'), *WINDOW)
    resume_button.draw()
    title_button.draw()
