import pygame as pg

# Размеры
CELL_SIZE = 160
BOARD_SIZE = 6
SCREEN_WIDTH = CELL_SIZE * BOARD_SIZE
SCREEN_HEIGHT = CELL_SIZE * BOARD_SIZE

# Цвета
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GRAY = (100, 100, 100)
GREEN = (0, 255, 0)
RED = (255, 0, 0)
BLUE = (0, 120, 255)
LIGHT_BLUE = (173, 216, 230)

# Состояния игры
MENU = 0
GAME = 1
RULES = 2
LOGIN = 3
REGISTER = 4

# Файлы
SAVE_FILE = 'dodgem_save.dat'
USERS_FILE = 'dodgem_users.json'

# Изображения
WHITE_CHECKER_IMG = "white-regular.png"
BLACK_CHECKER_IMG = "black-regular.png"
ICON_IMG = "icon32.png"
SOUND_FILE = "sound.mp3"

# Настройки бота
BOT_THINKING_TIME = 0.1  # секунд
BOT_DEPTH = 4         # глубина минимакса

# Шрифты (будут инициализированы в ui.py)
pg.font.init()
TITLE_FONT = pg.font.SysFont('Tahoma', 72)
MENU_FONT = pg.font.SysFont('Times New Roman', 42)
MESSAGE_FONT = pg.font.SysFont('Tahoma', 36)
RULES_FONT = pg.font.SysFont('Tahoma', 23)
INPUT_FONT = pg.font.SysFont('Arial', 32)