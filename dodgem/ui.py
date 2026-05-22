import pygame as pg
from constants import *
import os

# Глобальные переменные для изображений
IMG_WHITE = None
IMG_BLACK = None

def init_images():
    """Загружает и масштабирует изображения. Вызывать после создания окна."""
    global IMG_WHITE, IMG_BLACK
    try:
        image_white = pg.image.load(WHITE_CHECKER_IMG).convert_alpha()
        IMG_WHITE = pg.transform.smoothscale(image_white, (CELL_SIZE-20, CELL_SIZE-20))
        image_black = pg.image.load(BLACK_CHECKER_IMG).convert_alpha()
        IMG_BLACK = pg.transform.smoothscale(image_black, (CELL_SIZE-20, CELL_SIZE-20))
    except Exception as e:
        print("Ошибка загрузки изображений:", e)

class TextInput:
    """Поле ввода текста."""
    def __init__(self, x, y, width, height, placeholder='', is_password=False):
        self.rect = pg.Rect(x, y, width, height)
        self.text = ''
        self.active = False
        self.placeholder = placeholder
        self.is_password = is_password
        self.color_inactive = pg.Color('lightskyblue3')
        self.color_active = pg.Color('dodgerblue2')
        self.color = self.color_inactive
        self.txt_surface = INPUT_FONT.render(placeholder, True, (150, 150, 150))

    def handle_event(self, event):
        if event.type == pg.MOUSEBUTTONDOWN:
            self.active = self.rect.collidepoint(event.pos)
            self.color = self.color_active if self.active else self.color_inactive
            if self.active and self.text == '':
                self.txt_surface = INPUT_FONT.render('', True, BLACK)

        if event.type == pg.KEYDOWN and self.active:
            if event.key == pg.K_RETURN:
                return True
            elif event.key == pg.K_BACKSPACE:
                self.text = self.text[:-1]
            else:
                self.text += event.unicode

            display_text = '*' * len(self.text) if self.is_password else self.text
            self.txt_surface = INPUT_FONT.render(display_text, True, BLACK)
        return False

    def draw(self, screen):
        pg.draw.rect(screen, self.color, self.rect, 0)
        pg.draw.rect(screen, BLACK, self.rect, 2)
        screen.blit(self.txt_surface, (self.rect.x + 5, self.rect.y + 10))
        if self.text == '' and not self.active:
            placeholder_surf = INPUT_FONT.render(self.placeholder, True, (150, 150, 150))
            screen.blit(placeholder_surf, (self.rect.x + 5, self.rect.y + 10))

    def get_text(self):
        return self.text

def draw_login_screen(screen, username_input, password_input, error_msg):
    """Отрисовка экрана входа."""
    screen.fill(LIGHT_BLUE)
    title = TITLE_FONT.render("Вход в систему", True, BLUE)
    title_rect = title.get_rect(center=(SCREEN_WIDTH//2, 150))
    screen.blit(title, title_rect)

    username_input.draw(screen)
    password_input.draw(screen)

    # Кнопка "Войти"
    login_btn = pg.Rect(380, 500, 200, 60)
    pg.draw.rect(screen, GREEN, login_btn, border_radius=15)
    login_text = MENU_FONT.render("Войти", True, WHITE)
    login_text_rect = login_text.get_rect(center=login_btn.center)
    screen.blit(login_text, login_text_rect)

    # Кнопка "Регистрация"
    register_btn = pg.Rect(330, 600, 300, 60)
    pg.draw.rect(screen, BLUE, register_btn, border_radius=15)
    reg_text = MENU_FONT.render("Регистрация", True, WHITE)
    reg_text_rect = reg_text.get_rect(center=register_btn.center)
    screen.blit(reg_text, reg_text_rect)

    if error_msg:
        err = MESSAGE_FONT.render(error_msg, True, RED)
        err_rect = err.get_rect(center=(SCREEN_WIDTH//2, 580))
        screen.blit(err, err_rect)

    return login_btn, register_btn

def draw_register_screen(screen, username_input, password_input, confirm_input, error_msg):
    """Отрисовка экрана регистрации."""
    screen.fill(LIGHT_BLUE)
    title = TITLE_FONT.render("Регистрация", True, BLUE)
    title_rect = title.get_rect(center=(SCREEN_WIDTH//2, 150))
    screen.blit(title, title_rect)

    username_input.draw(screen)
    password_input.draw(screen)
    confirm_input.draw(screen)

    register_btn = pg.Rect(280, 550, 400, 60)
    pg.draw.rect(screen, GREEN, register_btn, border_radius=15)
    reg_text = MENU_FONT.render("Зарегистрироваться", True, WHITE)
    reg_text_rect = reg_text.get_rect(center=register_btn.center)
    screen.blit(reg_text, reg_text_rect)

    back_btn = pg.Rect(380, 650, 200, 60)
    pg.draw.rect(screen, GRAY, back_btn, border_radius=15)
    back_text = MENU_FONT.render("Назад", True, WHITE)
    back_text_rect = back_text.get_rect(center=back_btn.center)
    screen.blit(back_text, back_text_rect)

    if error_msg:
        err = MESSAGE_FONT.render(error_msg, True, RED)
        err_rect = err.get_rect(center=(SCREEN_WIDTH//2, 520))
        screen.blit(err, err_rect)

    return register_btn, back_btn

def draw_menu(screen, current_user):
    """Отрисовка главного меню."""
    screen.fill(BLACK)

    if current_user:
        user_text = MESSAGE_FONT.render(f"Пользователь: {current_user}", True, GREEN)
        screen.blit(user_text, (20, 20))
        logout_btn = pg.Rect(700, 20, 240, 40)
        pg.draw.rect(screen, RED, logout_btn, border_radius=10)
        logout_text = RULES_FONT.render("Выйти из аккаунта", True, WHITE)
        logout_rect = logout_text.get_rect(center=logout_btn.center)
        screen.blit(logout_text, logout_rect)
    else:
        logout_btn = None

    title = TITLE_FONT.render("Доджем", True, WHITE)
    title_rect = title.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//4))
    screen.blit(title, title_rect)

    start_text = MENU_FONT.render("Начать игру", True, WHITE)
    start_rect = start_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 100))
    screen.blit(start_text, start_rect)

    rules_text = MENU_FONT.render("Правила игры", True, WHITE)
    rules_rect = rules_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2))
    screen.blit(rules_text, rules_rect)

    # Кнопка загрузки (доступна, если есть сохранение)
    has_save = os.path.exists(SAVE_FILE)
    load_color = WHITE if has_save else GRAY
    load_game_text = MENU_FONT.render("Загрузить игру", True, load_color)
    load_game_rect = load_game_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 100))
    screen.blit(load_game_text, load_game_rect)

    exit_text = MENU_FONT.render("Выйти из игры", True, WHITE)
    exit_rect = exit_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 200))
    screen.blit(exit_text, exit_rect)

    return start_rect, rules_rect, load_game_rect, exit_rect, logout_btn

def draw_rules(screen):
    """Отрисовка правил игры."""
    screen.fill(BLACK)
    title = TITLE_FONT.render("Правила игры", True, WHITE)
    title_rect = title.get_rect(center=(SCREEN_WIDTH//2, 80))
    screen.blit(title, title_rect)

    rules = [
        "Доджем - стратегическая игра для двух игроков.",
        "",
        "Цель игры:",
        "- Белые должны довести 4 фишки до правого края",
        "- Чёрные должны довести 4 фишки до верхнего края",
        "",
        "Правила ходов:",
        "- Белые ходят: вверх, вправо или вниз",
        "- Чёрные ходят: влево, вправо или вверх",
        "- Фишки не могут ходить назад",
        "- Фишки блокируются при достижении своего края",
        "",
        "Победа:",
        "- Первый, кто доведёт 4 фишки до края - побеждает",
        "- Игрок, полностью заперевший шашки противника, проигрывает."
    ]

    y = 150
    for line in rules:
        if line:
            text = RULES_FONT.render(line, True, WHITE)
            screen.blit(text, (100, y))
        y += 40

    back_text = MENU_FONT.render("Назад", True, WHITE)
    back_rect = back_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT - 100))
    screen.blit(back_text, back_rect)
    return back_rect

def draw_board(screen):
    """Рисует клетки доски."""
    for x in range(6):
        for y in range(6):
            rect = (x * CELL_SIZE, y * CELL_SIZE, CELL_SIZE, CELL_SIZE)
            if (x == y == 5) or (x == y == 0) or (x == 5 and y == 0):
                pg.draw.rect(screen, BLACK, rect)
            elif (y == 0 and 1 <= x <= 4) or (x == 5 and 1 <= y <= 4):
                if (x + y) % 2 == 0:
                    pg.draw.rect(screen, (89, 87, 87), rect)
                else:
                    pg.draw.rect(screen, (61, 56, 56), rect)
            elif (x + y) % 2 == 0:
                pg.draw.rect(screen, (241, 217, 181), rect)
            else:
                pg.draw.rect(screen, (181, 135, 99), rect)

def draw_pieces(screen, board, moving_piece=None):
    """Рисует фишки на доске и анимируемую фишку."""
    for r in range(6):
        for c in range(6):
            piece = board.grid[r][c]
            if piece == 'ww' and IMG_WHITE:
                rect = IMG_WHITE.get_rect(center=(c*CELL_SIZE + CELL_SIZE//2, r*CELL_SIZE + CELL_SIZE//2))
                screen.blit(IMG_WHITE, rect)
            elif piece == 'bb' and IMG_BLACK:
                rect = IMG_BLACK.get_rect(center=(c*CELL_SIZE + CELL_SIZE//2, r*CELL_SIZE + CELL_SIZE//2))
                screen.blit(IMG_BLACK, rect)

    if moving_piece:
        sr, sc, er, ec, progress, piece_type = moving_piece
        x = sc * CELL_SIZE + CELL_SIZE//2 + (ec - sc) * CELL_SIZE * progress
        y = sr * CELL_SIZE + CELL_SIZE//2 + (er - sr) * CELL_SIZE * progress
        if piece_type == 'ww' and IMG_WHITE:
            rect = IMG_WHITE.get_rect(center=(x, y))
            screen.blit(IMG_WHITE, rect)
        elif piece_type == 'bb' and IMG_BLACK:
            rect = IMG_BLACK.get_rect(center=(x, y))
            screen.blit(IMG_BLACK, rect)

def draw_valid_moves(screen, moves):
    """Рисует зелёные кружки на допустимых ходах."""
    for r, c in moves:
        pg.draw.circle(screen, GREEN, (c*CELL_SIZE + CELL_SIZE//2, r*CELL_SIZE + CELL_SIZE//2), 15)

def draw_save_message(screen, timer):
    """Рисует сообщение о сохранении."""
    if timer > 0:
        msg = MESSAGE_FONT.render("Игра сохранена!", True, GREEN)
        msg_rect = msg.get_rect(center=(SCREEN_WIDTH//2, 50))
        screen.blit(msg, msg_rect)

def draw_thinking_message(screen):
    """Рисует сообщение о ходе бота."""
    msg = MESSAGE_FONT.render("Бот думает...", True, BLUE)
    msg_rect = msg.get_rect(center=(SCREEN_WIDTH//2, 50))
    screen.blit(msg, msg_rect)