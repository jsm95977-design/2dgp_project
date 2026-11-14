"""8x8 판: 배치, 줄 삭제, 방해 블록 (로직 전용, pico2d 없음)"""
import random

from config import BOARD_SIZE, MIN_PIECE_CELLS

# 칸 값: None(빈칸) | ('block', 색) | ('obstacle', 내구도)


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

    def full_lines(self):
        rows = [r for r in range(self.size) if all(self.cells[r][c] is not None for c in range(self.size))]
        cols = [c for c in range(self.size) if all(self.cells[r][c] is not None for r in range(self.size))]
        return rows, cols

    def clear_lines(self):
        """꽉 찬 가로·세로 줄을 동시에 지운다.
        돌려주는 값: (지운 줄 수, 사라진 칸 [(r, c, 색)], 금만 간 내구도 칸 [(r, c)])"""
        rows, cols = self.full_lines()
        targets = {(r, c) for r in rows for c in range(self.size)}
        targets |= {(r, c) for c in cols for r in range(self.size)}
        removed, cracked = [], []
        for r, c in sorted(targets):
            kind, value = self.cells[r][c]
            if kind == 'obstacle' and value > 1:
                self.cells[r][c] = ('obstacle', value - 1)
                cracked.append((r, c))
            else:
                removed.append((r, c, value if kind == 'block' else 'white'))
                self.cells[r][c] = None
        return len(rows) + len(cols), removed, cracked

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
