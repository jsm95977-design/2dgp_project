"""큐브 앞면 → 블록 추출 (로직 전용, pico2d 없음)"""
from config import MIN_PIECE_CELLS


def extract(front, color):
    """앞면 3x3 색 배열에서 color 칸들을 모아 왼쪽 위로 붙인 (행, 열) 목록을 돌려준다.
    연결되어 있지 않아도 하나의 블록으로 본다."""
    cells = [(r, c) for r in range(3) for c in range(3) if front[r][c] == color]
    if not cells:
        return []
    top = min(r for r, _ in cells)
    left = min(c for _, c in cells)
    return [(r - top, c - left) for r, c in cells]


def is_placeable(cells):
    return len(cells) >= MIN_PIECE_CELLS


def size(cells):
    """(행 수, 열 수)"""
    if not cells:
        return 0, 0
    return max(r for r, _ in cells) + 1, max(c for _, c in cells) + 1
