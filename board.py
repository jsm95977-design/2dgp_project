"""8x8 판: 배치, 줄 삭제, 방해 블록 (로직 전용, pico2d 없음)"""
import random

from config import BOARD_SIZE, MIN_PIECE_CELLS

# 칸 값: None(빈칸) | ('block', 색) | ('obstacle', 내구도)
# 스테이지 특수 블록 (맵에만 있다):
#   ('steel', 0)      강철: 절대 깨지지 않고, 강철이 있는 가로·세로 줄은 지워지지 않는다
#   ('bomb', 남은 턴)  폭탄: 턴이 끝날 때마다 1씩 줄고 0이 되면 주변 3x3의 블록을 없앤다 (점수 없음)
#   ('sun', 0/1)      해: 주변 8칸이 모두 차면 1(활성화). 활성화된 뒤 해가 든 줄을 지우면 획득
#   ('moon', 0~3)     달: 달이 든 줄이 지워질 때마다 초승(1)→반달(2)→보름달(3). 보름달 뒤 한 번 더 지우면 획득
SPECIAL_KINDS = ('steel', 'bomb', 'sun', 'moon')
MOON_FULL = 3


class Board:
    def __init__(self, size=BOARD_SIZE):
        self.size = size
        self.cells = [[None] * size for _ in range(size)]

    def inside(self, r, c):
        return 0 <= r < self.size and 0 <= c < self.size

    def can_place(self, shape, r0, c0):
        return bool(shape) and all(self.inside(r0 + r, c0 + c) and self.cells[r0 + r][c0 + c] is None
                                   for r, c in shape)

    def place(self, shape, r0, c0, color):
        for r, c in shape:
            self.cells[r0 + r][c0 + c] = ('block', color)

    def fits_anywhere(self, shape):
        return any(self.can_place(shape, r, c) for r in range(self.size) for c in range(self.size))

    def has_room_for_min_piece(self):
        """어떤 3칸 블록이라도 들어갈 자리가 있는가. 블록은 3x3 안의 칸들이므로
        3x3 창 안에 빈칸이 MIN_PIECE_CELLS개 이상이면 들어간다."""
        for r0 in range(self.size - 2):
            for c0 in range(self.size - 2):
                empty = sum(self.cells[r][c] is None for r in range(r0, r0 + 3) for c in range(c0, c0 + 3))
                if empty >= MIN_PIECE_CELLS:
                    return True
        return False

    def kind_at(self, r, c):
        cell = self.cells[r][c]
        return cell[0] if cell else None

    def line_cells(self, rows, cols):
        cells = {(r, c) for r in rows for c in range(self.size)}
        return cells | {(r, c) for c in cols for r in range(self.size)}

    def full_lines(self, include_steel=False):
        """꽉 찬 가로·세로 줄. 강철이 든 줄은 지울 수 없으므로 빼고 돌려준다."""
        def ok(cells):
            cells = list(cells)
            return (all(self.cells[r][c] is not None for r, c in cells) and
                    (include_steel or not any(self.kind_at(r, c) == 'steel' for r, c in cells)))
        n = self.size
        rows = [r for r in range(n) if ok((r, c) for c in range(n))]
        cols = [c for c in range(n) if ok((r, c) for r in range(n))]
        return rows, cols

    def steel_blocked(self):
        """꽉 찼지만 강철 때문에 지워지지 않는 줄에 든 강철 칸들 (버티는 연출용)"""
        rows, cols = self.full_lines(include_steel=True)
        return [(r, c) for r, c in sorted(self.line_cells(rows, cols)) if self.kind_at(r, c) == 'steel']

    def activate_suns(self):
        """주변 8칸이 모두 찬 해를 활성화한다 (판 바깥은 찬 칸으로 친다). 새로 활성화된 위치 목록"""
        activated = []
        for r in range(self.size):
            for c in range(self.size):
                if self.cells[r][c] != ('sun', 0):
                    continue
                if all(not self.inside(r + dr, c + dc) or self.cells[r + dr][c + dc] is not None
                       for dr in (-1, 0, 1) for dc in (-1, 0, 1) if (dr, dc) != (0, 0)):
                    self.cells[r][c] = ('sun', 1)
                    activated.append((r, c))
        return activated

    def clear_lines(self):
        """꽉 찬 가로·세로 줄을 동시에 지운다.
        돌려주는 값: (지운 줄 수, 사라진 칸 [(r, c, 색)], 금만 간 내구도 칸 [(r, c)])
        해·달 변화는 self.last_specials에 남긴다: {'moon_up': [(r, c)], 'collected': [(r, c, 종류)]}"""
        rows, cols = self.full_lines()
        removed, cracked = [], []
        self.last_specials = {'moon_up': [], 'collected': []}
        for r, c in sorted(self.line_cells(rows, cols)):
            kind, value = self.cells[r][c]
            if kind == 'obstacle' and value > 1:
                self.cells[r][c] = ('obstacle', value - 1)
                cracked.append((r, c))
            elif kind == 'sun' and value == 0:
                pass                                   # 아직 활성화 안 된 해는 그대로 남는다
            elif kind == 'moon' and value < MOON_FULL:
                self.cells[r][c] = ('moon', value + 1)  # 한 번 지울 때 한 단계 (가로·세로 겹쳐도 1단계)
                self.last_specials['moon_up'].append((r, c))
            elif kind in ('sun', 'moon'):
                self.cells[r][c] = None                # 활성화된 해, 보름달은 획득
                self.last_specials['collected'].append((r, c, kind))
            else:
                removed.append((r, c, value if kind == 'block' else 'white'))
                self.cells[r][c] = None
        return len(rows) + len(cols), removed, cracked

    def tick_bombs(self):
        """턴이 끝날 때 부른다. 모든 폭탄의 숫자를 1 줄이고, 0이 된 폭탄은 터뜨린다.
        터지면 폭탄 칸과 주변 3x3의 일반 블록·방해 블록이 사라진다 (플레이어가 지운 게 아니라 점수 없음).
        강철·해·달·다른 폭탄은 남는다.
        돌려주는 값: (터진 폭탄 위치 [(r, c)], 사라진 칸 [(r, c, 색)])"""
        bombs = [(r, c) for r in range(self.size) for c in range(self.size) if self.kind_at(r, c) == 'bomb']
        exploded = []
        for r, c in bombs:
            count = self.cells[r][c][1] - 1
            self.cells[r][c] = ('bomb', count)
            if count <= 0:
                exploded.append((r, c))
        destroyed = []
        for r, c in exploded:
            self.cells[r][c] = None
            for rr in range(r - 1, r + 2):
                for cc in range(c - 1, c + 2):
                    if self.inside(rr, cc) and self.kind_at(rr, cc) in ('block', 'obstacle'):
                        kind, value = self.cells[rr][cc]
                        destroyed.append((rr, cc, value if kind == 'block' else 'white'))
                        self.cells[rr][cc] = None
        return exploded, destroyed

    def count(self, kind):
        return sum(self.kind_at(r, c) == kind for r in range(self.size) for c in range(self.size))

    def empty_cells(self):
        return [(r, c) for r in range(self.size) for c in range(self.size) if self.cells[r][c] is None]

    def spawn_obstacles(self, hps):
        """hps의 각 내구도로 빈칸에 방해 블록을 만든다. 만든 위치 목록을 돌려준다."""
        empty = self.empty_cells()
        random.shuffle(empty)
        spawned = []
        for (r, c), hp in zip(empty, hps):
            self.cells[r][c] = ('obstacle', hp)
            spawned.append((r, c))
        return spawned
