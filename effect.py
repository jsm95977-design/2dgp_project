"""이펙트: 스프라이트 시트 애니메이션, 떠오르며 사라지는 문구·점수"""
from ui import img, draw_frame, draw_tl, draw_number


class SheetEffect:
    def __init__(self, name, frames, left, top, size=96, fps=14, delay=0.0):
        self.sheet = img(name)
        self.frames, self.size, self.fps = frames, size, fps
        self.left, self.top = left, top
        self.time = -delay
        self.done = False

    def update(self, dt):
        self.time += dt
        if self.time * self.fps >= self.frames:
            self.done = True

    def draw(self):
        if self.time >= 0 and not self.done:
            draw_frame(self.sheet, int(self.time * self.fps), self.size, self.size, self.left, self.top)


class FloatingText:
    """이미지(칭찬 문구) 또는 노란 숫자(점수)를 위로 띄우며 사라지게 한다"""

    def __init__(self, center_left, top, image_name=None, number=None, life=1.0, rise=60):
        self.image = img(image_name) if image_name else None
        self.number = number
        self.center_left, self.top = center_left, top
        self.life, self.rise = life, rise
        self.time = 0.0
        self.done = False

    def update(self, dt):
        self.time += dt
        self.done = self.time >= self.life

    def draw(self):
        t = self.time / self.life
        top = self.top - self.rise * t
        alpha = 1.0 if t < 0.6 else max(0.0, (1 - t) / 0.4)
        if self.image:
            self.image.opacify(alpha)
            draw_tl(self.image, self.center_left - self.image.w / 2, top)
            self.image.opacify(1.0)
        else:
            digits = img('hud/digits_yellow')
            digits.opacify(alpha)
            draw_number(self.number, self.center_left - len(self.number) * 18, top, yellow=True)
            digits.opacify(1.0)
