"""고를 수 있는 마스코트 캐릭터 목록과 선택 저장 (pico2d를 쓰지 않는다)"""
import os

# (폴더 이름, 화면에 보일 이름)
CHARACTERS = [('bot', '큐브봇'), ('cat', '박스냥'), ('slime', '젤리')]
DEFAULT = 'bot'
SLIME_COLOR = 'green'      # 지정 색이 없을 때(타이틀 등) 젤리 색
CHOICE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'character.txt')

KEYS = [key for key, _ in CHARACTERS]


def name_of(key):
    return dict(CHARACTERS)[key]


def load():
    """저장된 캐릭터. 파일이 없거나 이상하면 기본 캐릭터"""
    try:
        with open(CHOICE_FILE, encoding='utf-8') as f:
            key = f.read().strip()
    except OSError:
        return DEFAULT
    return key if key in KEYS else DEFAULT


def save(key):
    if key not in KEYS:
        return
    try:
        with open(CHOICE_FILE, 'w', encoding='utf-8') as f:
            f.write(key)
    except OSError:
        pass


def step(key, delta):
    """목록에서 delta만큼 옆 캐릭터 (끝에서는 반대쪽으로 돈다)"""
    return KEYS[(KEYS.index(key) + delta) % len(KEYS)]


def sheet_path(key, state, color=None):
    """assets/pixel 기준 시트 경로 (확장자 없이). 젤리만 색 폴더가 있다."""
    if key == 'slime':
        return 'mascot/slime/%s/mascot_%s' % (color or SLIME_COLOR, state)
    return 'mascot/%s/mascot_%s' % (key, state)
