"""게임오버 창: 플레이 화면 위에 push_mode로 띄운다"""
from pico2d import SDL_KEYDOWN, SDLK_ESCAPE, SDLK_RETURN, SDLK_SPACE

import game_framework
import play_mode
from ui import img, draw_tl, draw_number, Button

WINDOW = (288, 120)
retry_button = title_button = None
score = best = 0


def init():
    global retry_button, title_button, score, best
    retry_button = Button('buttons/btn_retry', WINDOW[0] + 24, WINDOW[1] + 336)
    title_button = Button('buttons/btn_title', WINDOW[0] + 352, WINDOW[1] + 336)
    score = play_mode.game.score
    best = play_mode.load_highscore()


def finish():
    pass


def pause():
    pass


def resume():
    pass


def handle_events(events):
    for event in events:
        if retry_button.handle_event(event) or (event.type == SDL_KEYDOWN and event.key in (SDLK_RETURN, SDLK_SPACE)):
            game_framework.change_mode(play_mode)
            return
        if title_button.handle_event(event) or (event.type == SDL_KEYDOWN and event.key == SDLK_ESCAPE):
            import title_mode
            game_framework.change_mode(title_mode)
            return


def update(dt):
    play_mode.game.mascot.update(dt)   # 실망한 마스코트는 계속 움직이게


def draw():
    draw_tl(img('windows/dim'), 0, 0)
    draw_tl(img('windows/gameover_window'), *WINDOW)
    draw_number('%06d' % min(score, 999999), WINDOW[0] + 344, WINDOW[1] + 156)
    draw_number('%06d' % min(best, 999999), WINDOW[0] + 344, WINDOW[1] + 228, yellow=True)
    retry_button.draw()
    title_button.draw()
