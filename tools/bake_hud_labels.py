"""HUD 패널 이미지의 글자(점수·턴·이번·다음·블록)를 Galmuri11 Bold로 다시 굽는다.

원래 이미지의 글자는 9~10px 글꼴을 4배로 키운 것이라 획이 뭉개져 보였다 ('점'이 '컴'처럼 보임).
글자 자리를 패널 바탕색으로 덮고, 같은 색·같은 어두운 테두리로 Galmuri11 Bold를 정확히 3배(36px)
크기에 안티앨리어싱 없이(Solid) 그려 픽셀 느낌은 유지하면서 더 또렷하게 만든다.

실행: python tools/bake_hud_labels.py   (assets/pixel/hud/의 PNG를 덮어쓴다. 여러 번 실행해도 결과가 같다)
"""
import ctypes
import os
import sys

from sdl2 import (SDL_Init, SDL_Quit, SDL_INIT_VIDEO, SDL_ConvertSurfaceFormat, SDL_PIXELFORMAT_ARGB8888,
                  SDL_FillRect, SDL_MapRGBA, SDL_Rect, SDL_BlitSurface, SDL_FreeSurface, SDL_Color)
from sdl2.sdlimage import IMG_Init, IMG_INIT_PNG, IMG_Load, IMG_SavePNG
from sdl2.sdlttf import TTF_Init, TTF_OpenFont, TTF_RenderUTF8_Solid, TTF_CloseFont, TTF_SizeUTF8

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HUD = os.path.join(ROOT, 'assets', 'pixel', 'hud')
FONT = os.path.join(ROOT, 'assets', 'fonts', 'Galmuri11-Bold.ttf')
SIZE = 36                 # Galmuri11은 12px 격자라 3배에서 픽셀이 반듯하다
PIXEL = SIZE // 12        # 글꼴 한 칸 = 3px → 테두리 두께
BG = (43, 37, 88)         # 패널 안쪽 바탕
OUTLINE = (36, 25, 92)    # 원래 글자 테두리색
YELLOW = (255, 210, 63)
WHITE = (255, 255, 255)
LIGHT_GRAY = (214, 222, 236)   # '다음' (원래 192,203,220보다 조금 밝게 해 대비를 올림)

# 파일: [(덮을 영역 x0, y0, x1, y1), 글자, 색, 글자 가운데 (x, y)] - 좌표는 이미지 왼쪽 위 기준
LABELS = {
    'score_panel': [((16, 10, 112, 64), '점수', YELLOW, (64, 36))],
    'turn_panel': [((16, 12, 72, 64), '턴', YELLOW, (42, 38))],
    'color_panel': [((16, 20, 122, 82), '이번', WHITE, (72, 51)),
                    ((126, 20, 232, 82), '다음', LIGHT_GRAY, (176, 51))],
    'block_preview_panel': [((16, 20, 124, 80), '블록', WHITE, (74, 48))],
}


def text_surface(font, text, color):
    return TTF_RenderUTF8_Solid(font, text.encode('utf-8'), SDL_Color(*color, 255))


def blit(src, dst, left, top):
    SDL_BlitSurface(src, None, dst, SDL_Rect(left, top, 0, 0))


def bake(name, labels, font):
    path = os.path.join(HUD, name + '.png')
    loaded = IMG_Load(path.encode())
    if not loaded:
        sys.exit('이미지를 열 수 없음: ' + path)
    image = SDL_ConvertSurfaceFormat(loaded, SDL_PIXELFORMAT_ARGB8888, 0)
    SDL_FreeSurface(loaded)
    for (x0, y0, x1, y1), text, color, (cx, cy) in labels:
        SDL_FillRect(image, SDL_Rect(x0, y0, x1 - x0, y1 - y0), SDL_MapRGBA(image.contents.format, *BG, 255))
        w, h = ctypes.c_int(), ctypes.c_int()
        TTF_SizeUTF8(font, text.encode('utf-8'), ctypes.byref(w), ctypes.byref(h))
        # 글꼴 칸(3px)에 맞춰 위치를 정해 픽셀이 반듯하게 놓이게 한다
        left = (cx - w.value // 2) // PIXEL * PIXEL
        top = (cy - h.value // 2) // PIXEL * PIXEL
        shadow = text_surface(font, text, OUTLINE)
        for dx in (-PIXEL, 0, PIXEL):          # 8방향 테두리
            for dy in (-PIXEL, 0, PIXEL):
                if dx or dy:
                    blit(shadow, image, left + dx, top + dy)
        blit(shadow, image, left, top + 2 * PIXEL)   # 아래쪽 그림자 한 칸 더 (원래 글자처럼 도톰하게)
        blit(shadow, image, left - PIXEL, top + 2 * PIXEL)
        blit(shadow, image, left + PIXEL, top + 2 * PIXEL)
        SDL_FreeSurface(shadow)
        face = text_surface(font, text, color)
        blit(face, image, left, top)
        SDL_FreeSurface(face)
    IMG_SavePNG(image, path.encode())
    SDL_FreeSurface(image)
    print('구움:', name)


def main():
    SDL_Init(SDL_INIT_VIDEO)
    IMG_Init(IMG_INIT_PNG)
    TTF_Init()
    font = TTF_OpenFont(FONT.encode(), SIZE)
    if not font:
        sys.exit('글꼴을 열 수 없음: ' + FONT)
    for name, labels in LABELS.items():
        bake(name, labels, font)
    TTF_CloseFont(font)
    SDL_Quit()


if __name__ == '__main__':
    main()
