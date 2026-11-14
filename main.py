from pico2d import open_canvas, close_canvas, hide_lattice

import game_framework
import title_mode
from settings import WIDTH, HEIGHT


def main():
    open_canvas(WIDTH, HEIGHT, sync=True)
    hide_lattice()
    game_framework.run(title_mode)
    close_canvas()


if __name__ == '__main__':
    main()
