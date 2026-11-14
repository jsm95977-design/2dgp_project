"""플레이 화면 (무한 모드 / 스테이지 모드)

턴 상태 머신: rotate(회전·배치 입력) → clearing(줄 삭제 연출) → shuffling(방해 블록·자동 섞기) → rotate ...
게임 오버가 되면 over 상태에서 잠시 기다렸다가 gameover_mode를 띄운다.

스테이지 모드: 모듈 변수 stage에 스테이지 번호를 넣고 이 모드로 바꾸면 stages.json의 맵으로 시작한다.
- 판은 맵 그대로, 턴 제한 안에 목표 줄 수를 지우고 해·달을 모두 획득하면 클리어 (clear 상태 → stage_clear_mode)
- 특수 블록(강철·폭탄·해·달) 규칙은 board.py 참고
- 에너지 대신 턴마다 회전 STAGE_ROTATIONS회, 턴마다 생기는 방해 블록 없음 (패스 패널티는 있음)"""
import random

from pico2d import *

import config
import game_framework
import piece as piece_logic
import stage_data
from board import Board
from cell_view import draw_cell
from cube_view import CubeView, cross
from effect import SheetEffect, FloatingText
from mascot import Mascot
from settings import HEIGHT
from ui import img, draw_tl, draw_number, draw_text, inside, Button

# ---- 배치 (화면 왼쪽 위 기준, UI_GUIDE.md) ----
BOARD_POS = (650, 60)
CELL0 = (694, 104)          # 칸 (0, 0)의 왼쪽 위
CELL = 64
CUBE_AREA = (0, 92, 392, 464)   # 큐브 주변 왼쪽 빈 화면: 스티커는 층 회전, 빈 곳은 시점 돌리기
CUBE_CENTER = (216, 272)
CUBE_SCALE = 62
COLOR_PANEL = (400, 104)
PREVIEW_PANEL = (400, 296)
MASCOT_CENTER, MASCOT_SIZE = (528, 596), 150
GAUGE_POS = (16, 16)

STATE_ROTATE, STATE_CLEARING, STATE_SHUFFLING, STATE_OVER = 'rotate', 'clearing', 'shuffling', 'over'
STATE_CLEAR = 'clear'      # 스테이지 목표 달성
CLEAR_DELAY = 0.45
OVER_DELAY = 1.2

game = None
stage = None               # None이면 무한 모드, 번호면 그 스테이지


def cell_tl(r, c):
    return CELL0[0] + CELL * c, CELL0[1] + CELL * r


class Game:
    def __init__(self):
        self.board = Board()
        left, top, w, h = CUBE_AREA
        self.cube_view = CubeView(center=(CUBE_CENTER[0], HEIGHT - CUBE_CENTER[1]), scale=CUBE_SCALE,
                                  area=(left, HEIGHT - top - h, left + w, HEIGHT - top), allow_orbit=True,
                                  mark_images=[img('cube/front_mark_0'), img('cube/front_mark_1')])
        self.cube_view.scramble(config.START_SCRAMBLE)
        self.cube_view.on_turn = self.on_rotate

        self.mascot = Mascot(*MASCOT_CENTER, MASCOT_SIZE)
        self.effects = []
        self.pass_button = Button('buttons/btn_pass', 160, 560, has_disabled=True)
        self.pause_button = Button('buttons/icon_pause', 1208, 4, hit_h=64)
        self.ccw_button = Button('cube/rotate_ccw', 48, 568, hit_h=56)
        self.cw_button = Button('cube/rotate_cw', 104, 568, hit_h=56)

        self.energy = config.ENERGY_START
        self.score = 0
        self.turn = 0
        self.combo = 0
        self.color = None
        self.next_color = random.choice(config.COLORS)
        self.piece = []
        self.state = None
        self.state_timer = 0.0
        self.blink_timer = 0.0
        self.steel_hit = []        # 강철 때문에 못 지운 줄의 강철 칸 (잠깐 steel_hit로 그린다)
        self.steel_hit_timer = 0.0

        self.dragging = False
        self.mouse = (0, 0)
        self.drop_cell = None   # 드래그 중인 블록이 놓일 (r, c), 판 밖이면 None

        # 스테이지 모드
        self.stage = stage
        self.lines_total = 0    # 지금까지 지운 줄 수 (목표 판정)
        self.stars = 0
        if self.stage:
            data = stage_data.load(self.stage)
            self.board.cells = [list(row) for row in data['cells']]
            self.turn_limit = data['turns']
            self.goal_lines = data['goal_lines']
            self.board.activate_suns()    # 맵에서 이미 둘러싸인 해는 바로 활성화
            self.goal_specials = {kind: self.board.count(kind) for kind in ('sun', 'moon')}

        self.start_turn()

    def specials_left(self, kind):
        return self.board.count(kind)

    def goal_done(self):
        """스테이지 목표: 줄 수를 채우고, 맵의 해·달을 모두 획득"""
        return (self.lines_total >= self.goal_lines and
                self.specials_left('sun') == 0 and self.specials_left('moon') == 0)

    def turns_left(self):
        """이번 턴을 포함해 남은 턴 수 (스테이지 모드)"""
        return self.turn_limit - self.turn + 1

    # ---------- 턴 진행 ----------
    def start_turn(self):
        if self.stage and self.turn >= self.turn_limit:
            self.game_over()     # 턴을 다 썼는데 목표를 못 채움
            return
        self.turn += 1
        if self.stage:
            self.energy = config.STAGE_ROTATIONS   # 스테이지는 턴마다 회전 횟수가 다시 채워진다
        self.color, self.next_color = self.next_color, random.choice(config.COLORS)
        self.cube_view.highlight = self.color
        self.state = STATE_ROTATE
        self.refresh_piece()
        self.check_game_over()

    def refresh_piece(self):
        self.piece = piece_logic.extract(self.cube_view.front_grid(), self.color)   # 화면에 보이는 앞면

    def on_rotate(self):
        """플레이어 회전 1회가 끝났다"""
        self.energy = max(0, self.energy - 1)
        self.refresh_piece()
        if self.state == STATE_ROTATE:
            self.check_game_over()

    def piece_ready(self):
        return piece_logic.is_placeable(self.piece)

    def can_act(self):
        return self.state == STATE_ROTATE and not self.cube_view.busy

    def place_piece(self, r0, c0):
        board = self.board
        board.place(self.piece, r0, c0, self.color)
        for r, c in self.piece:
            left, top = cell_tl(r0 + r, c0 + c)
            self.effects.append(SheetEffect('fx/fx_place', 6, left - 16, top - 16))

        n = len(self.piece)
        gained = n * n * config.PLACE_SCORE
        # 순서: 배치 → 해 활성화 확인 → 줄 삭제 (활성화된 해가 바로 같은 줄 삭제로 획득될 수 있다)
        for r, c in board.activate_suns():
            left, top = cell_tl(r, c)
            self.effects.append(SheetEffect('special/fx_sunrise', 8, left - 64, top - 64, size=192, fps=12))
        self.steel_hit = board.steel_blocked()
        if self.steel_hit:
            self.steel_hit_timer = 0.4
        lines, removed, cracked = board.clear_lines()
        self.show_special_changes(board.last_specials)
        if lines:
            self.combo += 1
            multiplier = 1 + config.COMBO_STEP * (self.combo - 1)
            gained += int(lines * lines * config.LINE_SCORE * multiplier)
            self.lines_total += lines
            if not self.stage:
                self.energy = min(config.ENERGY_MAX, self.energy + config.ENERGY_GAIN[min(lines, 3)])
            for i, (r, c, color) in enumerate(removed):
                left, top = cell_tl(r, c)
                self.effects.append(SheetEffect('fx/fx_clear_' + color, 8, left - 16, top - 16, delay=0.01 * i))
            self.mascot.cheer()
            text = {2: 'fx/text_good', 3: 'fx/text_great'}.get(lines, 'fx/text_perfect' if lines >= 4 else None)
            if text:
                self.effects.append(FloatingText(950, 300, image_name=text, life=1.2))
            if self.combo >= 2:
                self.effects.append(FloatingText(950, 380, image_name='fx/text_combo', life=1.2))
        else:
            self.combo = 0

        self.score += gained
        left, top = cell_tl(r0, c0)
        self.effects.append(FloatingText(left + 32, top - 8, number='+%d' % gained, life=0.9))

        self.state, self.state_timer = STATE_CLEARING, CLEAR_DELAY

    def show_special_changes(self, specials):
        """줄 삭제로 달이 차오르거나 해·달을 획득했을 때 이펙트"""
        for r, c in specials['moon_up']:
            left, top = cell_tl(r, c)
            self.effects.append(SheetEffect('special/fx_moon_up', 6, left - 16, top - 16, size=96, fps=10))
        for r, c, kind in specials['collected']:
            left, top = cell_tl(r, c)
            name = 'special/fx_moon_collect' if kind == 'moon' else 'special/fx_sunrise'
            self.effects.append(SheetEffect(name, 8, left - 64, top - 64, size=192, fps=12))

    def pass_turn(self):
        if not self.can_act():
            return
        self.combo = 0
        self.end_turn(config.PASS_OBSTACLES)

    def end_turn(self, extra_obstacles=0):
        """정리: 폭탄 카운트다운 → 방해 블록 생성 → 큐브 자동 섞기. 섞기가 끝나면 다음 턴."""
        exploded, destroyed = self.board.tick_bombs()
        for r, c in exploded:
            left, top = cell_tl(r, c)
            self.effects.append(SheetEffect('special/fx_explosion', 8, left - 64, top - 64, size=192, fps=12))
        for i, (r, c, color) in enumerate(destroyed):   # 폭발로 사라진 블록 (점수 없음)
            left, top = cell_tl(r, c)
            self.effects.append(SheetEffect('fx/fx_clear_' + color, 8, left - 16, top - 16, delay=0.15 + 0.01 * i))
        count = (0 if self.stage else config.obstacles_for_turn(self.turn)) + extra_obstacles
        hps = [config.DURABLE_HP if self.turn >= config.DURABLE_FROM_TURN and random.random() < config.DURABLE_CHANCE
               else config.NORMAL_HP for _ in range(count)]
        for r, c in self.board.spawn_obstacles(hps):
            left, top = cell_tl(r, c)
            self.effects.append(SheetEffect('fx/fx_spawn', 6, left - 16, top - 16, fps=12))
        self.cube_view.queue_random_turns(config.shuffles_for_turn(self.turn))
        self.state = STATE_SHUFFLING

    def check_game_over(self):
        if not self.board.has_room_for_min_piece():
            self.game_over()
        elif not self.stage and self.energy <= 0 and not self.any_view_placeable():
            self.game_over()   # 스테이지는 회전을 다 써도 패스로 다음 턴에 다시 채워지므로 제외

    def any_view_placeable(self):
        """에너지가 없어도 시점은 돌릴 수 있으므로, 6면 x 4방향 중 놓을 수 있는 블록이 하나라도 있는지"""
        cube = self.cube_view.cube
        for normal in ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1)):
            right, up = [tuple(1 if i == k else 0 for i in range(3)) for k in range(3) if normal[k] == 0]
            if cross(right, up) != normal:   # 바깥에서 본 모양이 되도록 (뒤집힌 모양 방지)
                up = tuple(-v for v in up)
            grid = cube.face_grid(normal, right, up)
            for _ in range(4):
                cells = piece_logic.extract(grid, self.color)
                if piece_logic.is_placeable(cells) and self.board.fits_anywhere(cells):
                    return True
                grid = [list(row) for row in zip(*grid[::-1])]   # 90도 돌린 모양
        return False

    def game_over(self):
        self.state, self.state_timer = STATE_OVER, OVER_DELAY
        self.dragging = False
        self.mascot.gameover = True
        if self.stage:
            stage_data.record_result(self.stage, 0, self.score)
        else:
            save_highscore(self.score)

    def stage_clear(self):
        self.stars = config.stars_for(self.turn_limit - self.turn, self.turn_limit)
        self.state, self.state_timer = STATE_CLEAR, OVER_DELAY
        self.mascot.cheer()
        stage_data.record_result(self.stage, self.stars, self.score)

    # ---------- 입력 ----------
    def handle_event(self, event):
        if event.type == SDL_KEYDOWN:
            if event.key == SDLK_ESCAPE:
                open_pause()
            elif event.key == SDLK_p:
                self.pass_turn()
            elif event.key == SDLK_r:
                self.cube_view.reset_view()
            elif event.key in (SDLK_q, SDLK_e) and self.state == STATE_ROTATE:
                self.cube_view.rotate_front(event.key == SDLK_e)
            return

        if self.pause_button.handle_event(event):
            open_pause()
            return
        if self.pass_button.handle_event(event):
            self.pass_turn()
            return
        for button, clockwise in ((self.ccw_button, False), (self.cw_button, True)):
            if button.handle_event(event) and self.state == STATE_ROTATE:
                self.cube_view.rotate_front(clockwise)
                return

        if event.type in (SDL_MOUSEMOTION, SDL_MOUSEBUTTONDOWN, SDL_MOUSEBUTTONUP):
            self.mouse = event.x, event.y

        if event.type == SDL_MOUSEBUTTONDOWN and event.button == SDL_BUTTON_LEFT:
            if self.can_act() and self.piece_ready() and inside(*self.mouse, *PREVIEW_PANEL, 256, 240):
                self.dragging = True
                self.update_drop_cell()
                return
        elif event.type == SDL_MOUSEMOTION and self.dragging:
            self.update_drop_cell()
        elif event.type == SDL_MOUSEBUTTONUP and event.button == SDL_BUTTON_LEFT and self.dragging:
            self.dragging = False
            self.update_drop_cell()
            if self.drop_cell and self.state == STATE_ROTATE and self.board.can_place(self.piece, *self.drop_cell):
                self.place_piece(*self.drop_cell)
            return

        if not self.dragging:
            self.cube_view.handle_event(event)

    def piece_top_left(self):
        """드래그 중인 블록의 왼쪽 위 화면 좌표 (마우스가 블록 가운데)"""
        rows, cols = piece_logic.size(self.piece)
        return self.mouse[0] - cols * CELL / 2, self.mouse[1] - rows * CELL / 2

    def update_drop_cell(self):
        left, top = self.piece_top_left()
        r0 = round((top - CELL0[1]) / CELL)
        c0 = round((left - CELL0[0]) / CELL)
        on_board = any(self.board.inside(r0 + r, c0 + c) for r, c in self.piece)
        self.drop_cell = (r0, c0) if on_board else None

    # ---------- 업데이트 ----------
    def update(self, dt):
        self.blink_timer += dt
        self.steel_hit_timer = max(0.0, self.steel_hit_timer - dt)
        self.cube_view.enabled = self.state == STATE_ROTATE and self.energy > 0 and not self.dragging
        self.cube_view.update(dt)
        if self.state == STATE_ROTATE and not self.dragging:
            self.refresh_piece()   # 시점을 돌리면 보이는 앞면이 바뀌므로 매 프레임 다시 읽는다
        if self.stage:
            self.mascot.nervous = self.turns_left() <= 1 and not self.goal_done()
        else:
            self.mascot.nervous = self.energy <= config.ENERGY_LOW
        self.mascot.color = self.color    # 젤리는 이번 턴 지정 색으로 바뀐다
        self.mascot.update(dt)
        for effect in self.effects:
            effect.update(dt)
        self.effects = [e for e in self.effects if not e.done]

        self.pass_button.enabled = self.can_act()

        if self.state == STATE_CLEARING:
            self.state_timer -= dt
            if self.state_timer <= 0:
                if self.stage and self.goal_done():
                    self.stage_clear()
                else:
                    self.end_turn()
        elif self.state == STATE_SHUFFLING and not self.cube_view.busy:
            self.start_turn()
        elif self.state == STATE_OVER:
            self.state_timer -= dt
            if self.state_timer <= 0:
                self.state_timer = float('inf')
                import gameover_mode
                game_framework.push_mode(gameover_mode)
        elif self.state == STATE_CLEAR:
            self.state_timer -= dt
            if self.state_timer <= 0:
                self.state_timer = float('inf')
                import stage_clear_mode
                game_framework.push_mode(stage_clear_mode)

    # ---------- 그리기 ----------
    def draw(self):
        draw_tl(img('board/play_bg'), 0, 0)
        self.draw_board()
        self.draw_hud()
        self.cube_view.draw()
        self.ccw_button.draw()
        self.cw_button.draw()
        self.pass_button.draw()
        self.pause_button.draw()
        self.mascot.draw()
        if self.dragging:
            self.draw_drag()
        for effect in self.effects:
            effect.draw()

    def draw_board(self):
        draw_tl(img('board/board'), *BOARD_POS)
        for r in range(self.board.size):
            for c in range(self.board.size):
                draw_cell(self.board.cells[r][c], *cell_tl(r, c), t=self.blink_timer, phase=0.37 * (r + 2 * c),
                          hit=(r, c) in self.steel_hit and self.steel_hit_timer > 0)
        if self.dragging and self.drop_cell:
            ok = self.board.can_place(self.piece, *self.drop_cell)
            ghost = img('board/ghost' if ok else 'board/ghost_bad')
            r0, c0 = self.drop_cell
            for r, c in self.piece:
                if self.board.inside(r0 + r, c0 + c):
                    draw_tl(ghost, *cell_tl(r0 + r, c0 + c))

    def draw_hud(self):
        # 에너지 게이지 (스테이지는 이번 턴에 남은 회전 수)
        draw_tl(img('hud/energy_gauge'), *GAUGE_POS)
        low = self.energy <= (1 if self.stage else config.ENERGY_LOW)
        blink = low and int(self.blink_timer * 4) % 2 == 1
        seg = img('hud/energy_seg_blink' if blink else 'hud/energy_seg_low' if low else 'hud/energy_seg_full')
        for i in range(self.energy):
            draw_tl(seg, 80 + 16 * i, 32)

        # 점수 · 턴
        draw_tl(img('hud/score_panel'), 672, 4)
        draw_number('%06d' % min(self.score, 999999), 784, 16)
        draw_tl(img('hud/turn_panel'), 1024, 4)
        if self.stage:
            # 남은 턴 수, 게이지 오른쪽에 스테이지 번호·목표 진행
            draw_number(str(max(0, self.turns_left())), 1100, 16, yellow=self.turns_left() <= 2)
            draw_text('스테이지 %d   회전 %d/%d' % (self.stage, self.energy, config.STAGE_ROTATIONS),
                      260, 34, 20, (255, 230, 120))
            goal = '목표: 줄 %d/%d' % (min(self.lines_total, self.goal_lines), self.goal_lines)
            for kind, name in (('sun', '해'), ('moon', '달')):
                total = self.goal_specials[kind]
                if total:
                    goal += '  %s %d/%d' % (name, total - self.specials_left(kind), total)
            draw_text(goal, 470, 34, 20)
        else:
            draw_number(str(self.turn), 1100, 16)

        # 이번 / 다음 색
        draw_tl(img('hud/color_panel'), *COLOR_PANEL)
        draw_tl(img('cube/sticker_front_' + self.color), 432, 192)
        draw_tl(img('hud/mini_' + self.next_color), 552, 204)

        # 블록 미리보기 (3칸 미만이면 회색)
        draw_tl(img('hud/block_preview_panel'), *PREVIEW_PANEL)
        if not self.dragging:
            mini = img('hud/mini_' + (self.color if self.piece_ready() else 'gray'))
            for r, c in self.piece:
                draw_tl(mini, 448 + 48 * c, 376 + 48 * r)

    def draw_drag(self):
        left, top = self.piece_top_left()
        block = img('board/block_' + self.color)
        for r, c in self.piece:
            draw_tl(block, left + CELL * c, top + CELL * r)


# ---------- 최고 기록 ----------
def load_highscore():
    try:
        with open(config.HIGHSCORE_FILE) as f:
            return int(f.read().strip() or 0)
    except (OSError, ValueError):
        return 0


def save_highscore(score):
    if score > load_highscore():
        with open(config.HIGHSCORE_FILE, 'w') as f:
            f.write(str(score))


def open_pause():
    if game.state in (STATE_OVER, STATE_CLEAR):
        return
    import pause_mode
    game_framework.push_mode(pause_mode)


# ---------- 모드 함수 ----------
def init():
    global game
    game = Game()


def finish():
    global game
    game = None


def pause():
    pass


def resume():
    pass


def handle_events(events):
    for event in events:
        game.handle_event(event)


def update(dt):
    game.update(dt)


def draw():
    game.draw()
