import sys
import pygame as pg
import pickle
import os
import time
import pyautogui
import random
import numpy as np
from constants import *
from board import Board
from dodgem_rl import DQNAgent, encode_board, get_legal_moves, compute_reward, MinimaxWhite
from ui import *
from utils import load_users, save_users

class Game:
    def __init__(self):
        self.screen = pg.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pg.display.set_caption("Доджем")
        init_images()
        try:
            icon = pg.image.load(ICON_IMG)
            pg.display.set_icon(icon)
        except:
            pass

        self.clock = pg.time.Clock()
        self.running = True
        self.state = LOGIN

        self.board = Board()
        self.agent = DQNAgent()

        self.current_color = 'white'
        self.game_over = False
        self.winner = None
        self.selected_piece = None
        self.valid_moves = []
        self.moving_piece = None
        self.last_mover = None
        self.save_message_timer = 0
        self.bot_thinking = False

        self.last_state = None
        self.last_action_idx = None
        self.last_action = None

        self.users = load_users()
        self.current_user = None

        self.login_username = TextInput(330, 300, 300, 50, 'Имя пользователя')
        self.login_password = TextInput(330, 400, 300, 50, 'Пароль', is_password=True)
        self.register_username = TextInput(330, 250, 300, 50, 'Имя пользователя')
        self.register_password = TextInput(330, 350, 300, 50, 'Пароль', is_password=True)
        self.register_confirm = TextInput(330, 450, 300, 50, 'Подтвердите пароль', is_password=True)

        self.login_error = ''
        self.register_error = ''

    def run(self):
        while self.running:
            if self.state == LOGIN:
                self.handle_login()
            elif self.state == REGISTER:
                self.handle_register()
            elif self.state == MENU:
                self.handle_menu()
            elif self.state == RULES:
                self.handle_rules()
            elif self.state == GAME:
                self.handle_game()
            pg.display.flip()
            self.clock.tick(60)
        self.agent.save_model()
        pg.quit()
        sys.exit()

    def handle_login(self):
        login_btn, register_btn = draw_login_screen(
            self.screen, self.login_username, self.login_password, self.login_error
        )
        for event in pg.event.get():
            if event.type == pg.QUIT:
                self.running = False
            self.login_username.handle_event(event)
            if self.login_password.handle_event(event):
                self.try_login()
            if event.type == pg.MOUSEBUTTONDOWN and event.button == 1:
                if login_btn.collidepoint(event.pos):
                    self.try_login()
                elif register_btn.collidepoint(event.pos):
                    self.state = REGISTER
                    self.register_error = ''
                    self.register_username.text = ''
                    self.register_password.text = ''
                    self.register_confirm.text = ''

    def try_login(self):
        username = self.login_username.get_text()
        password = self.login_password.get_text()
        if username in self.users and self.users[username]['password'] == password:
            self.current_user = username
            self.state = MENU
            self.login_error = ''
        else:
            self.login_error = 'Неверное имя или пароль'

    def handle_register(self):
        reg_btn, back_btn = draw_register_screen(
            self.screen, self.register_username, self.register_password,
            self.register_confirm, self.register_error
        )
        for event in pg.event.get():
            if event.type == pg.QUIT:
                self.running = False
            self.register_username.handle_event(event)
            self.register_password.handle_event(event)
            if self.register_confirm.handle_event(event):
                self.try_register()
            if event.type == pg.MOUSEBUTTONDOWN and event.button == 1:
                if reg_btn.collidepoint(event.pos):
                    self.try_register()
                elif back_btn.collidepoint(event.pos):
                    self.state = LOGIN
                    self.login_error = ''
                    self.login_username.text = ''
                    self.login_password.text = ''

    def try_register(self):
        username = self.register_username.get_text()
        password = self.register_password.get_text()
        confirm = self.register_confirm.get_text()
        if not username:
            self.register_error = 'Введите имя пользователя'
        elif username in self.users:
            self.register_error = 'Имя уже занято'
        elif not password:
            self.register_error = 'Введите пароль'
        elif password != confirm:
            self.register_error = 'Пароли не совпадают'
        else:
            self.users[username] = {'password': password}
            save_users(self.users)
            self.current_user = username
            self.state = MENU
            self.register_error = ''

    def handle_menu(self):
        start_rect, rules_rect, load_game_rect, exit_rect, logout_btn = draw_menu(self.screen, self.current_user)
        for event in pg.event.get():
            if event.type == pg.QUIT:
                self.running = False
            elif event.type == pg.MOUSEBUTTONDOWN and event.button == 1:
                pos = event.pos
                if logout_btn and logout_btn.collidepoint(pos):
                    self.current_user = None
                    self.state = LOGIN
                    self.login_username.text = ''
                    self.login_password.text = ''
                elif start_rect.collidepoint(pos):
                    self.state = GAME
                    self.reset_game()
                elif rules_rect.collidepoint(pos):
                    self.state = RULES
                elif load_game_rect.collidepoint(pos) and os.path.exists(SAVE_FILE):
                    if self.load_game():
                        self.state = GAME
                elif exit_rect.collidepoint(pos):
                    self.running = False

    def handle_rules(self):
        back_rect = draw_rules(self.screen)
        for event in pg.event.get():
            if event.type == pg.QUIT:
                self.running = False
            elif event.type == pg.MOUSEBUTTONDOWN and event.button == 1:
                if back_rect.collidepoint(event.pos):
                    self.state = MENU
                    
    def handle_game(self):
        if not self.game_over and not self.moving_piece:
            if self.current_color == 'white':
                self.handle_player_turn()
            else:
                self.handle_bot_turn()
        self.update_animation()
        self.draw_game()
        if self.save_message_timer > 0:
            self.save_message_timer -= 1
        if self.game_over:
            self.show_game_over()

    def handle_player_turn(self):
        for event in pg.event.get():
            if event.type == pg.QUIT:
                self.running = False
            elif event.type == pg.KEYDOWN:
                if event.key == pg.K_t:
                    self.self_play_random(2000)
                if event.key == pg.K_y:
                    self.self_play_against_minimax(17000) # самоигра против минимакса, кол-во партий можно изменять
                if event.key == pg.K_ESCAPE:
                    self.state = MENU
                    self.reset_game()
                elif event.key == pg.K_s and (pg.key.get_mods() & pg.KMOD_CTRL):
                    self.save_game()
            elif event.type == pg.MOUSEBUTTONDOWN and event.button == 1:
                x, y = event.pos
                col = x // CELL_SIZE
                row = y // CELL_SIZE
                if 0 <= row < 6 and 0 <= col < 6:
                    piece = self.board.get_piece(row, col)
                    if piece == 'ww' and self.current_color == 'white':
                        self.selected_piece = (row, col)
                        self.valid_moves = self.board.get_valid_moves(row, col, 'white')
                    elif self.selected_piece and (row, col) in self.valid_moves:
                        self.start_move(self.selected_piece, (row, col))
                        self.selected_piece = None
                        self.valid_moves = []
                    else:
                        self.selected_piece = None
                        self.valid_moves = []

    def handle_bot_turn(self):
        if not self.bot_thinking:
            self.bot_thinking = True
            possible = get_legal_moves(self.board, 'black')
            if not possible:
                self.game_over = True
                self.winner = '_black'
                self.bot_thinking = False
                return
            state = encode_board(self.board, 'black')
            action_idx, action = self.agent.act(state, possible)
            if action:
                self.last_state = state
                self.last_action_idx = action_idx
                self.last_action = action
                self.start_move(action[0], action[1])
            else:
                self.bot_thinking = False

    def start_move(self, start, end):
        sr, sc = start
        er, ec = end
        piece = self.board.get_piece(sr, sc)
        self.last_mover = self.current_color
        self.board.grid[sr][sc] = '--'
        self.moving_piece = (sr, sc, er, ec, 0.0, piece)
        try:
            pg.mixer.music.load(SOUND_FILE)
            pg.mixer.music.play()
        except:
            pass

    def update_animation(self):
        if self.moving_piece:
            sr, sc, er, ec, progress, piece = self.moving_piece
            progress += 0.1
            if progress >= 1.0:
                self.board.grid[er][ec] = piece
                self.moving_piece = None
                self._finish_move()
            else:
                self.moving_piece = (sr, sc, er, ec, progress, piece)

    def _finish_move(self):
        self.winner = self.board.check_win()
        if self.winner:
            self.game_over = True
            if self.last_mover == 'black' and self.last_state is not None:
                reward = compute_reward(self.last_action[0], self.last_action[1], self.board, self.winner)
                next_state = encode_board(self.board, self.current_color)
                self.agent.remember_and_train(self.last_state, self.last_action_idx, reward, next_state, True)
                self.agent.save_model()
            self.last_state = None
            return

        self.current_color = 'black' if self.current_color == 'white' else 'white'

        if self.last_mover == 'black' and self.last_state is not None:
            reward = compute_reward(self.last_action[0], self.last_action[1], self.board)
            next_state = encode_board(self.board, self.current_color)
            self.agent.remember_and_train(self.last_state, self.last_action_idx, reward, next_state, False)
            self.last_state = None

        if not self.board.has_any_move(self.current_color):
            self.game_over = True
            self.winner = '_white' if self.current_color == 'white' else '_black'
            if self.last_mover == 'black' and self.winner == '_white':
                reward = compute_reward(self.last_action[0], self.last_action[1], self.board, '_white')
                next_state = encode_board(self.board, self.current_color)
                self.agent.remember_and_train(self.last_state, self.last_action_idx, reward, next_state, True)
                self.agent.save_model()
            return

        if self.last_mover == 'black':
            self.bot_thinking = False
    #самоигра против рандомных ходов
    def self_play_random(self, num_games=17000, report_every=50):
        old_state = self.state
        self.state = None
        print(f"\n=== САМОИГРА: бот (чёрные) против СЛУЧАЙНЫХ белых ===")
        print(f"Всего партий: {num_games}, отчёт каждые {report_every} игр.\n")
        old_eps = self.agent.epsilon
        self.agent.epsilon = 0.3
        wins = 0
        for game_idx in range(1, num_games + 1):
            board = Board()
            color = 'white'
            step = 0
            winner = None
            last_state_black = None
            last_action_idx_black = None
            last_action_black = None
            while step < 300:
                possible = get_legal_moves(board, color)
                if not possible:
                    winner = 'black' if color == 'white' else 'white'
                    break
                if color == 'black':
                    state = encode_board(board, 'black')
                    act_idx, action = self.agent.act(state, possible)
                    if not action:
                        winner = 'white'
                        break
                    last_state_black = state
                    last_action_idx_black = act_idx
                    last_action_black = action
                    start, end = action
                else:
                    action = random.choice(possible)
                    start, end = action
                piece = board.grid[start[0]][start[1]]
                board.grid[start[0]][start[1]] = '--'
                board.grid[end[0]][end[1]] = piece
                winner = board.check_win()
                if winner:
                    break
                if color == 'black' and last_state_black is not None:
                    reward = compute_reward(last_action_black[0], last_action_black[1], board)
                    next_state = encode_board(board, 'white')
                    self.agent.remember_and_train(last_state_black, last_action_idx_black, reward, next_state, False)
                    last_state_black = None
                color = 'black' if color == 'white' else 'white'
                step += 1
            if not winner:
                winner = 'black' if color == 'white' else 'white'
            if winner == 'black':
                wins += 1
            if last_state_black is not None:
                final_reward = compute_reward(last_action_black[0], last_action_black[1], board, winner)
                next_state = encode_board(board, 'white')
                self.agent.remember_and_train(last_state_black, last_action_idx_black, final_reward, next_state, True)
            if game_idx % report_every == 0:
                win_rate = wins / report_every * 100
                print(f"[{game_idx:4d}] Побед чёрных: {wins:3d} / {report_every} = {win_rate:5.1f}% | ε={self.agent.epsilon:.3f}")
                wins = 0
                self.agent.save_model()
        self.agent.epsilon = old_eps
        self.agent.save_model()
        self.state = old_state
        print("\n=== САМОИГРА ЗАВЕРШЕНА ===\n")
    #самоигра против минимакса
    def self_play_against_minimax(self, num_games=17000, report_every=50):
        old_state = self.state
        self.state = None
        print(f"\n=== САМОИГРА: бот (чёрные) против МИНИМАКСА (depth=4, белые) ===")
        print(f"Всего партий: {num_games}, отчёт каждые {report_every} игр.\n")

        old_eps = self.agent.epsilon
        old_decay = self.agent.epsilon_decay
        old_eps_min = self.agent.epsilon_min  # сохраняем старый epsilon_min

        self.agent.epsilon = 0.9
        self.agent.epsilon_min = 0.02  # не даёт упасть ниже 0.02
        self.agent.epsilon_decay = 0.9999  # медленное исследование

        minimax_bot = MinimaxWhite(depth=4)
        wins = 0

        for game_idx in range(1, num_games + 1):
            board = Board()
            color = 'white'
            step = 0
            winner = None

            # буфер для отложенного обучения
            pending_state = None
            pending_action_idx = None
            pending_reward = 0.0

            while step < 300:
                possible = get_legal_moves(board, color)
                if not possible:
                    winner = 'black' if color == 'white' else 'white'
                    break

                if color == 'black':  # ход бота
                    state = encode_board(board, 'black')
                    act_idx, action = self.agent.act(state, possible)
                    if not action:
                        winner = 'white'
                        break
                    start, end = action

                    piece = board.grid[start[0]][start[1]]
                    board.grid[start[0]][start[1]] = '--'
                    board.grid[end[0]][end[1]] = piece

                    reward = compute_reward(start, end, board)
                    winner = board.check_win()

                    if winner:  # победа или поражение сразу после хода чёрных
                        final_reward = compute_reward(start, end, board, winner)
                        self.agent.remember_and_train(
                            state, act_idx, final_reward,
                            encode_board(board, 'black'), True
                        )
                        if winner == 'black':
                            wins += 1
                        pending_state = None
                        break

                    # иначе запоминаем переход и ждём ответа белых
                    pending_state = state
                    pending_action_idx = act_idx
                    pending_reward = reward
                    color = 'white'
                    step += 1
                    continue

                else:  # ход белых (минимакс)
                    move = minimax_bot.get_best_move(board)
                    if move is None:
                        winner = 'black'
                        if pending_state is not None:
                            self.agent.remember_and_train(
                                pending_state, pending_action_idx,
                                10.0, encode_board(board, 'black'), True
                            )
                            wins += 1
                        pending_state = None
                        break

                    start, end = move
                    piece = board.grid[start[0]][start[1]]
                    board.grid[start[0]][start[1]] = '--'
                    board.grid[end[0]][end[1]] = piece

                    winner = board.check_win()

                    if winner:  # белые выиграли
                        if pending_state is not None:
                            final_reward = compute_reward(start, end, board, winner)  # -10
                            self.agent.remember_and_train(
                                pending_state, pending_action_idx,
                                final_reward, encode_board(board, 'black'), True
                            )
                        pending_state = None
                        break

                    # игра продолжается: фиксируем переход (s,a,r,s')
                    if pending_state is not None:
                        next_state = encode_board(board, 'black')
                        self.agent.remember_and_train(
                            pending_state, pending_action_idx,
                            pending_reward, next_state, False
                        )
                        pending_state = None

                    color = 'black'
                    step += 1

            # если цикл завершился по шагам
            if winner is None:
                winner = 'black' if color == 'white' else 'white'

            # обрабатываем оставшийся pending (если есть)
            if pending_state is not None:
                final_reward = 10.0 if winner == 'black' else -10.0
                self.agent.remember_and_train(
                    pending_state, pending_action_idx,
                    final_reward, encode_board(board, 'black'), True
                )
                if winner == 'black':
                    wins += 1

            if game_idx % report_every == 0:
                win_rate = wins / report_every * 100
                print(
                    f"[{game_idx:4d}] Побед чёрных: {wins:3d} / {report_every} = {win_rate:5.1f}% | ε={self.agent.epsilon:.4f}")
                wins = 0
                self.agent.save_model()

        self.agent.epsilon = old_eps
        self.agent.epsilon_decay = old_decay
        self.agent.epsilon_min = old_eps_min  # восстанавливаем epsilon_min
        self.agent.save_model()
        self.state = old_state
        print("\n=== САМОИГРА ПРОТИВ МИНИМАКСА ЗАВЕРШЕНА ===\n")

    def draw_game(self):
        draw_board(self.screen)
        if self.selected_piece and not self.moving_piece and self.current_color == 'white':
            sr, sc = self.selected_piece
            pg.draw.rect(self.screen, RED, (sc*CELL_SIZE, sr*CELL_SIZE, CELL_SIZE, CELL_SIZE), 5)
            draw_valid_moves(self.screen, self.valid_moves)
        draw_pieces(self.screen, self.board, self.moving_piece)
        draw_save_message(self.screen, self.save_message_timer)

    def show_game_over(self):
        if self.winner == 'white':
            msg = 'Победили белые. Начать новую игру?'
        elif self.winner == 'black':
            msg = 'Победили чёрные. Начать новую игру?'
        elif self.winner == '_white':
            msg = 'Нет ходов! Победили белые. Начать новую игру?'
        elif self.winner == '_black':
            msg = 'Нет ходов! Победили чёрные. Начать новую игру?'
        else:
            msg = 'Игра окончена. Начать новую игру?'
        result = pyautogui.confirm(text=msg, title='Игра окончена', buttons=['OK', 'Cancel'])
        if result == 'Cancel':
            self.state = MENU
        self.reset_game()

    def reset_game(self):
        self.board.reset()
        self.current_color = 'white'
        self.game_over = False
        self.winner = None
        self.selected_piece = None
        self.valid_moves = []
        self.moving_piece = None
        self.bot_thinking = False
        self.last_mover = None
        self.last_state = None
        self.last_action_idx = None
        self.last_action = None
        self.agent.save_model()

    def save_game(self):
        state = {
            'board': self.board.grid,
            'current_color': self.current_color,
            'game_over': self.game_over,
            'winner': self.winner
        }
        try:
            with open(SAVE_FILE, 'wb') as f:
                pickle.dump(state, f)
            self.save_message_timer = 120
        except Exception as e:
            print("Ошибка сохранения:", e)

    def load_game(self):
        if not os.path.exists(SAVE_FILE):
            return False
        try:
            with open(SAVE_FILE, 'rb') as f:
                state = pickle.load(f)
            self.board.grid = state['board']
            self.current_color = state['current_color']
            self.game_over = state['game_over']
            self.winner = state['winner']
            self.selected_piece = None
            self.valid_moves = []
            self.moving_piece = None
            self.bot_thinking = False
            self.last_mover = None
            self.last_state = None
            self.last_action_idx = None
            self.last_action = None
            return True
        except Exception as e:
            print("Ошибка загрузки:", e)
            return False
