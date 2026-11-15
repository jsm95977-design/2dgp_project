"""스테이지 맵 저장/불러오기 (로직 전용, pico2d 없음)

stages.json 한 파일에 스테이지 번호별로 저장한다. 게임을 껐다 켜도 남는다.
{
  "1": {"turns": 10, "goal_lines": 3, "message": "말풍선 대사",
        "cells": [[null, ["block", "red"], ["obstacle", 2], ...], ...]   # 8x8, [0]이 맨 위 줄
  },
  ...
}
칸 값은 board.Board와 같다: None(빈칸) / ["block", 색] / ["obstacle", 내구도]
특수 블록: ["steel", 0] / ["bomb", 1~3] / ["sun", 0] / ["moon", 0]
"""
import json
import os

from config import BOARD_SIZE, COLORS

STAGE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'stages.json')
PROGRESS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'stage_progress.json')   # 클리어 기록
DEFAULT_TURNS = 10
DEFAULT_GOAL_LINES = 3
TURNS_RANGE = (1, 99)
GOAL_RANGE = (1, 99)
MESSAGE_MAX = 40          # 말풍선 대사 최대 글자 수 (말풍선 3줄)


def empty_stage():
    return {'turns': DEFAULT_TURNS, 'goal_lines': DEFAULT_GOAL_LINES, 'message': '',
            'cells': [[None] * BOARD_SIZE for _ in range(BOARD_SIZE)]}


def load_all():
    try:
        with open(STAGE_FILE, encoding='utf-8') as f:
            data = json.load(f)
    except (OSError, ValueError):
        return {}
    return {int(k): normalize(v) for k, v in data.items()}


def normalize(stage):
    """파일에서 읽은 값을 검사해 빠진 값은 기본값으로 채운다 (손으로 고친 파일 대비)"""
    result = empty_stage()
    result['turns'] = clamp(int(stage.get('turns', DEFAULT_TURNS)), *TURNS_RANGE)
    result['goal_lines'] = clamp(int(stage.get('goal_lines', DEFAULT_GOAL_LINES)), *GOAL_RANGE)
    message = stage.get('message', '')
    result['message'] = message[:MESSAGE_MAX] if isinstance(message, str) else ''
    cells = stage.get('cells') or []
    for r, row in enumerate(cells[:BOARD_SIZE]):
        for c, cell in enumerate(row[:BOARD_SIZE]):
            if not (isinstance(cell, list) and len(cell) == 2):
                continue
            kind, value = cell
            if valid_cell(kind, value):
                result['cells'][r][c] = (kind, value)
    return result


VALID_VALUES = {
    'obstacle': (1, 2, 3),
    'steel': (0,),
    'bomb': (1, 2, 3),       # 남은 턴
    'sun': (0,),             # 맵에서는 항상 활성화 전
    'moon': (0,),            # 맵에서는 항상 빈 달에서 시작
}


def valid_cell(kind, value):
    if kind == 'block':
        return value in COLORS
    return value in VALID_VALUES.get(kind, ())


def clamp(value, low, high):
    return max(low, min(high, value))


def load(stage):
    return load_all().get(stage, empty_stage())


def has_map(stage):
    return stage in load_all()


def load_progress():
    """클리어 기록 {스테이지: {'stars': 0~3, 'best': 최고 점수}}"""
    try:
        with open(PROGRESS_FILE, encoding='utf-8') as f:
            raw = json.load(f)
        return {int(k): {'stars': int(v.get('stars', 0)), 'best': int(v.get('best', 0))} for k, v in raw.items()}
    except (OSError, ValueError, AttributeError):
        return {}


def record_result(stage, stars, score):
    """별과 점수는 더 좋을 때만 덮어쓴다 (실패는 stars=0)"""
    progress = load_progress()
    old = progress.get(stage, {'stars': 0, 'best': 0})
    progress[stage] = {'stars': max(old['stars'], stars), 'best': max(old['best'], score)}
    write_json(PROGRESS_FILE, {str(k): v for k, v in sorted(progress.items())})


def write_json(path, value):
    """임시 파일에 쓰고 바꿔치기해서, 쓰다가 꺼져도 기존 파일이 깨지지 않게 한다"""
    tmp = path + '.tmp'
    with open(tmp, 'w', encoding='utf-8') as f:
        json.dump(value, f, ensure_ascii=False, indent=1)
    os.replace(tmp, path)


def save(stage, data):
    """한 스테이지를 저장한다. 임시 파일에 쓰고 바꿔치기해서, 쓰다가 꺼져도 기존 파일이 깨지지 않는다."""
    all_stages = load_all()
    all_stages[stage] = data
    serializable = {str(k): {'turns': v['turns'], 'goal_lines': v['goal_lines'], 'message': v.get('message', ''),
                             'cells': [[list(cell) if cell else None for cell in row] for row in v['cells']]}
                    for k, v in sorted(all_stages.items())}
    write_json(STAGE_FILE, serializable)
