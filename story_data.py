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
