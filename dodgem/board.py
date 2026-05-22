class Board:
    """Игровая доска 6x6"""
    def __init__(self, board_data=None):
        if board_data:
            # глубокое копирование
            self.grid = [row[:] for row in board_data]
        else:
            self.reset()

    def reset(self):
        """Начальная расстановка"""
        self.grid = [
            ["xx", "fb", "fb", "fb", "fb", "xx"],
            ["ww", "--", "--", "--", "--", "fw"],
            ["ww", "--", "--", "--", "--", "fw"],
            ["ww", "--", "--", "--", "--", "fw"],
            ["ww", "--", "--", "--", "--", "fw"],
            ["--", "bb", "bb", "bb", "bb", "xx"]
        ]

    def get_piece(self, row, col):
        return self.grid[row][col]

    def is_occupied(self, row, col, color):
        """Проверяет, занята ли клетка для фишки данного цвета.
        Для белых клетки 'fw' считаются свободными, для чёрных - 'fb'."""
        cell = self.grid[row][col]
        if cell == '--':
            return False
        if color == 'white' and cell == 'fw':
            return False
        if color == 'black' and cell == 'fb':
            return False
        return True

    def get_valid_moves(self, row, col, color):
        """Возвращает список координат (r, c) допустимых ходов для фишки."""
        # Проверка, что в клетке действительно фишка нужного цвета
        if color == 'white' and self.grid[row][col] != 'ww':
            return []
        if color == 'black' and self.grid[row][col] != 'bb':
            return []

        # Если фишка достигла своего края, ходов нет
        if color == 'white' and col == 5:
            return []
        if color == 'black' and row == 0:
            return []

        moves = []
        if color == 'white':
            directions = [(-1, 0), (0, 1), (1, 0)]  # вверх, вправо, вниз
        else:  # black
            directions = [(0, -1), (0, 1), (-1, 0)]  # влево, вправо, вверх

        for dr, dc in directions:
            nr, nc = row + dr, col + dc
            if 0 <= nr < 6 and 0 <= nc < 6:
                if not self.is_occupied(nr, nc, color):
                    moves.append((nr, nc))
        return moves

    def move_piece(self, start, end):
        """Перемещает фишку с start на end (без проверок)."""
        sr, sc = start
        er, ec = end
        piece = self.grid[sr][sc]
        self.grid[sr][sc] = '--'
        self.grid[er][ec] = piece

    def check_win(self):
        """Проверяет, есть ли победитель. Возвращает 'white' или 'black' или None."""
        # Чёрные побеждают, если 4 фишки в верхнем ряду (row=0)
        black_count = sum(1 for c in range(6) if self.grid[0][c] == 'bb')
        if black_count >= 4:
            return 'black'
        # Белые побеждают, если 4 фишки в правом столбце (col=5)
        white_count = sum(1 for r in range(6) if self.grid[r][5] == 'ww')
        if white_count >= 4:
            return 'white'
        return None

    def has_any_move(self, color):
        """Проверяет, есть ли у данного цвета хотя бы один допустимый ход."""
        for r in range(6):
            for c in range(6):
                if (color == 'white' and self.grid[r][c] == 'ww') or \
                   (color == 'black' and self.grid[r][c] == 'bb'):
                    if self.get_valid_moves(r, c, color):
                        return True
        return False

    def copy(self):
        """Создаёт глубокую копию доски."""
        return Board([row[:] for row in self.grid])
