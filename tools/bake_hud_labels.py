"""픽셀 UI 이미지에 구워진 글자를 Galmuri11 Bold로 다시 굽는다.

원래 이미지의 글자는 작은 글꼴을 크게 키운 것이라 획이 뭉개져 보였다 ('점'이 '컴'처럼 보임).
글자 자리를 바탕으로 덮고, 같은 색·같은 어두운 테두리로 Galmuri11 Bold를 12px 격자의 정확한 배수 크기에
안티앨리어싱 없이(Solid) 그려 픽셀 느낌은 유지하면서 더 또렷하게 만든다.

대상: HUD 패널(점수·턴·이번·다음·블록), 일시정지 창 제목, 계속하기·타이틀로 버튼(기본/hover)

실행: python tools/bake_hud_labels.py   (assets/pixel/의 PNG를 덮어쓴다. 여러 번 실행해도 결과가 같다)
"""
import ctypes
import os
import sys

from sdl2 import (SDL_Init, SDL_Quit, SDL_INIT_VIDEO, SDL_ConvertSurfaceFormat, SDL_PIXELFORMAT_ARGB8888,
                  SDL_FillRect, SDL_MapRGBA, SDL_Rect, SDL_BlitSurface, SDL_FreeSurface, SDL_Color,
                  SDL_LockSurface, SDL_UnlockSurface)
from sdl2.sdlimage import IMG_Init, IMG_INIT_PNG, IMG_Load, IMG_SavePNG
from sdl2.sdlttf import TTF_Init, TTF_OpenFont, TTF_RenderUTF8_Solid, TTF_CloseFont, TTF_SizeUTF8

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PIXEL_DIR = os.path.join(ROOT, 'assets', 'pixel')
# 글꼴: (파일, 격자 px). 크기를 격자의 배수로 하면 픽셀이 반듯하다.
# Galmuri14는 획 사이 여유가 있어 '틀'처럼 복잡한 글자도 크게 키웠을 때 덜 뭉개진다 (버튼·제목용)
FONTS = {
    'G11B': (os.path.join(ROOT, 'assets', 'fonts', 'Galmuri11-Bold.ttf'), 12),
    'G14': (os.path.join(ROOT, 'assets', 'fonts', 'Galmuri14.ttf'), 14),
}

BG = (43, 37, 88)         # HUD 패널 안쪽 바탕
OUTLINE = (36, 25, 92)    # 원래 글자 테두리색
YELLOW = (255, 210, 63)
WHITE = (255, 255, 255)
LIGHT_GRAY = (214, 222, 236)   # '다음' (원래 192,203,220보다 조금 밝게 해 대비를 올림)
TITLE_BANDS = [(255, 230, 149), (255, 210, 63), (199, 164, 49)]   # 창 제목: 위 밝게 → 아래 어둡게

# 덮기 방식: ('flat', 색) 은 한 색으로, ('row', x) 는 줄마다 같은 줄의 x 위치 바탕색으로 (띠 무늬·구분선 보존)
HUD = dict(font='G11B', size=36, fill=('flat', BG))
BUTTON = dict(font='G14', size=56, bold=True, fill=('row', 40), color=WHITE)
LABELS = {
    'hud/score_panel': [dict(HUD, rect=(16, 10, 112, 64), text='점수', color=YELLOW, center=(64, 36))],
    'hud/turn_panel': [dict(HUD, rect=(16, 12, 72, 64), text='턴', color=YELLOW, center=(42, 38))],
    'hud/color_panel': [dict(HUD, rect=(16, 20, 122, 82), text='이번', color=WHITE, center=(72, 51)),
                        dict(HUD, rect=(126, 20, 232, 82), text='다음', color=LIGHT_GRAY, center=(176, 51))],
    'hud/block_preview_panel': [dict(HUD, rect=(16, 20, 124, 80), text='블록', color=WHITE, center=(74, 48))],
    'windows/pause_window': [dict(font='G14', size=84, bold=True, fill=('row', 30), rect=(36, 32, 444, 130), text='일시정지',
                                  color=TITLE_BANDS, center=(240, 78))],
    # 버튼은 hover 그림이 4px 위로 올라가 있다
    'buttons/btn_resume': [dict(BUTTON, rect=(60, 26, 260, 80), text='계속하기', center=(160, 52))],
    'buttons/btn_resume_hover': [dict(BUTTON, rect=(60, 22, 260, 76), text='계속하기', center=(160, 48))],
    'buttons/btn_title': [dict(BUTTON, rect=(60, 26, 260, 80), text='타이틀로', center=(160, 52))],
    'buttons/btn_title_hover': [dict(BUTTON, rect=(60, 22, 260, 76), text='타이틀로', center=(160, 48))],
}

fonts = {}


def font(name, size):
    if (name, size) not in fonts:
        path = FONTS[name][0]
        fonts[name, size] = TTF_OpenFont(path.encode(), size)
        if not fonts[name, size]:
            sys.exit('글꼴을 열 수 없음: ' + path)
    return fonts[name, size]


def pixel_at(surface, x, y):
    """ARGB8888 표면의 (x, y) 색 (r, g, b)"""
    s = surface.contents
    row = ctypes.cast(s.pixels, ctypes.POINTER(ctypes.c_uint8))
    i = y * s.pitch + x * 4
    b, g, r = row[i], row[i + 1], row[i + 2]
    return r, g, b


def ink_rows(text_surface):
    """Solid로 그린 글자 표면(8비트)에서 글자가 있는 줄 범위 (첫 줄, 끝 줄+1)"""
    s = text_surface.contents
    data = ctypes.cast(s.pixels, ctypes.POINTER(ctypes.c_uint8))
    rows = [y for y in range(s.h) if any(data[y * s.pitch + x] for x in range(s.w))]
    return rows[0], rows[-1] + 1


def render(name, size, text, color):
    return TTF_RenderUTF8_Solid(font(name, size), text.encode('utf-8'), SDL_Color(*color, 255))


def blit(src, dst, left, top, src_rect=None):
    SDL_BlitSurface(src, src_rect, dst, SDL_Rect(left, top, 0, 0))


def cover(image, rect, fill):
    x0, y0, x1, y1 = rect
    kind, value = fill
    fmt = image.contents.format
    if kind == 'flat':
        SDL_FillRect(image, SDL_Rect(x0, y0, x1 - x0, y1 - y0), SDL_MapRGBA(fmt, *value, 255))
        return
    SDL_LockSurface(image)
    colors = [pixel_at(image, value, y) for y in range(y0, y1)]
    SDL_UnlockSurface(image)
    for y, color in zip(range(y0, y1), colors):
        SDL_FillRect(image, SDL_Rect(x0, y, x1 - x0, 1), SDL_MapRGBA(fmt, *color, 255))


def draw_label(image, label):
    name, size, text, color = label['font'], label['size'], label['text'], label['color']
    unit = size // FONTS[name][1]             # 글꼴 한 칸 크기 = 테두리 두께
    cover(image, label['rect'], label['fill'])

    w, h = ctypes.c_int(), ctypes.c_int()
    TTF_SizeUTF8(font(name, size), text.encode('utf-8'), ctypes.byref(w), ctypes.byref(h))
    cx, cy = label['center']
    left = (cx - w.value // 2) // unit * unit
    top = (cy - h.value // 2) // unit * unit

    bold = label.get('bold', False)
    widths = (0, unit) if bold else (0,)      # bold: 한 칸 오른쪽에 한 번 더 그려 세로획을 굵게
    shadow = render(name, size, text, OUTLINE)
    for dx in (-unit, 0, unit) + ((2 * unit,) if bold else ()):   # 8방향 테두리
        for dy in (-unit, 0, unit):
            if dx or dy:
                blit(shadow, image, left + dx, top + dy)
    for dx in (-unit, 0, unit) + ((2 * unit,) if bold else ()):   # 아래쪽 그림자 한 칸 더 (원래 글자처럼 도톰하게)
        blit(shadow, image, left + dx, top + 2 * unit)
    SDL_FreeSurface(shadow)

    if isinstance(color, tuple):
        face = render(name, size, text, color)
        for bx in widths:
            blit(face, image, left + bx, top)
        SDL_FreeSurface(face)
        return
    # 여러 색 띠: 글자 높이를 띠 수로 나눠 위에서부터 칠한다 (칸 단위로 맞춤)
    first = render(name, size, text, color[0])
    ink_top, ink_bottom = ink_rows(first)
    SDL_FreeSurface(first)
    step = (ink_bottom - ink_top) / len(color)
    for i, band in enumerate(color):
        y0 = ink_top + round(step * i / unit) * unit if i else 0
        y1 = ink_top + round(step * (i + 1) / unit) * unit if i < len(color) - 1 else h.value
        face = render(name, size, text, band)
        for bx in widths:
            blit(face, image, left + bx, top + y0, SDL_Rect(0, y0, w.value, y1 - y0))
        SDL_FreeSurface(face)


def bake(name, labels):
    path = os.path.join(PIXEL_DIR, *name.split('/')) + '.png'
    loaded = IMG_Load(path.encode())
    if not loaded:
        sys.exit('이미지를 열 수 없음: ' + path)
    image = SDL_ConvertSurfaceFormat(loaded, SDL_PIXELFORMAT_ARGB8888, 0)
    SDL_FreeSurface(loaded)
    for label in labels:
        draw_label(image, label)
    IMG_SavePNG(image, path.encode())
    SDL_FreeSurface(image)
    print('구움:', name)


def main():
    SDL_Init(SDL_INIT_VIDEO)
    IMG_Init(IMG_INIT_PNG)
    TTF_Init()
    targets = sys.argv[1:] or list(LABELS)     # 이름을 주면 그 이미지만
    for name in targets:
        bake(name, LABELS[name])
    for f in fonts.values():
        TTF_CloseFont(f)
    SDL_Quit()


if __name__ == '__main__':
    main()
