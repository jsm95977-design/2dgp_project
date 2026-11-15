"""지역 선택: 큐브마을 / 지구 / 우주 (UI_GUIDE.md의 '지역 선택')

- 잠긴 지역은 회색 아이콘·흐린 이름표이고 클릭해도 반응하지 않는다.
  앞 지역의 스테이지를 모두 깨면 다음 지역이 열린다 (story_data.is_unlocked).
- 마우스를 올리면 _hover 아이콘. 이름표 아래에 깬 스테이지 수 (★ 12/30).
- F1: 마우스가 올라간 지역은 잠겨 있어도 스테이지 선택으로 들어간다 (맵 편집용).
"""
from pico2d import SDL_KEYDOWN, SDLK_ESCAPE, SDLK_F1, SDL_MOUSEMOTION, SDL_MOUSEBUTTONDOWN, SDL_BUTTON_LEFT

import game_framework
import stage_data
import story_data
from settings import HEIGHT
from ui import img, draw_tl, draw_text, inside, Button

ICON = 192
ICON_POS = {'village': (144, 256), 'earth': (544, 224), 'space': (944, 256)}
NAME_POS = {'village': (114, 460), 'earth': (560, 428), 'space': (960, 460)}
TITLE_POS = (432, 40)
DIGIT_W, DIGIT_H = 28, 36
DIGITS = '0123456789+x/'

back_button = None
hover = None          # 마우스가 올라간 지역 번호
cleared = []


def region_at(x, y):
    for i, region in enumerate(story_data.REGIONS):
        if inside(x, y, *ICON_POS[region['key']], ICON, ICON):
            return i
    return None


def unlocked(i):
    return story_data.is_unlocked(i, cleared)


def open_region(i):
    import stage_select_mode
    stage_select_mode.region = i
    game_framework.change_mode(stage_select_mode)


def go_back():
    import mode_select_mode
    game_framework.change_mode(mode_select_mode)


def init():
    global back_button, hover, cleared
    back_button = Button('buttons/icon_back', 16, 16, hit_h=64)
    hover = None
    cleared = story_data.cleared_counts(stage_data.load_progress())


def finish():
    pass


def pause():
    pass


def resume():
    pass


def handle_events(events):
    global hover
    for event in events:
        if event.type == SDL_KEYDOWN and event.key == SDLK_ESCAPE:
            go_back()
            return
        if event.type == SDL_KEYDOWN and event.key == SDLK_F1 and hover is not None:
            open_region(hover)       # 편집용: 잠긴 지역도 들어간다
            return
        if back_button.handle_event(event):
            go_back()
            return
        if event.type == SDL_MOUSEMOTION:
            hover = region_at(event.x, event.y)
        elif event.type == SDL_MOUSEBUTTONDOWN and event.button == SDL_BUTTON_LEFT:
            i = region_at(event.x, event.y)
            if i is not None and unlocked(i):
                open_region(i)
                return


def update(dt):
    pass


def draw_small_number(text, left, top):
    digits = img('region/digits_small')
    for n, ch in enumerate(text):
        k = DIGITS.index(ch)
        digits.clip_draw(k * DIGIT_W, 0, DIGIT_W, DIGIT_H, left + n * DIGIT_W + DIGIT_W / 2, HEIGHT - top - DIGIT_H / 2)


def draw():
    draw_tl(img('region/region_select_bg'), 0, 0)
    draw_tl(img('region/title_region_select'), *TITLE_POS)
    back_button.draw()
    for i, region in enumerate(story_data.REGIONS):
        key = region['key']
        files = {k: v[:-4] for k, v in story_data.region_files(key).items()}
        open_ = unlocked(i)
        if not open_:
            icon = files['icon_locked']
        else:
            icon = files['icon_hover'] if hover == i else files['icon']
        draw_tl(img(icon), *ICON_POS[key])
        name_left, name_top = NAME_POS[key]
        draw_tl(img(files['name'] if open_ else files['name_locked']), name_left, name_top)
        if open_:   # 진행도: ★ 깬 수/전체
            text = '%d/%d' % (cleared[i], region['stages'])
            x0 = ICON_POS[key][0] + ICON // 2 - (DIGIT_W * len(text) + 36) // 2
            draw_tl(img('windows/star_small_full'), x0, name_top + 94)
            draw_small_number(text, x0 + 36, name_top + 94)
    draw_text('F1: 잠긴 지역도 들어가기 (맵 편집용)', 40, 680, 16, (220, 220, 240))
