"""스테이지 편집 모드: 스테이지 선택 화면에서 F1로 들어온다.

- 8x8 보드에 블록(6색)·방해 블록(내구도 1~3)을 칠하고, 턴 제한·목표 줄 수를 정한다.
- 바꿀 때마다 stages.json에 바로 저장되어 게임을 껐다 켜도 남는다.
- F1 / ESC / 뒤로 버튼으로 스테이지 선택 화면에 돌아간다.
"""
from pico2d import *

import game_framework
import stage_data
from config import COLORS, BOARD_SIZE
from settings import HEIGHT
from ui import img, draw_tl, draw_number, draw_text, inside, Button

BOARD_POS = (650, 60)
CELL0 = (694, 104)
CELL = 64

# 도구: (이름, 칸 값). 숫자 키 1~0 순서와 같다
TOOLS = [(color, ('block', color)) for color in COLORS] + \
        [('방해1', ('obstacle', 1)), ('방해2', ('obstacle', 2)), ('방해3', ('obstacle', 3)), ('지우개', None)]
TOOL_KEYS = [SDLK_1, SDLK_2, SDLK_3, SDLK_4, SDLK_5, SDLK_6, SDLK_7, SDLK_8, SDLK_9, SDLK_0]
COLOR_NAMES = {'red': '빨강', 'orange': '주황', 'yellow': '노랑', 'green': '초록', 'blue': '파랑', 'white': '흰색'}

PANEL = (24, 104, 600, 536)          # 왼쪽 패널 (왼쪽, 위, 너비, 높이)
TOOL0, TOOL_PITCH = (56, 176), 92    # 도구 칸 첫 위치와 간격 (한 줄 5개, 2줄)
SETTING_TOP = 452                    # 턴 제한 줄 위치 (목표 줄은 +64)

stage = 1
data = None
tool = 0
painting = None      # 마우스를 누른 채 칠하는 중이면 칠할 값 ('erase'는 지우기)
back_button = None
arrows = {}          # (설정 이름, -1/+1) → 화살표 왼쪽 위
saved_timer = 0.0


def cell_tl(r, c):
    return CELL0[0] + CELL * c, CELL0[1] + CELL * r


def cell_at(x, y):
    c, r = (x - CELL0[0]) // CELL, (y - CELL0[1]) // CELL
    if 0 <= r < BOARD_SIZE and 0 <= c < BOARD_SIZE:
        return r, c
    return None


def tool_tl(i):
    return TOOL0[0] + TOOL_PITCH * (i % 5), TOOL0[1] + TOOL_PITCH * (i // 5)


def tool_at(x, y):
    for i in range(len(TOOLS)):
        if inside(x, y, *tool_tl(i), 64, 64):
            return i
    return None


def save():
    global saved_timer
    stage_data.save(stage, data)
    saved_timer = 1.5


def paint(x, y):
    cell = cell_at(x, y)
    if cell is None:
        return
    r, c = cell
    value = None if painting == 'erase' else painting
    if data['cells'][r][c] != value:
        data['cells'][r][c] = value
        save()


def change_setting(key, delta):
    low, high = stage_data.TURNS_RANGE if key == 'turns' else stage_data.GOAL_RANGE
    value = stage_data.clamp(data[key] + delta, low, high)
    if value != data[key]:
        data[key] = value
        save()


def clear_board():
    data['cells'] = [[None] * BOARD_SIZE for _ in range(BOARD_SIZE)]
    save()


def go_back():
    import stage_select_mode
    game_framework.change_mode(stage_select_mode)


def init():
    global data, tool, painting, back_button, saved_timer
    data = stage_data.load(stage)
    tool, painting, saved_timer = 0, None, 0.0
    back_button = Button('buttons/icon_back', 16, 16, hit_h=64)
    for i, key in enumerate(('turns', 'goal_lines')):
        top = SETTING_TOP + 64 * i
        arrows[(key, -1)] = (300, top)
        arrows[(key, +1)] = (436, top)


def finish():
    pass


def pause():
    pass


def resume():
    pass


def handle_events(events):
    global tool, painting
    for event in events:
        if event.type == SDL_KEYDOWN:
            if event.key in (SDLK_F1, SDLK_ESCAPE):
                go_back()
                return
            if event.key in TOOL_KEYS:
                tool = TOOL_KEYS.index(event.key)
            elif event.key == SDLK_DELETE:
                clear_board()
            continue

        if back_button.handle_event(event):
            go_back()
            return

        if event.type == SDL_MOUSEBUTTONDOWN:
            x, y = event.x, event.y
            picked = tool_at(x, y)
            if picked is not None and event.button == SDL_BUTTON_LEFT:
                tool = picked
                continue
            for (key, delta), (left, top) in arrows.items():
                if inside(x, y, left, top, 40, 40) and event.button == SDL_BUTTON_LEFT:
                    change_setting(key, delta)
                    break
            else:
                if cell_at(x, y):
                    painting = TOOLS[tool][1] if event.button == SDL_BUTTON_LEFT else 'erase'
                    if painting is None:
                        painting = 'erase'
                    paint(x, y)
        elif event.type == SDL_MOUSEMOTION and painting is not None:
            paint(event.x, event.y)
        elif event.type == SDL_MOUSEBUTTONUP:
            painting = None


def update(dt):
    global saved_timer
    saved_timer = max(0.0, saved_timer - dt)


def draw_cell_value(value, left, top):
    if value is None:
        draw_tl(img('board/cell_empty'), left, top)
    elif value[0] == 'block':
        draw_tl(img('board/block_' + value[1]), left, top)
    else:
        draw_tl(img('board/obstacle_hp%d' % value[1]), left, top)


def draw():
    draw_tl(img('board/play_bg'), 0, 0)
    back_button.draw()
    draw_text('스테이지', 104, 26, 30)
    draw_number(str(stage), 240, 22, yellow=True)
    draw_text('편집 모드', 330, 26, 30, (255, 230, 120))

    # 왼쪽 패널
    left, top, w, h = PANEL
    draw_rectangle(left, HEIGHT - top - h, left + w, HEIGHT - top, 36, 33, 72, 235, True)
    draw_rectangle(left, HEIGHT - top - h, left + w, HEIGHT - top, 20, 18, 45, 255)

    draw_text('도구 (숫자 키 1~0)', 56, 128, 20)
    if saved_timer > 0:
        draw_text('자동 저장됨', 500, 128, 18, (140, 230, 140))
    for i, (name, value) in enumerate(TOOLS):
        x, y = tool_tl(i)
        draw_cell_value(value, x, y)
        if i == tool:
            draw_tl(img('cube/front_mark_0'), x, y)
        draw_text('%d' % ((i + 1) % 10), x + 2, y + 66, 14, (200, 200, 230))
    draw_text('선택: ' + COLOR_NAMES.get(TOOLS[tool][0], TOOLS[tool][0]), 56, 376, 20, (255, 230, 120))

    draw_text('턴 제한', 56, SETTING_TOP + 8, 22)
    draw_text('목표 줄 삭제', 56, SETTING_TOP + 72, 22)
    for i, key in enumerate(('turns', 'goal_lines')):
        top = SETTING_TOP + 64 * i
        draw_tl(img('cube/arrow_left'), *arrows[(key, -1)])
        text = str(data[key])
        draw_number(text, 388 - 18 * len(text), top, yellow=True)   # 두 화살표 사이 가운데
        draw_tl(img('cube/arrow_right'), *arrows[(key, +1)])

    draw_text('좌클릭·드래그: 칠하기    우클릭: 지우기    Delete: 전체 지우기', 40, 580, 16, (220, 220, 240))
    draw_text('F1 / ESC: 나가기 (바꿀 때마다 자동 저장)', 40, 606, 16, (220, 220, 240))

    # 보드
    draw_tl(img('board/board'), *BOARD_POS)
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            value = data['cells'][r][c]
            if value is not None:
                draw_cell_value(value, *cell_tl(r, c))
