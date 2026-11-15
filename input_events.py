"""입력 이벤트 읽기: pico2d.get_events()와 같고, 글자 입력(한글 조합 포함) 이벤트를 더 넘겨준다.

pico2d.get_events()는 SDL_TEXTINPUT / SDL_TEXTEDITING을 버려서 한글을 입력받을 수 없다.
- SDL_TEXTINPUT   : 확정된 글자.  event.text
- SDL_TEXTEDITING : 조합 중인 글자 (예: 'ㅎ' → '하' → '한'). event.text (빈 문자열이면 조합 끝)
- 백스페이스는 꾹 누르면 반복되게 반복 입력도 넘긴다 (다른 키의 반복은 예전처럼 버린다)

글자 입력은 평소에는 꺼 두고, 입력칸을 편집할 때만 start_text_input()으로 켠다.
(켜 두면 한글 입력기가 Q/E 같은 조작 키를 조합 글자로 가로챌 수 있다)
"""
import ctypes

from pico2d import (SDL_Event, SDL_PollEvent, SDL_Delay, SDL_QUIT, SDL_KEYDOWN, SDL_KEYUP, SDL_MOUSEMOTION,
                    SDL_MOUSEBUTTONDOWN, SDL_MOUSEBUTTONUP, SDL_MOUSEWHEEL, SDLK_BACKSPACE)
from pico2d.pico2d import Event, print_fps
from sdl2 import SDL_TEXTINPUT, SDL_TEXTEDITING, SDL_StartTextInput, SDL_StopTextInput, SDL_IsTextInputActive


def get_events():
    print_fps()
    SDL_Delay(1)
    sdl_event = SDL_Event()
    events = []
    while SDL_PollEvent(ctypes.byref(sdl_event)):
        t = sdl_event.type
        event = Event(t)
        if t == SDL_QUIT:
            events.append(event)
        elif t in (SDL_KEYDOWN, SDL_KEYUP):
            key = sdl_event.key.keysym.sym
            if not sdl_event.key.repeat or (t == SDL_KEYDOWN and key == SDLK_BACKSPACE):
                event.key = key
                events.append(event)
        elif t == SDL_MOUSEMOTION:
            event.x, event.y = sdl_event.motion.x, sdl_event.motion.y
            events.append(event)
        elif t in (SDL_MOUSEBUTTONDOWN, SDL_MOUSEBUTTONUP):
            event.button, event.x, event.y = sdl_event.button.button, sdl_event.button.x, sdl_event.button.y
            events.append(event)
        elif t == SDL_MOUSEWHEEL:
            event.x, event.y = sdl_event.wheel.x, sdl_event.wheel.y   # 휠은 위치 대신 굴린 양
            events.append(event)
        elif t == SDL_TEXTINPUT:
            event.text = sdl_event.text.text.decode('utf-8', 'ignore')
            events.append(event)
        elif t == SDL_TEXTEDITING:
            event.text = sdl_event.edit.text.decode('utf-8', 'ignore')
            events.append(event)
    return events


def start_text_input():
    SDL_StartTextInput()


def stop_text_input():
    SDL_StopTextInput()


def text_input_active():
    return bool(SDL_IsTextInputActive())
