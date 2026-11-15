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
TAIL_STEPS = 4                # 꼬리 계단 수
TAIL_STEP_W = 8               # 계단 한 단 너비 → 꼬리 길이 32px
MIN_H = 64


def _rounded_rect(left, top, w, h, color, inset=0):
    """모서리를 한 칸 깎은 사각형"""
    l, t, w, h = left + inset, top + inset, w - 2 * inset, h - 2 * inset
    fill_tl(l + UNIT, t, w - 2 * UNIT, h, color)
    fill_tl(l, t + UNIT, w, h - 2 * UNIT, color)


def tail_half(k):
    """꼬리 k번째 단의 테두리 절반 높이 (오른쪽으로 갈수록 한 칸씩 낮아진다)"""
    return (TAIL_STEPS - k) * UNIT + UNIT


def _tail(right, center_y):
    """오른쪽으로 튀어나온 계단 꼬리. 테두리를 먼저 그리고 안쪽을 한 칸 작게 채운다.
    첫 단의 안쪽은 말풍선 테두리 위까지 칠해 말풍선과 이어 보이게 한다."""
    x0 = right - UNIT
    for k in range(TAIL_STEPS):
        half = tail_half(k)
        fill_tl(x0 + k * TAIL_STEP_W, center_y - half, TAIL_STEP_W, 2 * half, OUTLINE)
    for k in range(TAIL_STEPS):
        half = tail_half(k) - 2 * UNIT
        if half <= 0:
            break
        extra = UNIT if k == 0 else 0
        fill_tl(x0 + k * TAIL_STEP_W - extra, center_y - half, TAIL_STEP_W + extra, 2 * half, FILL)


def lines_for(text, width):
    return wrap_text(text, TEXT_SIZE, width - 2 * PAD_X, max_lines=3)


def height_for(text, width):
    """대사 줄 수에 맞는 말풍선 높이"""
    return max(MIN_H, LINE_H * len(lines_for(text, width)) + 2 * PAD_Y)


def draw_bubble(left, bottom, w, text, tail_y):
    """아래쪽 bottom에 붙여 줄 수에 맞는 높이로 그린다 (위로 자란다).
    tail_y(화면 y)에 오른쪽 꼬리 - 말풍선 안에 들어오도록 맞춘다. 글자는 세로 가운데 정렬."""
    h = height_for(text, w)
    top = bottom - h
    margin = tail_half(0) + UNIT
    tail_y = max(top + margin, min(bottom - margin, tail_y))
    right = left + w
    # 그림자 → 테두리 → 안쪽 → 꼬리 (꼬리 안쪽이 말풍선 테두리를 덮어 이어진다)
    _rounded_rect(left, top + UNIT + 2, w, h, SHADOW)
    _rounded_rect(left, top, w, h, OUTLINE)
    _rounded_rect(left, top, w, h, FILL, inset=UNIT)
    _tail(right, tail_y)

    lines = lines_for(text, w)
    y = top + (h - LINE_H * len(lines)) // 2 + 3
    for line in lines:
        draw_text(line, left + PAD_X, y, TEXT_SIZE, TEXT)
        y += LINE_H
