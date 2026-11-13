from pico2d import *

from settings import WIDTH, HEIGHT
from character import Magician
from cube_view import CubeView

BACKGROUND = (238, 236, 247)

running = True
magician = None
cube_view = None
world = []   # 화면에 그릴 객체들 (리스트 앞쪽이 먼저 그려짐 → 배경은 앞에 추가)


def handle_events():
    global running
    for event in get_events():
        if event.type == SDL_QUIT:
            running = False
        elif event.type == SDL_KEYDOWN and event.key == SDLK_ESCAPE:
            running = False
        else:
            cube_view.handle_event(event)
            magician.handle_event(event)


def init():
    global magician, cube_view
    hide_lattice()
    cube_view = CubeView()
    magician = Magician()
    # 나중에 배경 추가 시: world.append(Background()) 를 캐릭터보다 먼저
    world.append(cube_view)
    world.append(magician)


def update(dt):
    for obj in world:
        obj.update(dt)


def draw():
    clear_canvas()
    draw_rectangle(0, 0, WIDTH, HEIGHT, *BACKGROUND, 255, True)
    for obj in world:
        obj.draw()
    update_canvas()


def main():
    open_canvas(WIDTH, HEIGHT, sync=True)
    init()

    last_time = get_time()
    while running:
        now = get_time()
        dt = now - last_time
        last_time = now

        handle_events()
        update(dt)
        draw()

    close_canvas()


if __name__ == '__main__':
    main()
