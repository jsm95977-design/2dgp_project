"""스테이지 모드 오프닝 컷신 (처음 한 번만, UI_GUIDE.md의 '오프닝 컷신')

장면 그림 → 대사 상자 → (큐비 이름표) → 대사 → 다음 화살표 → 건너뛰기 순서로 그린다.
- 대사는 한 글자씩 나타난다. 다 나오기 전에 클릭하면 한 번에 다 보여 준다.
- 클릭 / 스페이스 / Enter: 다음 대사. 장면의 마지막 대사 다음에는 다음 장면 그림.
- 마지막 대사 다음, 또는 건너뛰기(버튼·ESC)를 누르면 본 것으로 기록하고 지역 선택으로 간다.
"""
from pico2d import SDL_KEYDOWN, SDLK_ESCAPE, SDLK_RETURN, SDLK_SPACE, SDL_MOUSEBUTTONDOWN, SDL_BUTTON_LEFT

import game_framework
import story_data
from settings import HEIGHT
from ui import img, draw_tl, draw_frame, font, Button

DIALOG_BOX = (32, 520)
NAME_PLATE = (64, 460)
TEXT_LEFT, TEXT_TOP, LINE_GAP = 84, 560, 52
TEXT_SIZE = 36                 # Galmuri11 12px 격자의 3배
NEXT_ARROW = (1168, 644)
ARROW_BLINK = 0.4
CHARS_PER_SEC = 30

scene_i = line_i = 0
shown_chars = 0.0
arrow_timer = 0.0
skip_button = None


def image_name(path):
    """story_data의 'story/scene_1.png' → img()용 'story/scene_1'"""
    return path[:-4] if path.endswith('.png') else path


def current_line():
    return story_data.OPENING[scene_i]['lines'][line_i]


def line_done():
    return shown_chars >= len(current_line()[1])


def advance():
    """클릭 한 번: 글자가 나오는 중이면 다 보여 주고, 다 나왔으면 다음 대사"""
    global scene_i, line_i, shown_chars
    if not line_done():
        shown_chars = len(current_line()[1])
        return
    line_i += 1
    if line_i >= len(story_data.OPENING[scene_i]['lines']):
        scene_i, line_i = scene_i + 1, 0
    shown_chars = 0.0
    if scene_i >= len(story_data.OPENING):
        finish_opening()


def finish_opening():
    story_data.mark_opening_seen()
    import region_select_mode
    game_framework.change_mode(region_select_mode)


def init():
    global scene_i, line_i, shown_chars, arrow_timer, skip_button
    scene_i = line_i = 0
    shown_chars = arrow_timer = 0.0
    skip_button = Button('story/btn_skip', 976, 24, hit_h=76)


def finish():
    pass


def pause():
    pass


def resume():
    pass


def handle_events(events):
    for event in events:
        if skip_button.handle_event(event) or (event.type == SDL_KEYDOWN and event.key == SDLK_ESCAPE):
            finish_opening()
            return
        clicked = event.type == SDL_MOUSEBUTTONDOWN and event.button == SDL_BUTTON_LEFT
        if clicked or (event.type == SDL_KEYDOWN and event.key in (SDLK_SPACE, SDLK_RETURN)):
            advance()
            if game_framework.stack[-1] is not this_module():
                return


def this_module():
    import sys
    return sys.modules[__name__]


def update(dt):
    global shown_chars, arrow_timer
    shown_chars = min(len(current_line()[1]), shown_chars + CHARS_PER_SEC * dt)
    arrow_timer += dt


def draw():
    scene = story_data.OPENING[scene_i]
    draw_tl(img(image_name(scene['image'])), 0, 0)
    draw_tl(img('story/dialog_box'), *DIALOG_BOX)
    who, text = current_line()
    if who in story_data.NAME_PLATES:
        draw_tl(img(image_name(story_data.NAME_PLATES[who])), *NAME_PLATE)

    f = font(TEXT_SIZE)
    if f:
        visible = text[:int(shown_chars)]
        for n, line in enumerate(visible.split('\n')):
            # font.draw의 y는 글자 세로 가운데 → 왼쪽 위 (L, T)는 H - T - 18
            f.draw(TEXT_LEFT, HEIGHT - (TEXT_TOP + LINE_GAP * n) - TEXT_SIZE // 2, line, (255, 255, 255))

    if line_done():   # 다 나왔을 때만 다음 화살표가 통통 튄다
        draw_frame(img('story/next_arrow'), int(arrow_timer / ARROW_BLINK) % 2, 36, 32, *NEXT_ARROW)
    skip_button.draw()
