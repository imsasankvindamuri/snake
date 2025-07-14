# Released under The Unlicense. You may use this for any purpose-- open-source or proprietary--
# with or without credit. This software is only compatible with Unix-like operating systems.

from enum import Enum
import os
import random
import sys
import termios
import tty
import select
import time
from collections.abc import Generator
from typing import override, Any
from types import NotImplementedType, TracebackType

# ANSI escape codes for colors
RESET = "\033[0m"
GREEN = "\033[32m"
RED = "\033[31m"
BLUE = "\033[34m"
        
class KeyListener:
    def __init__(self) -> None:
        self.fd: int
        self.old_settings: list[Any]
    
    def __enter__(self) -> 'KeyListener':
        self.fd = sys.stdin.fileno()
        self.old_settings = termios.tcgetattr(self.fd)
        _ = tty.setcbreak(self.fd)
        return self

    def __exit__(self, exc_type: type[BaseException] | None, 
                 exc_val: BaseException | None, 
                 exc_tb: TracebackType | None) -> None:
        termios.tcsetattr(self.fd, termios.TCSADRAIN, self.old_settings)

    def get_key(self) -> str | None:
        if select.select([sys.stdin], [], [], 0)[0]:
            return sys.stdin.read(1)
        return None

class Point2D:
    def __init__(self, x_coord: int, y_coord: int) -> None:
        self.x: int = x_coord
        self.y: int = y_coord

    def __add__(self, other: object) -> 'Point2D | NotImplementedType':
        if isinstance(other, Point2D):
            return Point2D(self.x + other.x, self.y + other.y)
        return NotImplemented

    @override
    def __repr__(self) -> str:
        return f"({self.x}, {self.y})"

    def __iter__(self) -> Generator[int, None, None]:
        yield self.x
        yield self.y

    @override
    def __eq__(self, other: object) -> bool:
        if isinstance(other, Point2D):
            return self.x == other.x and self.y == other.y
        return False

    @override
    def __hash__(self) -> int:
        return hash((self.x, self.y))

    def __neg__(self) -> 'Point2D':
        return Point2D(-self.x, -self.y)

    def squash(self, x_bounds: int, y_bounds: int) -> 'Point2D':
        return Point2D((self.x % x_bounds), (self.y % y_bounds))

class Direction(Enum):
    UP = Point2D(0, -1)
    DOWN = Point2D(0, 1)
    RIGHT = Point2D(1, 0)
    LEFT = Point2D(-1, 0)

class Snake:
    def __init__(self, x_coord: int, y_coord: int, direction: Direction) -> None:
        self.coords: list[Point2D] = [Point2D(x_coord, y_coord)]
        self.direction: Direction = direction
        self.char_to_direction: dict[str, Direction] = {
            'w' : Direction.UP,
            'a' : Direction.LEFT,
            's' : Direction.DOWN,
            'd' : Direction.RIGHT
        }


    def show(self) -> list[Point2D]:
        return self.coords

    def move(self, key: str) -> bool:
        character = key.strip().lower()
        if character in self.char_to_direction:
            if self.direction.value != -self.char_to_direction[character].value:
                self.direction = self.char_to_direction[character]
        if character == 'q':
            return False
        return True

    def grow(self) -> None:
        self.coords = [self.coords[0] + self.direction.value] + self.coords

    def update(self, x_bounds : int, y_bounds : int) -> None:
        self.coords = [coord.squash(x_bounds, y_bounds) for coord in self.coords]
        self.grow()
        _ = self.coords.pop()

    def is_dead(self) -> bool:
        return self.coords[0] in self.coords[1:]

def new_apple_location(x_bounds: int, y_bounds: int, snake: Snake) -> Point2D:
    occupied = set(snake.coords)
    free = [Point2D(x, y) for x in range(x_bounds) for y in range(y_bounds) if Point2D(x, y) not in occupied]
    if not free:
        # Win condition: snake has filled the board
        print("You won! No more space left.")
        sys.exit(0)
    return random.choice(free)

def plot(x_bounds: int, y_bounds: int, snake: Snake, apple: Point2D) -> list[str]:
    _ = os.system("clear")
    board = [[" " for _ in range(x_bounds)] for _ in range(y_bounds)]
    board[apple.y][apple.x] = f"{RED}A{RESET}"
    for point in snake.coords:
        if 0 <= point.x < x_bounds and 0 <= point.y < y_bounds:
            board[point.y][point.x] = f"{GREEN}S{RESET}"

    horizontal_border = f"{BLUE}+{'-' * x_bounds*2}+{RESET}"
    rendered_board = [horizontal_border]
    for row in board:
        rendered_board.append(f"{BLUE}|{RESET}" + " ".join(row) + f" {BLUE}|{RESET}")
    rendered_board.append(horizontal_border)
    return rendered_board

def main() -> None:
    X_BOUNDS = 30
    Y_BOUNDS = 20
    snake = Snake(X_BOUNDS // 2, Y_BOUNDS // 2, Direction.DOWN)
    apple = new_apple_location(X_BOUNDS, Y_BOUNDS, snake)
    is_running = True
    delay = 0.5
    score = 0
    with KeyListener() as listener:
        while is_running:
            print("\n".join(plot(X_BOUNDS, Y_BOUNDS, snake, apple)))
            if snake.is_dead():
                break
            if snake.coords[0] == apple:
                score += 1
                print("\a", end="", flush=True)
                snake.grow()
                apple = new_apple_location(X_BOUNDS, Y_BOUNDS, snake)
            key = listener.get_key()
            if key:
                is_running = snake.move(key)
            snake.update(X_BOUNDS, Y_BOUNDS)
            time.sleep(delay)

    print(f"{RED}GAME OVER{RESET} — SCORE: {score}")

if __name__ == "__main__":
    main()
