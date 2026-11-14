"""모드 전환 (수업 구조). 모드는 init/finish/pause/resume/handle_events/update/draw를 가진 모듈이다.
스택에 쌓인 모드는 아래부터 모두 그리고, 맨 위 모드만 입력과 업데이트를 받는다."""
from pico2d import clear_canvas, update_canvas, get_events, get_time, SDL_QUIT

running = False
stack = []


def change_mode(mode):
    """쌓인 모드를 모두 끝내고 mode 하나로 바꾼다"""
    while stack:
        stack.pop().finish()
    stack.append(mode)
    mode.init()


def push_mode(mode):
    if stack:
        stack[-1].pause()
    stack.append(mode)
    mode.init()


def pop_mode():
    if stack:
        stack.pop().finish()
    if stack:
        stack[-1].resume()


def quit():
    global running
    running = False


def run(start_mode):
    global running
    running = True
    change_mode(start_mode)

    last_time = get_time()
    while running:
        now = get_time()
        frame_time = min(now - last_time, 0.1)   # 창을 끌다 멈춘 경우 등 큰 값 방지
        last_time = now

        events = get_events()
        if any(event.type == SDL_QUIT for event in events):
            quit()
            break
        mode = stack[-1]
        mode.handle_events(events)
        if stack and stack[-1] is mode:
            mode.update(frame_time)

        clear_canvas()
        for m in list(stack):
            m.draw()
        update_canvas()

    while stack:
        stack.pop().finish()
