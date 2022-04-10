import threading
import datetime
import time
import tkinter as tk
import tkinter.ttk
from model import *

failed_prefixes = {int: []}
tries = 0
answer: Board = None


def reset():
    """
    重置棋盘
    """
    global failed_prefixes
    global tries
    global answer

    failed_prefixes = {int: []}
    tries = 0
    answer = None


def parallel_main(canvas: Canvas, month: int, day: int) -> (float, int):
    """
    多线程解谜
    """
    reset()

    start_time = time.time()
    workers = []
    for i in range(os.cpu_count()):
        worker = Worker(month, day, i)
        worker.start()
        workers.append(worker)
    for w in workers:
        w.join()
    if answer is not None:
        answer.draw(canvas)
        return (time.time() - start_time), tries
    else:
        return None


class Worker(threading.Thread):
    def __init__(self, month: int, day: int, slot: int):
        threading.Thread.__init__(self)
        self.__slot = slot
        self.__board = Board(month, day)
        self.__factory = BrickSeqFactory(BRICKS, slot)

    def run(self):
        print("[Worker-%s] Started" % self.__slot)
        global answer
        while answer is None:
            bricks = self.__factory.next()
            if len(bricks) == 0:
                # 已遍历完所有可能
                break
            brick_seq = []
            if self.__place_brick(self.__board, brick_seq, bricks, 0):
                # 找到一个解
                answer = self.__board
                break

    def __place_brick(self, board: Board, brick_seq: List[Brick], bricks: List[Brick], idx: int) -> bool:
        global tries
        if idx == len(bricks):
            return True

        # 检查是否包含失败前缀
        if has_failed_prefix(brick_seq, bricks, idx):
            return False

        placed = False
        for b in board.split_bricks(bricks[idx], False):
            loc = board.find_location(b)
            if loc is None:
                continue

            tries += 1
            if tries % 10000 == 0:
                print("[Worker-%s] %s: %s" % (self.__slot, time.asctime(time.localtime(time.time())), tries))

            placed = True
            brick_seq.append(b)
            board.place(loc, b)
            if self.__place_brick(board, brick_seq, bricks, idx + 1):
                return True
            board.unplace()
            brick_seq.pop()

        if not placed:
            # 新的失败前缀
            add_failed_prefix(brick_seq, bricks, idx)

        return False


def main(month: int, day: int):
    """
    单线程解谜（用于Debug）
    """
    reset()

    start_time = time.time()
    board = Board(month, day)
    factory = BrickSeqFactory(BRICKS)
    while True:
        bricks = factory.next()
        if len(bricks) == 0:
            # 已遍历完所有可能
            break
        brick_seq = []
        if place_brick(board, brick_seq, bricks, 0):
            print("\nA solution is found after %s seconds!" % (time.time() - start_time))
            board.draw()
            exit()
    print("\nSomething is wrong... No solution is found!")


def place_brick(board: Board, brick_seq: List[Brick], bricks: List[Brick], idx: int) -> bool:
    if idx == len(bricks):
        return True

    # 检查是否包含失败前缀
    if has_failed_prefix(brick_seq, bricks, idx):
        return False

    placed = False
    for b in board.split_bricks(bricks[idx], False):
        loc = board.find_location(b)
        if loc is None:
            continue

        placed = True
        brick_seq.append(b)
        board.place(loc, b)
        print(board)
        board.draw(1000)
        if place_brick(board, brick_seq, bricks, idx + 1):
            return True
        board.unplace()
        brick_seq.pop()

    if not placed:
        # 新的失败前缀
        add_failed_prefix(brick_seq, bricks, idx)

    return False


def has_failed_prefix(brick_seq: List[Brick], bricks: List[Brick], idx: int) -> bool:
    prefix = get_prefix(brick_seq, bricks, idx)
    if failed_prefixes.get(idx + 1) is None:
        return False
    else:
        return prefix in failed_prefixes.get(idx + 1)


def add_failed_prefix(brick_seq: List[Brick], bricks: List[Brick], idx: int):
    prefix = get_prefix(brick_seq, bricks, idx)
    if failed_prefixes.get(idx + 1) is None:
        failed_prefixes[idx + 1] = [prefix]
    else:
        failed_prefixes.get(idx + 1).append(prefix)


def get_prefix(brick_seq: List[Brick], bricks: List[Brick], idx: int) -> List[Brick]:
    brick_seq = brick_seq.copy()
    brick_seq.append(bricks[idx])
    return brick_seq


if __name__ == '__main__':
    window = tk.Tk()
    window.title("Calendar Puzzle")
    # 初始化资源
    puzzle_img = tk.PhotoImage(file="calendar.png")
    puzzle_canvas = None
    prompt_frame = None
    result_canvas = None


    def start(*args):
        global puzzle_canvas
        global prompt_frame
        if puzzle_canvas is not None:
            puzzle_canvas.destroy()
        if prompt_frame is not None:
            prompt_frame.destroy()
        if result_canvas is not None:
            result_canvas.destroy()

        # 获取月份和日期
        puzzle_canvas = tk.Canvas(window, height=200)
        puzzle_canvas.pack()
        puzzle_canvas.create_image(150, 100, image=puzzle_img)

        prompt_frame = tk.Frame(window)
        prompt_frame.pack()

        today = datetime.datetime.today()
        month_label = tk.Label(prompt_frame, text="月份：")
        month_label.grid(row=0, column=0)
        month = tk.StringVar()
        month.set(today.month)
        month_entry = tk.Entry(prompt_frame, textvariable=month)
        month_entry.grid(row=0, column=1)
        month_entry.focus()

        day_label = tk.Label(prompt_frame, text="日期：")
        day_label.grid(row=1, column=0)
        day = tk.StringVar()
        day.set(today.day)
        day_entry = tk.Entry(prompt_frame, textvariable=day)
        day_entry.grid(row=1, column=1)

        def riddle():
            # 显示进度条
            riddle_progress = tk.ttk.Progressbar(prompt_frame, length=200, mode='indeterminate',
                                                 orient=tkinter.HORIZONTAL)
            riddle_progress.grid(row=3, columnspan=2)
            riddle_progress['maximum'] = 100
            riddle_progress['value'] = 0
            riddle_progress.start()
            # 异步解谜
            threading.Thread(target=__riddle).start()

        def __riddle():
            global result_canvas
            result_canvas = tk.Canvas(window, width=window.winfo_width(), height=window.winfo_height())
            result_canvas.bind("<Double-Button-1>", start)
            result = parallel_main(result_canvas, int(month.get()) - 1, int(day.get()) - 1)
            if result is not None:
                # 销毁首页
                puzzle_canvas.destroy()
                prompt_frame.destroy()
                # 显示谜底
                result_canvas.create_text(5, window.winfo_height() - 1, anchor=tk.SW,
                                          text="用时: %s 秒, 步数: %s" % (result[0], result[1]))
                result_canvas.pack()

        tk.Button(prompt_frame, text="开始解谜", command=riddle).grid(row=2, columnspan=2)


    # 添加菜单
    menu = tk.Menu(window)
    about = tk.Menu(menu)
    about.add_command(label="重新开始", command=start)
    about.add_separator()
    about.add_command(label="结束", command=window.quit)
    menu.add_cascade(label="关于", menu=about)
    window.config(menu=menu)

    start()

    window.geometry("%sx%s+0+0" % (DOT_SIZE * 7, DOT_SIZE * 7 + 20))
    window.resizable(False, False)
    window.mainloop()

    '''test: main'''
    # parallel_main(0, 0)
    # main(0, 0)
    '''test: place_brick'''
    # bricks = [
    #     BRICK_2.rotate().rotate(),
    #     BRICK_1.flip().rotate().rotate(),
    #     BRICK_3,
    #     BRICK_7.rotate().rotate(),
    #     BRICK_6.flip().rotate().rotate(),
    #     BRICK_5.flip(),
    #     BRICK_4.rotate(),
    #     BRICK_0,
    # ]
    # brick_seq = []
    # place_brick(Board(6, 7), brick_seq, bricks, 0)
