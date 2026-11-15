"""스테이지 클리어 창: 플레이 화면 위에 push_mode로 띄운다 (배치는 UI_GUIDE.md의 클리어 창)"""
from pico2d import SDL_KEYDOWN, SDLK_ESCAPE, SDLK_RETURN, SDLK_SPACE

import game_framework
import play_mode
import stage_data
from ui import img, draw_tl, draw_number, Button

WINDOW = (288, 120)
next_button = back_button = None
stars = score = 0
next_stage = None


def find_next_stage(stage):
    """다음 번호 중 맵이 있는 첫 스테이지 (없으면 None)"""
    stages = stage_data.load_all()
    later = [s for s in stages if s > stage]
    return min(later) if later else None


def init():
    global next_button, back_button, stars, score, next_stage
    game = play_mode.game
    stars, score = game.stars, game.score
    next_stage = find_next_stage(game.stage)
    next_button = Button('buttons/btn_next', WINDOW[0] + 144, WINDOW[1] + 336)
    next_button.enabled = next_stage is not None
    back_button = Button('buttons/icon_back', WINDOW[0] + 40, WINDOW[1] + 348, hit_h=64)


def finish():
    pass


def pause():
    pass


def resume():
    pass


def go_stage_select():
    import stage_select_mode
    stage_select_mode.show(play_mode.game.stage)     # 그 스테이지가 든 지역의 선택 화면


def handle_events(events):
    for event in events:
        go_next = next_button.handle_event(event) or \
            (event.type == SDL_KEYDOWN and event.key in (SDLK_RETURN, SDLK_SPACE) and next_stage)
        if go_next:
            play_mode.stage = next_stage
            game_framework.change_mode(play_mode)
            return
        if back_button.handle_event(event) or (event.type == SDL_KEYDOWN and event.key == SDLK_ESCAPE):
            go_stage_select()
            return


def update(dt):
    play_mode.game.mascot.update(dt)


def draw():
    left, top = WINDOW
    draw_tl(img('windows/dim'), 0, 0)
    draw_tl(img('windows/clear_window'), left, top)
    for i in range(3):
        draw_tl(img('windows/star_full' if i < stars else 'windows/star_empty'), left + 208 + 76 * i, top + 136)
    draw_number('%06d' % min(score, 999999), left + 344, top + 244)
    if next_button.enabled:   # 다음 스테이지 맵이 없으면 버튼을 숨긴다
        next_button.draw()
    back_button.draw()
