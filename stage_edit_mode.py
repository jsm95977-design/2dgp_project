"""스테이지 편집 모드: 스테이지 선택 화면에서 F1로 들어온다.

- 말풍선 입력칸을 클릭하면 스테이지 대사를 쓸 수 있다 (한글 가능, Enter/ESC/바깥 클릭으로 끝).
- 8x8 보드에 블록(6색)·방해 블록(내구도 1~3)·특수 블록(강철·폭탄·해·달)을 칠하고,
  턴 제한·목표 줄 수를 정한다.
- 바꿀 때마다 stages.json에 바로 저장되어 게임을 껐다 켜도 남는다.
- F1 / ESC / 뒤로 버튼으로 스테이지 선택 화면에 돌아간다.
"""
from pico2d import *

import game_framework
import stage_data
import story_data
from config import COLORS, BOARD_SIZE
from settings import HEIGHT
from cell_view import draw_cell
from input_events import start_text_input, stop_text_input
from ui import fill_tl, text_width, img, draw_tl, draw_number, draw_text, inside, Button

BOARD_POS = (650, 60)
CELL0 = (694, 104)
CELL = 64

# 도구: (이름, 칸 값). 숫자 키 1~0 순서와 같다
TOOLS = [(color, ('block', color)) for color in COLORS] + \
        [('방해1', ('obstacle', 1)), ('방해2', ('obstacle', 2)), ('방해3', ('obstacle', 3)), ('지우개', None)] +         [('강철', ('steel', 0)), ('폭탄 3턴', ('bomb', 3)), ('폭탄 2턴', ('bomb', 2)), ('폭탄 1턴', ('bomb', 1)),
         ('해', ('sun', 0)), ('달', ('moon', 0))]      # 특수 블록은 클릭으로만 고른다
TOOL_HELP = {
    'steel': '절대 안 깨짐. 강철이 있는 가로·세로 줄은 지울 수 없다',
    'bomb': '턴마다 숫자가 줄고 0이면 주변 3x3 블록을 없앤다 (점수 없음)',
    'sun': '주변 8칸을 채우면 활성화, 그 뒤 해가 든 줄을 지우면 획득',
    'moon': '든 줄을 3번 지우면 보름달, 그 뒤 한 번 더 지우면 획득',
}
TOOL_KEYS = [SDLK_1, SDLK_2, SDLK_3, SDLK_4, SDLK_5, SDLK_6, SDLK_7, SDLK_8, SDLK_9, SDLK_0]
COLOR_NAMES = stage_data.COLOR_NAMES

PANEL = (24, 104, 600, 536)          # 왼쪽 패널 (왼쪽, 위, 너비, 높이)
TOOL0, TOOL_PITCH = (56, 176), (68, 92)   # 도구 칸 첫 위치와 가로·세로 간격
TOOLS_PER_ROW = 8
SETTING_TOP, SETTING_GAP = 432, 48   # 설정 줄: 턴 제한 / 목표 종류 / 목표 양 (+ 색)
ARROW_L, ARROW_R, VALUE_CENTER = 200, 420, 330
COLOR_ARROWS = (478, 576)            # 색 목표일 때 오른쪽 색 고르기 화살표
MESSAGE_BOX = (150, 578, 450, 36)    # 말풍선 대사 입력칸 (왼쪽, 위, 너비, 높이)

stage = 1
data = None
tool = 0
painting = None      # 마우스를 누른 채 칠하는 중이면 칠할 값 ('erase'는 지우기)
back_button = None
saved_timer = 0.0
anim_time = 0.0      # 특수 블록 애니메이션용
editing = False      # 말풍선 대사를 입력하는 중
composing = ''       # 한글 입력기에서 조합 중인 글자 (아직 확정 전)


def cell_tl(r, c):
    return CELL0[0] + CELL * c, CELL0[1] + CELL * r


def cell_at(x, y):
    c, r = (x - CELL0[0]) // CELL, (y - CELL0[1]) // CELL
    if 0 <= r < BOARD_SIZE and 0 <= c < BOARD_SIZE:
        return r, c
    return None


def tool_tl(i):
    row, col = divmod(i, TOOLS_PER_ROW)
    return TOOL0[0] + TOOL_PITCH[0] * col, TOOL0[1] + TOOL_PITCH[1] * row


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
    """화살표 한 번. goal_type·goal_color는 목록을 돌고, 숫자는 범위 안에서 늘리고 줄인다"""
    if key == 'goal_type':
        types = stage_data.GOAL_TYPES
        data['goal_type'] = types[(types.index(data['goal_type']) + delta) % len(types)]
        data['goal'] = stage_data.GOAL_DEFAULTS[data['goal_type']]    # 종류가 바뀌면 기본 양으로
    elif key == 'goal_color':
        data['goal_color'] = COLORS[(COLORS.index(data['goal_color']) + delta) % len(COLORS)]
    else:
        if key == 'turns':
            low, high, step = *stage_data.TURNS_RANGE, 1
        else:
            goal_type = data['goal_type']
            low, high = stage_data.GOAL_RANGES[goal_type]
            step = stage_data.GOAL_STEPS[goal_type]
        value = stage_data.clamp(data[key] + delta * step, low, high)
        if value == data[key]:
            return
        data[key] = value
    save()


def setting_rows():
    """(설정 이름, 줄 위쪽) - 색 목표면 목표 양 줄 오른쪽에 색 고르기가 붙는다"""
    return [('turns', SETTING_TOP), ('goal_type', SETTING_TOP + SETTING_GAP), ('goal', SETTING_TOP + 2 * SETTING_GAP)]


def active_arrows():
    """지금 보이는 화살표 {(설정, -1/+1): (왼쪽, 위)}"""
    result = {}
    for key, top in setting_rows():
        result[(key, -1)] = (ARROW_L, top)
        result[(key, +1)] = (ARROW_R, top)
    if data['goal_type'] == 'color':
        top = SETTING_TOP + 2 * SETTING_GAP
        result[('goal_color', -1)] = (COLOR_ARROWS[0], top)
        result[('goal_color', +1)] = (COLOR_ARROWS[1], top)
    return result


def clear_board():
    data['cells'] = [[None] * BOARD_SIZE for _ in range(BOARD_SIZE)]
    save()


def start_editing():
    global editing, composing
    editing, composing = True, ''
    start_text_input()


def finish_editing():
    global editing, composing
    if editing:
        editing, composing = False, ''
        stop_text_input()


def type_text(text):
    message = (data['message'] + text)[:stage_data.MESSAGE_MAX]
    if message != data['message']:
        data['message'] = message
        save()


def handle_text_event(event):
    """입력 중일 때의 이벤트. 다른 단축키(숫자·Delete·F1)는 무시한다. 처리했으면 True"""
    global composing
    if event.type == SDL_TEXTINPUT:
        composing = ''
        type_text(event.text)
    elif event.type == SDL_TEXTEDITING:
        composing = event.text
    elif event.type == SDL_KEYDOWN:
        if event.key in (SDLK_RETURN, SDLK_KP_ENTER, SDLK_ESCAPE):
            finish_editing()
        elif event.key == SDLK_BACKSPACE and not composing:   # 조합 중에는 입력기가 지운다
            if data['message']:
                data['message'] = data['message'][:-1]
                save()
    elif event.type == SDL_MOUSEBUTTONDOWN and not inside(event.x, event.y, *MESSAGE_BOX):
        finish_editing()
        return False     # 바깥 클릭은 원래 동작(도구 고르기·칠하기)도 한다
    return True


def go_back():
    finish_editing()
    import stage_select_mode
    stage_select_mode.show(stage)     # 편집하던 스테이지가 든 지역으로 돌아간다


def init():
    global data, tool, painting, back_button, saved_timer
    data = stage_data.load(stage)
    tool, painting, saved_timer = 0, None, 0.0
    finish_editing()
    back_button = Button('buttons/icon_back', 16, 16, hit_h=64)


def finish():
    finish_editing()


def pause():
    pass


def resume():
    pass


def handle_events(events):
    global tool, painting
    for event in events:
        if editing and handle_text_event(event):
            continue
        if event.type in (SDL_TEXTINPUT, SDL_TEXTEDITING):
            continue
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
            if event.button == SDL_BUTTON_LEFT and inside(x, y, *MESSAGE_BOX):
                start_editing()
                continue
            picked = tool_at(x, y)
            if picked is not None and event.button == SDL_BUTTON_LEFT:
                tool = picked
                continue
            for (key, delta), (left, top) in active_arrows().items():
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
    global saved_timer, anim_time
    saved_timer = max(0.0, saved_timer - dt)
    anim_time += dt


def draw_cell_value(value, left, top):
    if value is None:
        draw_tl(img('board/cell_empty'), left, top)
    else:
        draw_cell(value, left, top, t=anim_time)


GOAL_AMOUNT_LABELS = {'lines': '줄 수', 'score': '점수', 'color': '블록 수', 'stones': '돌 수'}


def draw_settings():
    labels = {'turns': '턴 제한', 'goal_type': '목표', 'goal': GOAL_AMOUNT_LABELS[data['goal_type']]}
    arrows_now = active_arrows()
    for key, top in setting_rows():
        draw_text(labels[key], 56, top + 8, 24)
        draw_tl(img('cube/arrow_left'), *arrows_now[(key, -1)])
        draw_tl(img('cube/arrow_right'), *arrows_now[(key, +1)])
        if key == 'goal_type':
            text = stage_data.GOAL_NAMES[data['goal_type']]
            draw_text(text, VALUE_CENTER - text_width(text, 24) // 2, top + 8, 24, (255, 230, 120))
        else:
            text = str(data[key])
            draw_number(text, VALUE_CENTER - 18 * len(text), top, yellow=True)   # 두 화살표 사이 가운데
    if data['goal_type'] == 'color':      # 색 고르기: ◀ [블록] ▶
        top = SETTING_TOP + 2 * SETTING_GAP
        draw_tl(img('cube/arrow_left'), *arrows_now[('goal_color', -1)])
        draw_tl(img('hud/mini_' + data['goal_color']), COLOR_ARROWS[0] + 48, top - 4)
        draw_tl(img('cube/arrow_right'), *arrows_now[('goal_color', +1)])


def draw_message_box():
    left, top, w, h = MESSAGE_BOX
    draw_text('말풍선', 56, top + 8, 22)
    fill_tl(left, top, w, h, (255, 230, 120) if editing else (90, 84, 140))   # 테두리 (입력 중이면 노랑)
    fill_tl(left + 2, top + 2, w - 4, h - 4, (20, 18, 45))
    text = data['message'] + (composing if editing else '')
    if not text and not editing:
        draw_text('클릭해서 대사 입력 (최대 %d자)' % stage_data.MESSAGE_MAX, left + 12, top + 10, 18, (130, 126, 170))
    else:
        inner = w - 24 - 70
        shown = text
        while shown and text_width(shown, 18) > inner:   # 길면 끝부분만 보인다
            shown = shown[1:]
        draw_text(shown, left + 12, top + 10, 18)
        if editing and int(anim_time * 2) % 2 == 0:     # 깜빡이는 커서
            fill_tl(left + 12 + text_width(shown, 18) + 2, top + 9, 2, 22, (255, 230, 120))
    count = '%d/%d' % (len(data['message']), stage_data.MESSAGE_MAX)
    draw_text(count, left + w - 12 - text_width(count, 16), top + 12, 16, (150, 146, 190))


def draw():
    draw_tl(img('board/play_bg'), 0, 0)
    back_button.draw()
    region, local = story_data.region_of(stage)     # 예: 지구 3 (전체 번호 23)
    name = story_data.REGIONS[region]['name']
    draw_text(name, 104, 26, 36)
    number_left = 104 + text_width(name, 36) + 16
    draw_number(str(local), number_left, 22, yellow=True)
    draw_text('편집 모드', number_left + 36 * len(str(local)) + 24, 26, 36, (255, 230, 120))

    # 왼쪽 패널
    left, top, w, h = PANEL
    draw_rectangle(left, HEIGHT - top - h, left + w, HEIGHT - top, 36, 33, 72, 235, True)
    draw_rectangle(left, HEIGHT - top - h, left + w, HEIGHT - top, 20, 18, 45, 255)

    draw_text('도구 (클릭, 숫자 키 1~0)', 56, 128, 20)
    if saved_timer > 0:
        draw_text('자동 저장됨', 500, 128, 18, (140, 230, 140))
    for i, (name, value) in enumerate(TOOLS):
        x, y = tool_tl(i)
        draw_cell_value(value, x, y)
        if i == tool:
            draw_tl(img('cube/front_mark_0'), x, y)
        if i < len(TOOL_KEYS):
            draw_text('%d' % ((i + 1) % 10), x + 2, y + 66, 14, (200, 200, 230))
    draw_text('선택: ' + COLOR_NAMES.get(TOOLS[tool][0], TOOLS[tool][0]), 56, 376, 20, (255, 230, 120))
    value = TOOLS[tool][1]
    if value and value[0] in TOOL_HELP:
        draw_text(TOOL_HELP[value[0]], 56, 408, 16, (220, 220, 240))

    draw_settings()

    draw_message_box()
    draw_text('좌클릭·드래그 칠하기 · 우클릭 지우기 · Delete 전체 지우기 · F1/ESC 나가기', 40, 620, 16,
              (220, 220, 240))

    # 보드
    draw_tl(img('board/board'), *BOARD_POS)
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            value = data['cells'][r][c]
            if value is not None:
                draw_cell_value(value, *cell_tl(r, c))
