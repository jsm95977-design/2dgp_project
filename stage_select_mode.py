"""지역별 스테이지 선택 (UI_GUIDE.md의 '지역별 스테이지 선택')

- region(지역 번호)의 배경·이름표, 스테이지 타일을 한 줄에 10개씩 (큐브마을 20개, 지구·우주 30개)
- 타일 숫자는 지역 안 번호(1부터), 맵·기록은 전체 번호(story_data: 큐브마을 1~20, 지구 21~50 ...)
- 처음 클릭은 선택, 선택된 타일을 한 번 더 누르거나 Enter면 맵이 있을 때 플레이
- F1: 선택한(없으면 마우스가 올라간, 그것도 없으면 첫) 스테이지 편집
- 뒤로 / ESC: 지역 선택
"""
from pico2d import SDL_KEYDOWN, SDLK_ESCAPE, SDLK_F1, SDLK_RETURN, SDL_MOUSEMOTION, SDL_MOUSEBUTTONDOWN, SDL_BUTTON_LEFT

import game_framework
import stage_data
import story_data
from ui import img, draw_tl, draw_number, draw_hint_bar, inside, Button

COLUMNS = 10
TILE = 104
GRID_LEFT, GRID_TOP = 48, 216
PITCH_X, PITCH_Y = 120, 128
STARS_TOP = 90            # 타일 위쪽 기준 작은 별 위치 (타일 아래 테두리에 걸치게)
NAME_TOP = 40

region = 0                # 지역 번호 (story_data.REGIONS 순서)
back_button = None
hover_stage = None        # 전체 스테이지 번호
selected_stage = None
edited_stages = set()
progress = {}


def show(stage):
    """stage가 든 지역의 스테이지 선택 화면으로 가고, 그 스테이지를 선택해 둔다"""
    global region, selected_stage
    region = story_data.region_of(stage)[0]
    selected_stage = stage
    import sys
    game_framework.change_mode(sys.modules[__name__])


def stages():
    return story_data.stage_numbers(region)


def tile_tl(stage):
    i = stage - story_data.first_stage(region)
    return GRID_LEFT + PITCH_X * (i % COLUMNS), GRID_TOP + PITCH_Y * (i // COLUMNS)


def stage_at(x, y):
    for stage in stages():
        if inside(x, y, *tile_tl(stage), TILE, TILE):
            return stage
    return None


def is_unlocked(stage):
    return True    # 지역 안 스테이지는 모두 열려 있다 (지역 단위로 잠근다)


def stars(stage):
    """클리어 기록에 남은 별 수 (0~3)"""
    return progress.get(stage, {'stars': 0})['stars']


def click_stage(stage):
    """처음 클릭은 선택(F1 편집 대상), 선택된 스테이지를 한 번 더 누르면 맵이 있을 때 플레이"""
    global selected_stage
    if stage == selected_stage:
        play_stage(stage)
    else:
        selected_stage = stage


def play_stage(stage):
    if stage not in edited_stages:   # 맵이 없으면 플레이할 수 없다
        return
    import play_mode
    play_mode.stage = stage
    game_framework.change_mode(play_mode)


def go_back():
    import region_select_mode
    game_framework.change_mode(region_select_mode)


def open_editor():
    """F1: 선택한 스테이지(없으면 마우스가 올라간 스테이지, 그것도 없으면 지역 첫 스테이지)를 편집"""
    import stage_edit_mode
    stage_edit_mode.stage = selected_stage or hover_stage or story_data.first_stage(region)
    game_framework.change_mode(stage_edit_mode)


def init():
    global back_button, hover_stage, selected_stage, edited_stages, progress
    back_button = Button('buttons/icon_back', 16, 16, hit_h=64)
    hover_stage = None
    if selected_stage not in stages():    # 다른 지역에서 고른 스테이지는 잊는다
        selected_stage = None
    edited_stages = set(stage_data.load_all())
    progress = stage_data.load_progress()


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
        if event.type == SDL_KEYDOWN and event.key == SDLK_RETURN and selected_stage:
            play_stage(selected_stage)
            return
        if back_button.handle_event(event):
            go_back()
            return
        if event.type == SDL_MOUSEMOTION:
            hover_stage = stage_at(event.x, event.y)
        elif event.type == SDL_MOUSEBUTTONDOWN and event.button == SDL_BUTTON_LEFT:
            stage = stage_at(event.x, event.y)
            if stage and is_unlocked(stage):
                click_stage(stage)


def update(dt):
    pass


def draw():
    key = story_data.REGIONS[region]['key']
    draw_tl(img('region/bg_' + key), 0, 0)
    name = img('region/name_' + key)
    draw_tl(name, 640 - name.w // 2, NAME_TOP)
    back_button.draw()
    for stage in stages():
        left, top = tile_tl(stage)
        if not is_unlocked(stage):
            draw_tl(img('windows/stage_tile_locked'), left, top)
            continue
        active = stage in (hover_stage, selected_stage)
        draw_tl(img('windows/stage_tile_hover' if active else 'windows/stage_tile'), left, top)
        text = str(story_data.region_of(stage)[1])
        # 편집해 둔 맵이 있는 스테이지는 노란 숫자
        draw_number(text, left + (TILE - 36 * len(text)) / 2, top + 22, yellow=stage in edited_stages)
        for k in range(3):   # 별 3개 (28x28), 타일 아래 테두리에 걸치게
            star = img('windows/star_small_full' if k < stars(stage) else 'windows/star_small_empty')
            draw_tl(star, left + 4 + 34 * k, top + STARS_TOP)
    draw_hint_bar('클릭: 선택   한 번 더 클릭 / Enter: 플레이 (노란 번호 = 맵 있음)   F1: 편집 모드', 24, 672)
