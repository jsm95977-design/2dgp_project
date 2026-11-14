"""보드 칸 하나 그리기 (플레이 화면과 편집 모드가 같이 쓴다)

일반 블록·방해 블록과 스테이지 특수 블록(assets/pixel/special/)을 64x64로 그린다.
t는 애니메이션용 시간(초)이다."""
from ui import img, draw_tl, draw_frame

CELL = 64
STEEL_SHINE_EVERY = 3.0      # 강철은 이 간격마다 한 번 반짝인다
DIM = 0.45                   # 활성화 전 해, 빈 달의 투명도


def anim(name, frames, fps, t, left, top):
    draw_frame(img(name), int(t * fps) % frames, CELL, CELL, left, top)


def draw_dim(name, left, top):
    image = img(name)
    image.opacify(DIM)
    draw_tl(image, left, top)
    image.opacify(1.0)


def draw_cell(value, left, top, t=0.0, phase=0.0, hit=False):
    """value: board 칸 값 (None이면 아무것도 그리지 않는다). phase는 칸마다 반짝임을 엇갈리게 하는 값"""
    if value is None:
        return
    kind, v = value
    if kind == 'block':
        draw_tl(img('board/block_' + v), left, top)
    elif kind == 'obstacle':
        draw_tl(img('board/obstacle_hp%d' % v), left, top)
    elif kind == 'steel':
        if hit:
            draw_tl(img('special/steel_hit'), left, top)
            return
        shine = (t + phase) % STEEL_SHINE_EVERY
        if shine < 0.6:
            draw_frame(img('special/steel_anim'), int(shine * 10), CELL, CELL, left, top)
        else:
            draw_tl(img('special/steel'), left, top)
    elif kind == 'bomb':
        if v <= 1:
            anim('special/bomb_1_anim', 4, 8, t, left, top)      # 터지기 직전 깜빡임
        else:
            draw_tl(img('special/bomb_%d' % min(v, 3)), left, top)
    elif kind == 'sun':
        if v:
            anim('special/sun_anim', 4, 5, t + phase, left, top)   # 활성화: 햇살이 움직인다
        else:
            draw_dim('special/sun', left, top)
    elif kind == 'moon':
        if v:
            anim('special/moon_%d_anim' % v, 3, 4, t + phase, left, top)   # 1 초승, 2 반달, 3 보름달
        else:
            draw_dim('special/moon_1', left, top)                   # 아직 한 번도 안 지운 달
