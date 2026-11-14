import ctypes
import math
import os
import random

from pico2d import *
import pico2d.pico2d as pico2d_core

from cube import Cube, FACES, IDENTITY, mat_mul, rotation, transform

SCALE = 100           # 큐브 한 칸의 화면 크기(픽셀)
CAMERA_DISTANCE = 11  # 작을수록 원근이 강해진다
BODY_COLOR = (30, 29, 40)
LIGHT = (0.25, 0.45, 0.86)
AMBIENT, DIFFUSE = 0.62, 0.38

START_YAW, START_PITCH = math.radians(-35), math.radians(30)
ORBIT_SPEED = 0.008   # 빈 공간 드래그: 픽셀당 라디안
DRAG_THRESHOLD = 6    # 이만큼 움직여야 층 회전 방향을 정한다
SETTLE_SPEED = 9.0    # 놓은 뒤 90도 단위로 맞춰지는 속도(라디안/초)
QUARTER = math.pi / 2

UVS = ((0, 0), (1, 0), (1, 1), (0, 1))
TILE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'assets', 'tiles')


def face_corners(normal, right, up):
    return [tuple((n + right_sign * r + up_sign * u) / 2 for n, r, u in zip(normal, right, up))
            for right_sign, up_sign in ((-1, 1), (1, 1), (1, -1), (-1, -1))]


FACE_CORNERS = [face_corners(*face[:3]) for face in FACES]


def add(a, b):
    return tuple(p + q for p, q in zip(a, b))


def dot(a, b):
    return sum(p * q for p, q in zip(a, b))


def cross(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def signed_area(quad):
    return sum(quad[i - 1][0] * quad[i][1] - quad[i][0] * quad[i - 1][1] for i in range(4))


def inside_quad(quad, x, y):
    return all((quad[i][0] - quad[i - 1][0]) * (y - quad[i - 1][1])
               - (quad[i][1] - quad[i - 1][1]) * (x - quad[i - 1][0]) <= 0 for i in range(4))


class LayerTurn:
    """돌아가는 중인 층. angle은 axis의 양의 방향 기준 라디안."""

    def __init__(self, axis, layer):
        self.axis, self.layer = axis, layer
        self.angle = 0.0
        self.target = None  # 마우스를 놓으면 맞춰질 각도
        self.screen_dir = (0, 0)
        self.radians_per_pixel = 0
        self.auto = False   # 자동 섞기로 생긴 회전이면 True (에너지 소모 없음)


class CubeView:
    def __init__(self, center=None, scale=SCALE, area=None, allow_orbit=True, mark_images=None):
        """center: 큐브 중심(pico2d 좌표, 왼쪽 아래 원점), area: 마우스를 받을 영역 (left, bottom, right, top)
        mark_images: highlight 색의 앞면 칸 위에 번갈아 겹칠 이미지들"""
        self.cube = Cube()
        self.scale = scale
        self.area = area
        self.allow_orbit = allow_orbit
        self.enabled = True       # False면 플레이어 입력으로 돌릴 수 없다
        self.on_turn = None       # 플레이어가 돌린 회전이 끝날 때마다 불린다
        self.queue = []           # 애니메이션으로 돌릴 (axis, layer, quarters) 목록
        self.highlight = None
        self.mark_images = mark_images or []
        self.mark_timer = 0.0
        self.tiles = {face[3]: load_image(os.path.join(TILE_DIR, 'tile_%s.png' % face[3])) for face in FACES}
        self.vertices = (SDL_Vertex * 4)()
        self.indices = (ctypes.c_int * 6)(0, 1, 2, 0, 2, 3)
        for vertex, (u, v) in zip(self.vertices, UVS):
            vertex.tex_coord.x, vertex.tex_coord.y = u, v
            vertex.color.a = 255

        self.center = center or (get_canvas_width() / 2, get_canvas_height() / 2)
        self.view = IDENTITY
        self.orbit(START_YAW, START_PITCH)

        self.turn = None
        self.dragging = None  # None, 'orbit', 'grab', 'layer'
        self.grabbed = None
        self.mouse = self.press = (0, 0)

    def orbit(self, yaw, pitch):
        self.view = mat_mul(rotation(1, math.cos(yaw), math.sin(yaw)), self.view)
        self.view = mat_mul(rotation(0, math.cos(pitch), math.sin(pitch)), self.view)

    def project(self, p):
        s = self.scale * CAMERA_DISTANCE / (CAMERA_DISTANCE - p[2])
        return self.center[0] + p[0] * s, self.center[1] + p[1] * s

    def model_view(self, cubie):
        model = cubie.rot
        if self.turn is not None and cubie.pos[self.turn.axis] == self.turn.layer:
            turn = rotation(self.turn.axis, math.cos(self.turn.angle), math.sin(self.turn.angle))
            model = mat_mul(turn, model)
        return mat_mul(self.view, model)

    def project_face(self, m, cubie, face_index):
        return [self.project(transform(m, add(cubie.home, corner))) for corner in FACE_CORNERS[face_index]]

    def pick(self, x, y):
        """(x, y) 아래 보이는 스티커의 (큐비 위치, 바깥 법선)을 돌려준다."""
        for cubie in self.cube.cubies:
            m = mat_mul(self.view, cubie.rot)
            for face_index, face in enumerate(FACES):
                if face not in cubie.stickers:
                    continue
                quad = self.project_face(m, cubie, face_index)
                if signed_area(quad) < 0 and inside_quad(quad, x, y):
                    return cubie.pos, transform(cubie.rot, face[0])
        return None

    def start_layer_turn(self, drag_x, drag_y):
        pos, normal = self.grabbed
        point = add(pos, tuple(n / 2 for n in normal))
        origin = self.project(transform(self.view, point))

        # 스티커 위의 두 방향 중 드래그와 더 나란한 쪽을 고른다
        best = None
        for axis in range(3):
            if normal[axis] != 0:
                continue
            tangent = tuple(1 if i == axis else 0 for i in range(3))
            end = self.project(transform(self.view, add(point, tuple(t / 2 for t in tangent))))
            sx, sy = end[0] - origin[0], end[1] - origin[1]
            length = math.hypot(sx, sy)
            if length < 1:
                continue
            along = (drag_x * sx + drag_y * sy) / length
            if best is None or abs(along) > abs(best[0]):
                best = along, tangent, (sx / length, sy / length), length * 2

        _, tangent, screen_dir, pixels_per_unit = best
        # 법선 n 쪽 표면이 접선 t 방향으로 움직이려면 회전축은 n x t
        rotation_axis = cross(normal, tangent)
        axis = next(i for i in range(3) if rotation_axis[i] != 0)
        self.turn = LayerTurn(axis, pos[axis])
        self.turn.screen_dir = screen_dir
        self.turn.radians_per_pixel = rotation_axis[axis] / (1.5 * pixels_per_unit)

    def start_wheel_turn(self, wheel):
        normal = max((face[0] for face in FACES), key=lambda n: transform(self.view, n)[2])
        axis = next(i for i in range(3) if normal[i] != 0)
        self.turn = LayerTurn(axis, normal[axis])
        # 휠 위 = 화면 쪽 면을 바깥에서 봤을 때 시계 방향
        self.turn.target = -normal[axis] * QUARTER if wheel > 0 else normal[axis] * QUARTER

    def drag_orbit(self, x, y):
        self.orbit((x - self.mouse[0]) * ORBIT_SPEED, -(y - self.mouse[1]) * ORBIT_SPEED)

    def drag_layer(self, x, y):
        drag_x, drag_y = x - self.press[0], y - self.press[1]
        if self.dragging == 'grab' and math.hypot(drag_x, drag_y) >= DRAG_THRESHOLD:
            self.start_layer_turn(drag_x, drag_y)
            self.dragging = 'layer'
        if self.dragging == 'layer':
            along = drag_x * self.turn.screen_dir[0] + drag_y * self.turn.screen_dir[1]
            self.turn.angle = along * self.turn.radians_per_pixel

    @property
    def busy(self):
        """돌아가는 중이거나 돌릴 회전이 남아 있으면 True"""
        return self.turn is not None or bool(self.queue) or self.dragging in ('grab', 'layer')

    def in_area(self, x, y):
        if self.area is None:
            return True
        left, bottom, right, top = self.area
        return left <= x <= right and bottom <= y <= top

    def rotate_front(self, clockwise):
        """앞면(화면 쪽 면)을 90도 돌린다. 키보드·버튼용"""
        if self.enabled and self.turn is None and self.dragging is None and not self.queue:
            self.start_wheel_turn(1 if clockwise else -1)

    def queue_turn(self, axis, layer, quarters):
        self.queue.append((axis, layer, quarters))

    def queue_random_turns(self, count):
        for _ in range(count):
            self.queue_turn(random.randrange(3), random.choice((-1, 0, 1)), random.choice((1, 3)))

    def scramble(self, count):
        """애니메이션 없이 바로 섞는다"""
        for _ in range(count):
            self.cube.turn(random.randrange(3), random.choice((-1, 0, 1)), random.choice((1, 3)))

    def handle_event(self, event):
        if not self.enabled:
            if event.type == SDL_MOUSEBUTTONUP and self.dragging in ('orbit', 'grab'):
                self.dragging = None
            elif event.type == SDL_MOUSEBUTTONUP and self.dragging == 'layer':
                self.turn.target = round(self.turn.angle / QUARTER) * QUARTER
                self.dragging = None
            return
        if event.type == SDL_MOUSEBUTTONDOWN and event.button == SDL_BUTTON_LEFT:
            self.mouse = self.press = event.x, get_canvas_height() - 1 - event.y
            if not self.in_area(*self.mouse):
                return
            self.grabbed = self.pick(*self.mouse)
            if self.grabbed is None:
                self.dragging = 'orbit' if self.allow_orbit else None
            elif self.turn is None and not self.queue:
                self.dragging = 'grab'
        elif event.type == SDL_MOUSEMOTION and self.dragging:
            x, y = event.x, get_canvas_height() - 1 - event.y
            if self.dragging == 'orbit':
                self.drag_orbit(x, y)
            else:
                self.drag_layer(x, y)
            self.mouse = x, y
        elif event.type == SDL_MOUSEBUTTONUP and event.button == SDL_BUTTON_LEFT:
            if self.dragging == 'layer':
                self.turn.target = round(self.turn.angle / QUARTER) * QUARTER
            self.dragging = None
        elif event.type == SDL_MOUSEWHEEL and event.y != 0:
            if self.turn is None and self.dragging is None and not self.queue:
                self.start_wheel_turn(event.y)

    def update(self, frame_time):
        self.mark_timer += frame_time
        if self.turn is None and self.queue and self.dragging is None:
            axis, layer, quarters = self.queue.pop(0)
            self.turn = LayerTurn(axis, layer)
            self.turn.target = quarters * QUARTER
            self.turn.auto = True
        if self.turn is None or self.turn.target is None:
            return
        remaining = self.turn.target - self.turn.angle
        step = SETTLE_SPEED * frame_time
        if abs(remaining) > step:
            self.turn.angle += math.copysign(step, remaining)
            return
        quarters = round(self.turn.target / QUARTER)
        self.cube.turn(self.turn.axis, self.turn.layer, quarters)
        finished, self.turn = self.turn, None
        if quarters % 4 != 0 and not finished.auto and self.on_turn:
            self.on_turn()

    def draw_quad(self, texture, quad, color):
        height = get_canvas_height()
        for vertex, (x, y) in zip(self.vertices, quad):
            vertex.position.x, vertex.position.y = x, height - y
            vertex.color.r, vertex.color.g, vertex.color.b = color
        SDL_RenderGeometry(pico2d_core.renderer, texture, self.vertices, 4, self.indices, 6)

    def draw_cubie(self, cubie, m):
        for face_index, face in enumerate(FACES):
            quad = self.project_face(m, cubie, face_index)
            if signed_area(quad) >= 0:
                continue
            light = AMBIENT + DIFFUSE * max(0, dot(transform(m, face[0]), LIGHT))
            self.draw_quad(None, quad, tuple(int(c * light) for c in BODY_COLOR))
            if face in cubie.stickers:
                self.draw_quad(self.tiles[face[3]].texture, quad, (int(255 * light),) * 3)

    def draw(self):
        # 돌아가는 층과 나머지가 겹치므로, 층 단위로 카메라에서 먼 쪽부터 그린다
        eye = transform(tuple(zip(*self.view)), (0, 0, CAMERA_DISTANCE))

        def draw_order(item):
            cubie, m = item
            distance = math.dist(transform(m, cubie.home), (0, 0, CAMERA_DISTANCE))
            if self.turn is None:
                return -distance
            return -abs(eye[self.turn.axis] - cubie.pos[self.turn.axis]), -distance

        items = [(cubie, self.model_view(cubie)) for cubie in self.cube.cubies]
        for cubie, m in sorted(items, key=draw_order):
            self.draw_cubie(cubie, m)
