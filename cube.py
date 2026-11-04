# 3x3 큐브 상태. 좌표계: x 오른쪽(R), y 위(U), z 앞(F)

# 면마다 (바깥 법선, 텍스처 오른쪽, 텍스처 위, 색)
FACES = (
    (( 0,  0,  1), ( 1, 0,  0), (0, 1,  0), 'green'),   # F
    (( 0,  0, -1), (-1, 0,  0), (0, 1,  0), 'blue'),    # B
    (( 1,  0,  0), ( 0, 0, -1), (0, 1,  0), 'red'),     # R
    ((-1,  0,  0), ( 0, 0,  1), (0, 1,  0), 'orange'),  # L
    (( 0,  1,  0), ( 1, 0,  0), (0, 0, -1), 'white'),   # U
    (( 0, -1,  0), ( 1, 0,  0), (0, 0,  1), 'yellow'),  # D
)

IDENTITY = ((1, 0, 0), (0, 1, 0), (0, 0, 1))
QUARTERS = ((1, 0), (0, 1), (-1, 0), (0, -1))  # 90도 단위 (cos, sin)


def rotation(axis, cos, sin):
    a, b = (axis + 1) % 3, (axis + 2) % 3
    m = [[0, 0, 0], [0, 0, 0], [0, 0, 0]]
    m[axis][axis] = 1
    m[a][a], m[a][b] = cos, -sin
    m[b][a], m[b][b] = sin, cos
    return m


def mat_mul(a, b):
    return tuple(tuple(sum(a[r][k] * b[k][c] for k in range(3)) for c in range(3)) for r in range(3))


def transform(m, v):
    return tuple(m[r][0] * v[0] + m[r][1] * v[1] + m[r][2] * v[2] for r in range(3))


class Cubie:
    def __init__(self, home):
        self.home = home
        self.pos = home
        self.rot = IDENTITY
        self.stickers = [face for face in FACES if sum(h * n for h, n in zip(home, face[0])) == 1]


class Cube:
    def __init__(self):
        self.cubies = [Cubie((x, y, z))
                       for x in (-1, 0, 1) for y in (-1, 0, 1) for z in (-1, 0, 1)
                       if (x, y, z) != (0, 0, 0)]

    def turn(self, axis, layer, quarters):
        """axis(0:x 1:y 2:z)의 양의 방향을 기준으로 layer 층을 반시계로 90도 x quarters 만큼 돌린다."""
        m = rotation(axis, *QUARTERS[quarters % 4])
        for cubie in self.cubies:
            if cubie.pos[axis] == layer:
                cubie.pos = transform(m, cubie.pos)
                cubie.rot = mat_mul(m, cubie.rot)
