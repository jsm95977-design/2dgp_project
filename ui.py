"""픽셀 에셋 불러오기와 왼쪽 위 기준 그리기 (assets/pixel/UI_GUIDE.md 참고)

가이드의 좌표는 모두 화면 왼쪽 위 기준, 이미지 왼쪽 위 모서리다.
pico2d는 왼쪽 아래 원점, 이미지 중심 기준이라 여기서 바꿔 그린다.
마우스 이벤트의 (event.x, event.y)는 원래 왼쪽 위 기준이므로 UI 판정에는 그대로 쓴다."""
import os

import ctypes

from pico2d import load_image, load_font, draw_rectangle, SDL_MOUSEMOTION, SDL_MOUSEBUTTONDOWN, SDL_BUTTON_LEFT
from sdl2.sdlttf import TTF_SizeUTF8

from settings import HEIGHT

PIXEL_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'assets', 'pixel')
DIGITS = '0123456789+x/'

_cache = {}


FONT_CANDIDATES = (
    os.path.join(os.path.dirname(os.path.abspath(__file__)), 'assets', 'fonts', 'Galmuri11-Bold.ttf'),
    os.path.join(os.path.dirname(os.path.abspath(__file__)), 'assets', 'fonts', 'Galmuri11.ttf'),
    'C:/Windows/Fonts/malgunbd.ttf',
    'C:/Windows/Fonts/malgun.ttf',
)
_fonts = {}


def font(size):
    """한글 폰트. 픽셀 에셋과 같은 Galmuri11(굵게)을 쓰고, 없으면 맑은 고딕. 둘 다 없으면 None"""
    if size not in _fonts:
        _fonts[size] = None
        for path in FONT_CANDIDATES:
            if os.path.exists(path):
                _fonts[size] = load_font(path, size)
                break
    return _fonts[size]


def draw_text(text, left, top, size=20, color=(255, 255, 255)):
    """왼쪽 위 기준 글자 그리기 (top은 글자 줄의 위쪽)"""
    f = font(size)
    if f:
        f.draw(left, HEIGHT - top - size * 0.7, text, color)


def text_width(text, size=20):
    """draw_text로 그렸을 때 글자 너비(px). 글꼴이 없으면 대략 글자 수 x 크기"""
    f = font(size)
    if not f or not text:
        return len(text) * size
    w, h = ctypes.c_int(), ctypes.c_int()
    TTF_SizeUTF8(f.font, text.encode('utf-8'), ctypes.byref(w), ctypes.byref(h))
    return w.value


def wrap_text(text, size, width, max_lines=None):
    """width(px) 안에 들어가게 줄을 나눈다. 띄어쓰기에서 먼저 나누고, 한 단어가 너무 길면 글자 단위로 나눈다."""
    lines = []
    for paragraph in text.split('\n'):
        line = ''
        for word in paragraph.split(' '):
            candidate = word if not line else line + ' ' + word
            if text_width(candidate, size) <= width:
                line = candidate
                continue
            if line:
                lines.append(line)
            line = ''
            for ch in word:                      # 단어 자체가 길면 글자 단위
                if text_width(line + ch, size) > width and line:
                    lines.append(line)
                    line = ''
                line += ch
        lines.append(line)
    return lines[:max_lines] if max_lines else lines


def fill_tl(left, top, w, h, color):
    """왼쪽 위 기준 채운 사각형 (색은 (r, g, b))"""
    draw_rectangle(left, HEIGHT - top - h, left + w - 1, HEIGHT - top - 1, *color, 255, True)


def draw_hint_bar(text, left, top, size=18):
    """밝은 배경 위에서도 읽히게 HUD 패널 색의 어두운 띠 위에 도움말 글자를 쓴다"""
    pad_x, pad_y = 12, 6
    w, h = text_width(text, size) + 2 * pad_x, size + 2 * pad_y + 2
    fill_tl(left, top, w, h, (36, 25, 92))                  # 테두리
    fill_tl(left + 2, top + 2, w - 4, h - 4, (43, 37, 88))  # 안쪽
    draw_text(text, left + pad_x, top + pad_y + 2, size, (220, 220, 240))


def img(path):
    """'hud/score_panel' 처럼 확장자 없이 부른다. 한 번 불러온 이미지는 재사용한다."""
    if path not in _cache:
        _cache[path] = load_image(os.path.join(PIXEL_DIR, path + '.png'))
    return _cache[path]


def draw_tl(image, left, top):
    image.draw(left + image.w / 2, HEIGHT - top - image.h / 2)


def draw_part(image, src_left, src_w, left, top, w=None):
    """이미지의 가로 일부(src_left부터 src_w만큼, 높이 전체)를 왼쪽 위 (left, top)에 그린다.
    w를 주면 그 너비로 늘린다 (패널 가운데를 늘려 길이를 바꿀 때)"""
    w = src_w if w is None else w
    image.clip_draw(src_left, 0, src_w, image.h, left + w / 2, HEIGHT - top - image.h / 2, w, image.h)


def draw_tl_scaled(image, left, top, w, h):
    image.draw(left + w / 2, HEIGHT - top - h / 2, w, h)


def draw_frame(sheet, i, fw, fh, left, top):
    """가로 시트의 i번째 프레임을 왼쪽 위 (left, top)에 그린다"""
    sheet.clip_draw(i * fw, 0, fw, fh, left + fw / 2, HEIGHT - top - fh / 2)


def draw_number(text, left, top, yellow=False):
    digits = img('hud/digits_yellow' if yellow else 'hud/digits_white')
    for n, ch in enumerate(text):
        k = DIGITS.index(ch)
        digits.clip_draw(k * 36, 0, 36, 40, left + n * 36 + 18, HEIGHT - top - 20)


def inside(x, y, left, top, w, h):
    return left <= x < left + w and top <= y < top + h


class Button:
    """name: 'buttons/btn_pass' 처럼. _hover(있으면 _disabled) 이미지를 함께 쓴다."""

    def __init__(self, name, left, top, hit_h=92, has_disabled=False):
        self.normal = img(name)
        self.hover_image = img(name + '_hover')
        self.disabled_image = img(name + '_disabled') if has_disabled else None
        self.left, self.top = left, top
        self.hit_h = hit_h
        self.hover = False
        self.enabled = True

    def contains(self, x, y):
        return inside(x, y, self.left, self.top, self.normal.w, self.hit_h)

    def handle_event(self, event):
        """클릭되면 True"""
        if event.type == SDL_MOUSEMOTION:
            self.hover = self.contains(event.x, event.y)
        elif event.type == SDL_MOUSEBUTTONDOWN and event.button == SDL_BUTTON_LEFT:
            return self.enabled and self.contains(event.x, event.y)
        return False

    def draw(self):
        if not self.enabled and self.disabled_image:
            image = self.disabled_image
        elif self.hover and self.enabled:
            image = self.hover_image
        else:
            image = self.normal
        draw_tl(image, self.left, self.top)
