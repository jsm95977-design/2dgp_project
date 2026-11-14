"""픽셀 에셋 불러오기와 왼쪽 위 기준 그리기 (assets/pixel/UI_GUIDE.md 참고)

가이드의 좌표는 모두 화면 왼쪽 위 기준, 이미지 왼쪽 위 모서리다.
pico2d는 왼쪽 아래 원점, 이미지 중심 기준이라 여기서 바꿔 그린다.
마우스 이벤트의 (event.x, event.y)는 원래 왼쪽 위 기준이므로 UI 판정에는 그대로 쓴다."""
import os

from pico2d import load_image, load_font, SDL_MOUSEMOTION, SDL_MOUSEBUTTONDOWN, SDL_BUTTON_LEFT

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


def img(path):
    """'hud/score_panel' 처럼 확장자 없이 부른다. 한 번 불러온 이미지는 재사용한다."""
    if path not in _cache:
        _cache[path] = load_image(os.path.join(PIXEL_DIR, path + '.png'))
    return _cache[path]


def draw_tl(image, left, top):
    image.draw(left + image.w / 2, HEIGHT - top - image.h / 2)


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
