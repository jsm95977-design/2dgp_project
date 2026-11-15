"""스테이지 모드 오프닝 대본과 지역 정보.

pico2d를 쓰지 않는 순수 데이터 파일입니다. 대사를 고치거나 지역을 추가할 때는 이 파일만 바꾸면 됩니다.
- 대사 한 줄 = (말하는 사람, 문장). 말하는 사람이 None이면 내레이션(이름표 없음)
- 문장 안의 '\n'은 대사 상자 안에서 줄바꿈 (한 화면에 최대 2줄, 한 줄 25자 안팎)
"""

OPENING = [
    {'image': 'story/scene_1.png', 'lines': [
        (None, '알록달록한 큐브들이 모여 사는 곳,\n큐브마을.'),
        (None, '마을 한가운데에는 마을을 환하게\n지켜 주는 \'마을 큐브\'가 있어요.'),
        ('큐비', '오늘도 마을 큐브가 반짝반짝하네!'),
        ('큐비', '그런데 왜 한쪽 귀퉁이만 비어 있을까?\n왠지 자꾸 눈길이 간단 말이야.'),
    ]},
    {'image': 'story/scene_2.png', 'lines': [
        (None, '그러던 어느 날,\n하늘이 갑자기 어두워지더니…'),
        (None, '회색 블록이 비처럼\n쏟아지기 시작했어요!'),
        ('큐비', '으앗! 이게 다 뭐야?!'),
    ]},
    {'image': 'story/scene_3.png', 'lines': [
        (None, '쾅! 회색 블록에 맞은 마을 큐브가\n산산조각 나 버렸어요.'),
        (None, '흩어진 조각들은 반짝이며\n저 멀리 지구와 우주로 날아갔어요.'),
        ('큐비', '안 돼! 조각들아, 어디 가는 거야!'),
    ]},
    {'image': 'story/scene_4.png', 'lines': [
        (None, '마을 큐브를 잃은 마을은\n점점 회색으로 물들어 갔어요.'),
        ('큐비', '모두 색이 바래고 있어…'),
        ('큐비', '이대로 둘 순 없어.\n내가 조각을 전부 찾아올 거야!'),
    ]},
    {'image': 'story/scene_5.png', 'lines': [
        (None, '이렇게 큐비의 조각 찾기 여행이\n시작되었어요.'),
        ('큐비', '먼저 마을을 덮은 회색 블록부터\n치우자. 출발!'),
    ]},
]

# 지역마다 보여 줄 이야기 (지역 선택의 '스토리 보기' 버튼). 없는 지역은 아직 준비 중
STORIES = {'village': OPENING}

# 이름표 이미지 (내레이션은 이름표 없음)
NAME_PLATES = {'큐비': 'story/name_kubi.png'}

# 지역 순서대로. 앞 지역의 마지막 스테이지를 깨면 다음 지역이 열린다.
REGIONS = [
    {'key': 'village', 'name': '큐브마을', 'stages': 20},
    {'key': 'earth',   'name': '지구',     'stages': 30},
    {'key': 'space',   'name': '우주',     'stages': 30},   # 스테이지 수는 아직 미정
]


def region_files(key):
    """지역 하나에 쓰는 이미지 경로."""
    return {
        'icon': f'region/icon_{key}.png',
        'icon_hover': f'region/icon_{key}_hover.png',
        'icon_locked': f'region/icon_{key}_locked.png',
        'name': f'region/name_{key}.png',
        'name_locked': f'region/name_{key}_locked.png',
        'bg': f'region/bg_{key}.png',          # 그 지역의 스테이지 선택 배경
    }


def is_unlocked(region_index, cleared):
    """cleared[i] = i번째 지역에서 깬 스테이지 수."""
    if region_index == 0:
        return True
    prev = REGIONS[region_index - 1]
    return cleared[region_index - 1] >= prev['stages']


# ---------- 스테이지 번호 ↔ 지역 ----------
# 스테이지 번호는 지역을 이어서 매긴다: 큐브마을 1~20, 지구 21~50, 우주 51~80
# (stages.json, stage_progress.json은 이 전체 번호를 쓴다)

def first_stage(region_index):
    """그 지역 첫 스테이지의 전체 번호"""
    return 1 + sum(r['stages'] for r in REGIONS[:region_index])


def stage_numbers(region_index):
    first = first_stage(region_index)
    return range(first, first + REGIONS[region_index]['stages'])


def total_stages():
    return sum(r['stages'] for r in REGIONS)


def region_of(stage):
    """전체 번호 → (지역 번호, 지역 안 번호 1부터)"""
    for i in range(len(REGIONS)):
        if stage in stage_numbers(i):
            return i, stage - first_stage(i) + 1
    return len(REGIONS) - 1, stage - first_stage(len(REGIONS) - 1) + 1


def stage_label(stage):
    """화면에 보일 스테이지 이름 (예: '지구 3')"""
    i, local = region_of(stage)
    return '%s %d' % (REGIONS[i]['name'], local)


def cleared_counts(progress):
    """지역마다 깬(별 1개 이상) 스테이지 수. progress는 stage_data.load_progress()"""
    return [sum(1 for s in stage_numbers(i) if progress.get(s, {}).get('stars', 0) > 0)
            for i in range(len(REGIONS))]


# ---------- 오프닝을 봤는지 (최고 기록처럼 파일에 저장) ----------
import os

OPENING_SEEN_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'opening_seen.txt')


def opening_seen():
    return os.path.exists(OPENING_SEEN_FILE)


def mark_opening_seen():
    try:
        with open(OPENING_SEEN_FILE, 'w', encoding='utf-8') as f:
            f.write('1')
    except OSError:
        pass
