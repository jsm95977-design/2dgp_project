from pico2d import *

from cube_view import CubeView

WIDTH, HEIGHT = 800, 600
BACKGROUND = (238, 236, 247)


def main():
    open_canvas(WIDTH, HEIGHT, sync=True)
    hide_lattice()
    cube_view = CubeView()

    running = True
    last_time = get_time()
    while running:
        now = get_time()
        frame_time = now - last_time
        last_time = now

        for event in get_events():
            if event.type == SDL_QUIT or (event.type == SDL_KEYDOWN and event.key == SDLK_ESCAPE):
                running = False
            else:
                cube_view.handle_event(event)

        cube_view.update(frame_time)

        clear_canvas()
        draw_rectangle(0, 0, WIDTH, HEIGHT, *BACKGROUND, 255, True)
        cube_view.draw()
        update_canvas()

    close_canvas()


if __name__ == '__main__':
    main()
