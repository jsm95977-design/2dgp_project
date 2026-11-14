"""타이틀: 로고, 천천히 돌아가는 큐브, 게임 시작 버튼, 캐릭터 선택"""
from pico2d import SDL_KEYDOWN, SDLK_ESCAPE, SDLK_RETURN, SDLK_SPACE, SDLK_LEFT, SDLK_RIGHT, SDL_MOUSEMOTION, SDL_MOUSEBUTTONDOWN, SDL_BUTTON_LEFT

import characters
import game_framework
import mode_select_mode
from cube_view import CubeView
from mascot import Mascot
from settings import HEIGHT
from ui import img, draw_tl, draw_tl_scaled, draw_text, inside, Button

CUBE_CENTER, CUBE_SCALE = (640, 400), 52
SPIN_SPEED = 0.5        # 라디안/초
TURN_INTERVAL = 1.4     # 이 간격마다 층 하나를 돌린다

# 캐릭터 선택: 오른쪽에 타일 3개, 고른 캐릭터는 왼쪽 언덕 위에 크게
CARD, CARD_GAP = 108, 10
CARDS_LEFT, CARDS_TOP = 900, 300
LABEL_COLOR = (40, 40, 90)
HERO_CENTER, HERO_SIZE = (190, 500), 220

start_button = None
cube_view = None
turn_timer = 0.0
selected = None
hover_key = None
hero = None
cards = {}


def card_tl(i):
    return CARDS_LEFT + (CARD + CARD_GAP) * i, CARDS_TOP


def card_at(x, y):
    for i, key in enumerate(characters.KEYS):
        if inside(x, y, *card_tl(i), CARD, CARD):
            return key
    return None


def choose(key):
    """캐릭터를 고르면 바로 저장하고, 왼쪽 큰 캐릭터를 바꿔 기뻐하게 한다"""
    global selected, hero
    selected = key
    characters.save(key)
    hero = Mascot(*HERO_CENTER, HERO_SIZE, key)
    hero.cheer()


def init():
    global start_button, cube_view, turn_timer, selected, hover_key, hero, cards
    start_button = Button('title/btn_start', 480, 548)
    cube_view = CubeView(center=(CUBE_CENTER[0], HEIGHT - CUBE_CENTER[1]), scale=CUBE_SCALE)
    cube_view.enabled = False
    cube_view.scramble(20)
    turn_timer = 0.0
    selected = characters.load()
    hover_key = None
    hero = Mascot(*HERO_CENTER, HERO_SIZE, selected)
    cards = {}
    for i, key in enumerate(characters.KEYS):
        left, top = card_tl(i)
        cards[key] = Mascot(left + CARD // 2, top + CARD // 2, CARD - 8, key)


def finish():
    global cube_view
    cube_view = None


def pause():
    pass


def resume():
    pass


def handle_events(events):
    global hover_key
    for event in events:
        if event.type == SDL_KEYDOWN and event.key == SDLK_ESCAPE:
            game_framework.quit()
            return
        if start_button.handle_event(event) or (event.type == SDL_KEYDOWN and event.key in (SDLK_RETURN, SDLK_SPACE)):
            game_framework.change_mode(mode_select_mode)
            return
        if event.type == SDL_KEYDOWN and event.key in (SDLK_LEFT, SDLK_RIGHT):
            choose(characters.step(selected, -1 if event.key == SDLK_LEFT else 1))
        elif event.type == SDL_MOUSEMOTION:
            hover_key = card_at(event.x, event.y)
        elif event.type == SDL_MOUSEBUTTONDOWN and event.button == SDL_BUTTON_LEFT:
            key = card_at(event.x, event.y)
            if key:
                choose(key)


def update(dt):
    global turn_timer
    cube_view.orbit(SPIN_SPEED * dt, 0)
    turn_timer += dt
    if turn_timer >= TURN_INTERVAL and not cube_view.busy:
        turn_timer = 0.0
        cube_view.queue_random_turns(1)
    cube_view.update(dt)
    hero.update(dt)
    for mascot in cards.values():
        mascot.update(dt)


def draw_character_select():
    draw_text('캐릭터 선택', CARDS_LEFT, CARDS_TOP - 36, 24, LABEL_COLOR)
    for i, key in enumerate(characters.KEYS):
        left, top = card_tl(i)
        active = key in (selected, hover_key)
        draw_tl_scaled(img('windows/stage_tile_hover' if active else 'windows/stage_tile'), left, top, CARD, CARD)
        cards[key].draw()
        name = characters.name_of(key)
        color = (200, 60, 40) if key == selected else LABEL_COLOR
        draw_text(name, left + CARD // 2 - 11 * len(name), top + CARD + 8, 22, color)
    draw_text('← → 또는 클릭', CARDS_LEFT, CARDS_TOP + CARD + 44, 18, LABEL_COLOR)


def draw():
    draw_tl(img('board/play_bg'), 0, 0)
    cube_view.draw()
    draw_tl(img('title/logo'), 280, 0)
    start_button.draw()
    hero.draw()
    draw_character_select()
