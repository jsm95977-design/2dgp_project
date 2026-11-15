"""픽셀 말풍선: 이미지 없이 사각형만으로 그린다 (다른 UI처럼 4px 단위, 어두운 테두리·아래 그림자).

꼬리는 오른쪽으로 계단 모양으로 튀어나와 말하는 캐릭터를 가리킨다."""
from ui import fill_tl, draw_text, wrap_text

UNIT = 4
OUTLINE = (36, 25, 92)        # 다른 UI의 어두운 테두리색
SHADOW = (36, 25, 92)
FILL = (255, 255, 255)
TEXT = (36, 25, 92)
TEXT_SIZE = 24                # Galmuri11 12px 격자의 2배 → 반듯한 픽셀
LINE_H = 30
PAD_X, PAD_Y = 20, 14
TAIL_STEPS = 5                # 꼬리 길이 (칸 수)


def _rounded_rect(left, top, w, h, color, inset=0):
    """모서리를 한 칸 깎은 사각형"""
    l, t, w, h = left + inset, top + inset, w - 2 * inset, h - 2 * inset
    fill_tl(l + UNIT, t, w - 2 * UNIT, h, color)
    fill_tl(l, t + UNIT, w, h - 2 * UNIT, color)


def _tail(right, center_y, color, shrink):
    """오른쪽으로 갈수록 짧아지는 세로 막대들. shrink만큼 위아래를 줄여 안쪽 색을 그린다."""
    for k in range(TAIL_STEPS):
        half = (TAIL_STEPS - 1 - k) * UNIT // 2 + UNIT - shrink
        if half <= 0:
            break
        fill_tl(right + k * UNIT, center_y - half, UNIT, 2 * half, color)


def lines_for(text, width):
    return wrap_text(text, TEXT_SIZE, width - 2 * PAD_X, max_lines=3)


def draw_bubble(left, top, w, h, text, tail_y=None):
    """왼쪽 위 (left, top), 크기 w x h 말풍선. tail_y(화면 y)에 오른쪽 꼬리. 글자는 세로 가운데 정렬."""
    tail_y = top + h // 2 if tail_y is None else tail_y
    right = left + w
    # 그림자 → 테두리 → 안쪽
    _rounded_rect(left, top + UNIT + 2, w, h, SHADOW)
    _rounded_rect(left, top, w, h, OUTLINE)
    _tail(right - UNIT, tail_y, OUTLINE, 0)
    _rounded_rect(left, top, w, h, FILL, inset=UNIT)
    _tail(right - 2 * UNIT, tail_y, FILL, UNIT)

    lines = lines_for(text, w)
    y = top + (h - LINE_H * len(lines)) // 2 + 3
    for line in lines:
        draw_text(line, left + PAD_X, y, TEXT_SIZE, TEXT)
        y += LINE_H
