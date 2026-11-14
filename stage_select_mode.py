"""스테이지 선택: 1~20 스테이지 타일 (한 줄에 7개, 3줄, 줄마다 가운데 정렬)"""
from pico2d import SDL_KEYDOWN, SDLK_ESCAPE, SDLK_F1, SDL_MOUSEMOTION, SDL_MOUSEBUTTONDOWN, SDL_BUTTON_LEFT

import game_framework
import stage_data
from ui import img, draw_tl, draw_number, draw_text, inside, Button

STAGE_COUNT = 20
COLUMNS = 7
TILE = 104
GRID_TOP = 150                     # 첫 줄 타일 위쪽
PITCH_X, PITCH_Y = 152, 170        # 타일 간격 (세로: 타일 104 + 별 28 + 여백)
TITLE_POS = (360, 24)

back_button = None
hover_stage = None
selected_stage = None


def tile_tl(stage):
    row, col = divmod(stage - 1, COLUMNS)
    in_row = min(COLUMNS, STAGE_COUNT - row * COLUMNS)   # 이 줄의 타일 수 (마지막 줄은 6개)
    row_width = PITCH_X * (in_row - 1) + TILE
    return (1280 - row_width) // 2 + PITCH_X * col, GRID_TOP + PITCH_Y * row


def stage_at(x, y):
    for stage in range(1, STAGE_COUNT + 1):
        if inside(x, y, *tile_tl(stage), TILE, TILE):
            return stage
    return None


def is_unlocked(stage):
    return True    # 진행 저장이 생기면 클리어한 다음 스테이지까지만 열기


def stars(stage):
    return 0       # 스테이지 기록이 생기면 얻은 별 수 (0~3)


def start_stage(stage):
    """스테이지 플레이는 아직 없으므로 선택만 표시한다"""
    global selected_stage
    selected_stage = stage


def go_back():
    import mode_select_mode
    game_framework.change_mode(mode_select_mode)


def open_editor():
    """F1: 선택한 스테이지(없으면 마우스가 올라간 스테이지, 그것도 없으면 1)를 편집"""
    import stage_edit_mode
    stage_edit_mode.stage = selected_stage or hover_stage or 1
    game_framework.change_mode(stage_edit_mode)


edited_stages = set()


def init():
    global back_button, hover_stage, edited_stages
    back_button = Button('buttons/icon_back', 16, 16, hit_h=64)
    hover_stage = None    # selected_stage는 편집 모드에 다녀와도 유지
    edited_stages = set(stage_data.load_all())


def finish():
    pass


def pause():
    pass


def resume():
    pass


def handle_events(events):
    global hover_stage
    for event in events:
        if event.type == SDL_KEYDOWN and event.key == SDLK_ESCAPE:
            go_back()
            return
        if event.type == SDL_KEYDOWN and event.key == SDLK_F1:
            open_editor()
            return
        if back_button.handle_event(event):
            go_back()
            return
        if event.type == SDL_MOUSEMOTION:
            hover_stage = stage_at(event.x, event.y)
        elif event.type == SDL_MOUSEBUTTONDOWN and event.button == SDL_BUTTON_LEFT:
            stage = stage_at(event.x, event.y)
            if stage and is_unlocked(stage):
                start_stage(stage)


def update(dt):
    pass


def draw():
    draw_tl(img('board/play_bg'), 0, 0)
    draw_tl(img('windows/title_stage_select'), *TITLE_POS)
    back_button.draw()
    draw_text('F1 : 편집 모드 (스테이지를 클릭해 고른 뒤)', 40, 672, 18)
    for stage in range(1, STAGE_COUNT + 1):
        left, top = tile_tl(stage)
        if not is_unlocked(stage):
            draw_tl(img('windows/stage_tile_locked'), left, top)
            continue
        active = stage in (hover_stage, selected_stage)
        draw_tl(img('windows/stage_tile_hover' if active else 'windows/stage_tile'), left, top)
        text = str(stage)
        draw_number(text, left + (TILE - 36 * len(text)) / 2, top + 28)
        for k in range(3):   # 별 3개 (28x28), 타일 아래 가운데
            star = img('windows/star_small_full' if k < stars(stage) else 'windows/star_small_empty')
            draw_tl(star, left + 4 + 34 * k, top + TILE + 2)
