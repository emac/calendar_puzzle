from typing import List
import numpy as np
import os
from numpy import ndarray
from tkinter import Canvas

DOT_SIZE = 50

GRID_STATUS_BLANK = 0
GRID_STATUS_CALENDAR = 1
GRID_STATUS_BRICK = 2
GRID_STATUS_FORBIDDEN = 3

COLOR_BLANK = "white"
COLOR_CALENDAR = "yellow"
COLOR_BRICK = "pink"
COLOR_FORBIDDEN = "grey"

BRICK_DIRECTION_0 = 0
BRICK_DIRECTION_90 = 1
BRICK_DIRECTION_180 = 2
BRICK_DIRECTION_270 = 3

MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec", ""]

# 月份所占行数
MONTH_ROW_COUNT = 2


class Grid:
    """坐标点"""

    def __init__(self, x: int, y: int, is_day: bool = False, status: int = GRID_STATUS_BLANK):
        self.x = x
        self.y = y
        self.is_day = is_day
        self.status = status

    def __repr__(self):
        return (self.x, self.y, self.status).__repr__()


class Brick:
    """积木"""

    def __init__(self, width: int, height: int, darray: ndarray, bidirection: bool = False, flippable: bool = True):
        self.width = width
        self.height = height
        self.darray = darray
        self.bidirection = bidirection
        self.flippable = flippable

    def __eq__(self, other):
        if not isinstance(other, Brick):
            return False
        return self.width == other.width and self.height == other.height and np.array_equal(self.darray, other.darray)

    def __hash__(self):
        return hash((self.darray.all()))

    def __repr__(self):
        return self.darray.__repr__()

    def rotate(self) -> "Brick":
        """
        逆时针旋转90°
        @see https://numpy.org/doc/stable/reference/generated/numpy.rot90.html
        """
        return Brick(self.height, self.width, np.rot90(self.darray), self.bidirection, self.flippable)

    def flip(self) -> "Brick":
        """
        水平翻转
        @see https://numpy.org/doc/stable/reference/generated/numpy.flip.html
        """
        assert self.flippable
        return Brick(self.width, self.height, np.flip(self.darray, 1), self.bidirection, self.flippable)

    def calc_left_displacement(self) -> int:
        """
        计算首行第一个非空格移动到首行首格的左移格数
        """
        for i in range(len(self.darray[0])):
            if self.darray[0][i] == 1:
                return i

class BrickSeqFactory:
    "积木集合"

    def __init__(self, bricks: List[Brick], slot: int = -1):
        assert -1 <= slot < os.cpu_count()

        self.__bricks = bricks
        self.__slot = slot
        self.__seqs = self.__init_seqs(len(bricks))
        self.__idx = 0

    def __init_seqs(self, length) -> List[List[int]]:
        """
        初始化全排列序列
        """
        nums = []
        for i in range(length):
            nums.append(i)

        full_seqs = self.__gen_seqs(nums)
        if self.__slot == -1:
            return full_seqs

        seqs = []
        for i, s in enumerate(full_seqs):
            if i % os.cpu_count() == self.__slot:
                seqs.append(s)
        return seqs

    def __gen_seqs(self, nums: List[int]) -> List[List[int]]:
        """
        生成全排列
        @see itertools.permutations
        """
        # fn(1)=1
        if len(nums) == 1:
            return [[nums.pop()]]

        seqs = []
        for n in nums:
            seq = [n]
            nums2 = nums.copy()
            nums2.remove(n)
            for s in self.__gen_seqs(nums2):
                # fn(N) = n + fn(N-1)
                seqs.append(seq + s)
        return seqs

    def next(self) -> List[Brick]:
        """
        返回下一个积木序列
        """
        if self.__idx == len(self.__seqs):
            return []

        seq = []
        for i in self.__seqs[self.__idx]:
            seq.append(self.__bricks[i])
        self.__idx += 1
        return seq


# 积木常量
BRICK_0 = Brick(2, 3, np.array([[1, 1], [1, 1], [1, 1]], int), True, False)
BRICK_1 = Brick(2, 3, np.array([[1, 0], [1, 1], [1, 1]], int), False, True)
BRICK_2 = Brick(2, 3, np.array([[1, 1], [1, 0], [1, 1]], int), False, False)
BRICK_3 = Brick(3, 3, np.array([[1, 1, 0], [0, 1, 0], [0, 1, 1]], int), True, True)
BRICK_4 = Brick(3, 3, np.array([[1, 0, 0], [1, 0, 0], [1, 1, 1]], int), False, False)
BRICK_5 = Brick(2, 4, np.array([[1, 1], [1, 0], [1, 0], [1, 0]], int), False, True)
BRICK_6 = Brick(2, 4, np.array([[1, 0], [1, 1], [1, 0], [1, 0]], int), False, True)
BRICK_7 = Brick(2, 4, np.array([[1, 0], [1, 1], [0, 1], [0, 1]], int), False, True)
BRICKS = [BRICK_0, BRICK_1, BRICK_2, BRICK_3, BRICK_4, BRICK_5, BRICK_6, BRICK_7]


class Board:
    """日历板"""

    def __init__(self, month: int, day: int):
        self.__board = self.__init_board("calendar.data")
        self.__board[int(month / 6)][month % 6] = Grid(month % 6, int(month / 6), False, GRID_STATUS_CALENDAR)
        self.__board[int(day / 7) + 2][day % 7] = Grid(day % 7, int(day / 7) + 2, True, GRID_STATUS_CALENDAR)
        self.__bricks = []

    def __repr__(self):
        result = ""
        for b in self.__bricks:
            result += b[0].__repr__()
            result += "\n"
            result += b[1].__repr__()
            result += "\n"
        return result

    def __init_board(self, file: str) -> List[List[Grid]]:
        data = open(file, "r")
        board = []
        for i, line in enumerate(data):
            row = []
            for j, c in enumerate(line.strip()):
                status = GRID_STATUS_FORBIDDEN if c == "x" else GRID_STATUS_BLANK
                # status = DOT_STATUS_FORBIDDEN if c == "x" else DOT_STATUS_BRICK
                # 行对应y，列对应x
                row.append(Grid(j, i, i >= MONTH_ROW_COUNT, status))
            board.append(row)
        return board

    def find_location(self, brick: Brick) -> Grid:
        location = None
        blanks = []
        for row in self.__board:
            for g in row:
                if g.status == GRID_STATUS_BLANK:
                    if location is None:
                        # 只取第一个空格，保证积木严格按照预定顺序放入
                        location = g
                    blanks.append(g)

        # 根据积木形状移动放置点
        displacement = brick.calc_left_displacement()
        location = Grid(location.x - displacement, location.y)
        if self.__try_place(location, brick, blanks):
            return location
        return None

    def __try_place(self, location: Grid, brick: Brick, blanks: List[Grid]) -> bool:
        # 检查是否越界
        if location.x < 0 or (location.x + brick.width - 1) >= 7 or (location.y + brick.height - 1) >= 7:
            return False

        # 检查是否都是空格
        blanks = blanks.copy()
        for y, row in enumerate(brick.darray):
            for x, g in enumerate(row):
                if g == 1:
                    if self.__board[y + location.y][x + location.x].status != GRID_STATUS_BLANK:
                        return False
                    blanks.remove(self.__board[y + location.y][x + location.x])

        # 检查是否有孤立的非法空白区域
        for zone in self.__divide_zones(blanks):
            length = len(zone)
            if length % 5 > 1:
                return False
            if length == 1:
                return False
            if length == 6:
                # 6格的合法空白区域只有BRICK_0一种
                border = self.__calc_zone_board(zone)
                width = border[0] - border[1] + 1
                height = border[2] - border[3] + 1
                if width * height != 6:
                    return False
                if width == 1 or width == 6:
                    return False
                if self.__is_eq(brick, BRICK_0) or self.__is_used(BRICK_0):
                    return False
            if length == 5:
                border = self.__calc_zone_board(zone)
                width = border[0] - border[1] + 1
                if width == 1 or width == 5:
                    return False
                # 用空白区域构造一个伪积木，注意伪积木不能旋转和翻转
                fake_brick = self.__build_fake_brick(zone)
                if not self.__is_valid_brick(fake_brick):
                    return False
                if self.__is_eq(brick, fake_brick) or self.__is_used(fake_brick):
                    return False
        return True

    def __build_fake_brick(self, zone: List[Grid]) -> Brick:
        border = self.__calc_zone_board(zone)
        width = border[0] - border[1] + 1
        height = border[2] - border[3] + 1
        grids = []
        # 初始化（全置0）
        for r in range(height):
            row = []
            grids.append(row)
            for c in range(width):
                row.append(0)
        # 置1
        for g in zone:
            grids[g.y - border[3]][g.x - border[1]] = 1

        return Brick(width, height, np.array(grids, int))

    def __is_valid_brick(self, brick: Brick) -> bool:
        for b1 in BRICKS:
            for b2 in self.split_bricks(b1, False):
                if brick == b2:
                    return True
        return False

    def __is_eq(self, source: Brick, target: Brick) -> bool:
        for b in self.split_bricks(source, False):
            if b == target:
                return True
        return False

    def __is_used(self, brick: Brick) -> bool:
        for b in self.__bricks:
            if self.__is_eq(b[1], brick):
                return True
        return False

    def split_bricks(self, raw: Brick, flipped: bool) -> List[Brick]:
        bricks = [raw]
        if raw.bidirection:
            bricks.append(raw.rotate())
        else:
            _raw = raw.rotate()
            bricks.append(_raw)
            _raw = _raw.rotate()
            bricks.append(_raw)
            _raw = _raw.rotate()
            bricks.append(_raw)

        if raw.flippable and not flipped:
            bricks = bricks + self.split_bricks(raw.flip(), not flipped)
        return bricks

    def __calc_zone_board(self, zone: List[Grid]) -> tuple:
        # max取最小值，min取最大值，逐步收敛
        max_x = 0
        min_x = 6
        max_y = 0
        min_y = 6
        for g in zone:
            max_x = max(max_x, g.x)
            min_x = min(min_x, g.x)
            max_y = max(max_y, g.y)
            min_y = min(min_y, g.y)
        return max_x, min_x, max_y, min_y

    def __divide_zones(self, blanks: List[Grid]) -> List[List[Grid]]:
        zones = []
        while len(blanks) > 0:
            # 新建一个空白区域
            head = blanks.pop(0)
            queue = [head]
            zone = []
            zones.append(zone)
            while len(queue) > 0:
                grid = queue.pop(0)
                zone.append(grid)

                right = (grid.y <= 1 and grid.x == 5) or (grid.y > 1 and grid.x == 6)
                if not right:
                    right_neighbour = self.__board[grid.y][grid.x + 1]
                bottom = (grid.x <= 2 and grid.y == 6) or (grid.x > 2 and grid.y == 5)
                if not bottom:
                    bottom_neighbour = self.__board[grid.y + 1][grid.x]
                left = grid.x == 0
                if not left:
                    left_neighbour = self.__board[grid.y][grid.x - 1]
                top = (grid.x <= 5 and grid.y == 0) or (grid.x == 6 and grid.y == 2)
                if not top:
                    top_neighbour = self.__board[grid.y - 1][grid.x]

                if not right and right_neighbour in blanks:
                    self.__move(right_neighbour, blanks, queue)
                if not bottom and bottom_neighbour in blanks:
                    self.__move(bottom_neighbour, blanks, queue)
                if not left and left_neighbour in blanks:
                    self.__move(left_neighbour, blanks, queue)
                if not top and top_neighbour in blanks:
                    self.__move(top_neighbour, blanks, queue)
        return zones

    def __move(self, grid: Grid, source: List[Grid], target: List[Grid]):
        source.remove(grid)
        target.append(grid)

    def place(self, location: Grid, brick: Brick):
        self.__bricks.append((location, brick))
        # 填充积木格
        for y, row in enumerate(brick.darray):
            for x, g in enumerate(row):
                if g == 1:
                    self.__replace_grid(
                        Grid(x + location.x, y + location.y, (y + location.y) >= MONTH_ROW_COUNT, GRID_STATUS_BRICK))

    def unplace(self):
        lb = self.__bricks.pop()
        location = lb[0]
        brick = lb[1]
        # 恢复空格
        for y, row in enumerate(brick.darray):
            for x, g in enumerate(row):
                if g == 1:
                    self.__replace_grid(
                        Grid(x + location.x, y + location.y, (y + location.y) >= MONTH_ROW_COUNT, GRID_STATUS_BLANK))

    def __replace_grid(self, grid: Grid):
        self.__board[grid.y][grid.x] = grid

    def draw(self, canvas: Canvas):
        # 画底板
        for row in self.__board:
            for g in row:
                # 标签
                if not g.is_day:
                    label = MONTHS[g.y * 7 + g.x]
                else:
                    label = (g.y - 2) * 7 + g.x + 1
                    if label > 31:
                        label = ""
                    else:
                        label = str(label)
                # 背景色
                if g.status == GRID_STATUS_BLANK:
                    color = COLOR_BLANK
                elif g.status == GRID_STATUS_CALENDAR:
                    color = COLOR_CALENDAR
                elif g.status == GRID_STATUS_BRICK:
                    color = COLOR_BRICK
                else:
                    color = COLOR_FORBIDDEN
                # 填充背景色
                canvas.create_rectangle(g.x * DOT_SIZE, g.y * DOT_SIZE,
                                        (g.x + 1) * DOT_SIZE, (g.y + 1) * DOT_SIZE, fill=color, outline="")
                # 写标签
                canvas.create_text(g.x * DOT_SIZE + DOT_SIZE / 2, g.y * DOT_SIZE + DOT_SIZE / 2, text=label)
        # 积木描边
        for b in self.__bricks:
            self.__draw_brick(canvas, b[0], b[1])

    def __draw_brick(self, canvas: Canvas, location: Grid, brick: Brick):
        # 计算外廓（相对坐标）
        lines = []
        for y, row in enumerate(brick.darray):
            for x, g in enumerate(row):
                if g == 0:
                    # 空格
                    continue
                if x == 0 or brick.darray[y][x - 1] == 0:
                    # 添加左边
                    lines.append((Grid(x * DOT_SIZE, y * DOT_SIZE), Grid(x * DOT_SIZE, (y + 1) * DOT_SIZE)))

                if x == brick.width - 1 or brick.darray[y][x + 1] == 0:
                    # 添加右边
                    lines.append((Grid((x + 1) * DOT_SIZE, y * DOT_SIZE), Grid((x + 1) * DOT_SIZE, (y + 1) * DOT_SIZE)))

                if y == 0 or brick.darray[y - 1][x] == 0:
                    # 添加上边
                    lines.append((Grid(x * DOT_SIZE, y * DOT_SIZE), Grid((x + 1) * DOT_SIZE, y * DOT_SIZE)))

                if y == brick.height - 1 or brick.darray[y + 1][x] == 0:
                    # 添加下边
                    lines.append((Grid(x * DOT_SIZE, (y + 1) * DOT_SIZE), Grid((x + 1) * DOT_SIZE, (y + 1) * DOT_SIZE)))

        for l in lines:
            # 平移外廓（绝对坐标）
            start = Grid(l[0].x + location.x * DOT_SIZE, l[0].y + location.y * DOT_SIZE)
            end = Grid(l[1].x + location.x * DOT_SIZE, l[1].y + location.y * DOT_SIZE)
            # 画线
            canvas.create_line(start.x, start.y, end.x, end.y, fill="black")


if __name__ == '__main__':
    '''test01: BrickSeqFactory'''
    # factory = BrickSeqFactory(BRICKS)
    # while True:
    #     bricks = factory.next()
    #     if len(bricks) == 0:
    #         # 已遍历完所有可能
    #         break
    #     print(bricks)
    '''test02: Brick'''
    # assert BRICK_5 != BRICK_6
    # assert BRICK_1.rotate() != BRICK_1.flip().rotate().flip().rotate()
    # assert BRICK_1.rotate() == BRICK_1.flip().rotate().flip().rotate().rotate()
    '''test03: Board'''
    # board = Board(1, 17)
    # board.draw()
