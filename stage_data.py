"""스테이지 맵 저장/불러오기 (로직 전용, pico2d 없음)

stages.json 한 파일에 스테이지 번호별로 저장한다. 게임을 껐다 켜도 남는다.
{
  "1": {"turns": 10, "goal_lines": 3,
        "cells": [[null, ["block", "red"], ["obstacle", 2], ...], ...]   # 8x8, [0]이 맨 위 줄
  },
  ...
}
칸 값은 board.Board와 같다: None(빈칸) / ["block", 색] / ["obstacle", 내구도]
"""
import json
import os

from config import BOARD_SIZE, COLORS

STAGE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'stages.json')
DEFAULT_TURNS = 10
DEFAULT_GOAL_LINES = 3
TURNS_RANGE = (1, 99)
GOAL_RANGE = (1, 99)


def empty_stage():
    return {'turns': DEFAULT_TURNS, 'goal_lines': DEFAULT_GOAL_LINES,
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
    cells = stage.get('cells') or []
    for r, row in enumerate(cells[:BOARD_SIZE]):
        for c, cell in enumerate(row[:BOARD_SIZE]):
            if not (isinstance(cell, list) and len(cell) == 2):
                continue
            kind, value = cell
            if (kind == 'block' and value in COLORS) or (kind == 'obstacle' and value in (1, 2, 3)):
                result['cells'][r][c] = (kind, value)
    return result


def clamp(value, low, high):
    return max(low, min(high, value))


def load(stage):
    return load_all().get(stage, empty_stage())


def has_map(stage):
    return stage in load_all()


def save(stage, data):
    """한 스테이지를 저장한다. 임시 파일에 쓰고 바꿔치기해서, 쓰다가 꺼져도 기존 파일이 깨지지 않는다."""
    all_stages = load_all()
    all_stages[stage] = data
    serializable = {str(k): {'turns': v['turns'], 'goal_lines': v['goal_lines'],
                             'cells': [[list(cell) if cell else None for cell in row] for row in v['cells']]}
                    for k, v in sorted(all_stages.items())}
    tmp = STAGE_FILE + '.tmp'
    with open(tmp, 'w', encoding='utf-8') as f:
        json.dump(serializable, f, ensure_ascii=False, indent=1)
    os.replace(tmp, STAGE_FILE)
