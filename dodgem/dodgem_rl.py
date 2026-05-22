import numpy as np
import random
import torch
import torch.nn as nn
import torch.optim as optim
import os
import pickle
import math

# --- Вспомогательные функции ---
def encode_board(board, current_color):
    state = np.zeros(37, dtype=np.float32)
    for r in range(6):
        for c in range(6):
            piece = board.grid[r][c]
            if piece == 'ww':
                state[r*6+c] = 1.0
            elif piece == 'bb':
                state[r*6+c] = 2.0
    state[36] = 0.0 if current_color == 'white' else 1.0
    return state

def get_legal_moves(board, color):
    actions = []
    for r in range(6):
        for c in range(6):
            piece = board.grid[r][c]
            if color == 'white' and piece == 'ww':
                moves = board.get_valid_moves(r, c, 'white')
            elif color == 'black' and piece == 'bb':
                moves = board.get_valid_moves(r, c, 'black')
            else:
                continue
            for move in moves:
                actions.append(((r, c), move))
    return actions

def compute_reward(start, end, board, winner=None):
    sr, sc = start
    er, ec = end
    reward = -0.01                     

    if sr > er:                         
        reward += 0.6 * (sr - er)
    elif sr < er:                       
        reward -= 1.0

    if sc != ec:                        
        reward -= 0.15

    if er == 1:
        reward += 3.0
    elif er == 0:
        reward += 6.0   

    if winner == 'black':
        reward += 10.0
    elif winner == 'white':
        reward -= 10.0

    return reward

#Приоритетный буфер (PER)
class PrioritizedReplayBuffer:
    def __init__(self, capacity=50000, alpha=0.6):
        self.capacity = capacity
        self.alpha = alpha
        self.buffer = []
        self.priorities = np.zeros(capacity, dtype=np.float32)
        self.pos = 0
        self.size = 0

    def push(self, state, action_idx, reward, next_state, done):
        max_prio = self.priorities.max() if self.size > 0 else 1.0
        if self.size < self.capacity:
            self.buffer.append((state, action_idx, reward, next_state, done))
        else:
            self.buffer[self.pos] = (state, action_idx, reward, next_state, done)
        self.priorities[self.pos] = max_prio
        self.pos = (self.pos + 1) % self.capacity
        self.size = min(self.size + 1, self.capacity)

    def sample(self, batch_size, beta=0.4):
        if self.size == 0:
            return None
        probs = self.priorities[:self.size] ** self.alpha
        probs /= probs.sum()
        indices = np.random.choice(self.size, batch_size, p=probs)
        samples = [self.buffer[i] for i in indices]
        total = self.size
        weights = (total * probs[indices]) ** (-beta)
        weights /= weights.max()
        return indices, samples, weights

    def update_priorities(self, indices, priorities):
        for idx, prio in zip(indices, priorities):
            self.priorities[idx] = prio

    def save(self, filename='dodgem_replay_buffer.pkl'):
        with open(filename, 'wb') as f:
            pickle.dump((self.buffer, self.priorities, self.pos, self.size), f)

    def load(self, filename='dodgem_replay_buffer.pkl'):
        if os.path.exists(filename):
            with open(filename, 'rb') as f:
                self.buffer, self.priorities, self.pos, self.size = pickle.load(f)
                self.buffer = list(self.buffer)
                print(f"[Buffer] Загружено {self.size} переходов")

#Нейросеть
class DQN(nn.Module):
    def __init__(self, input_dim=37, output_dim=20):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(input_dim, 128),
            nn.ReLU(),
            nn.Linear(128, 128),
            nn.ReLU(),
            nn.Linear(128, output_dim)
        )
    def forward(self, x):
        return self.net(x)

#DDQN с PER
class DQNAgent:
    def __init__(self, model_file='dodgem_model.pth', buffer_file='dodgem_replay_buffer.pkl',
                 lr=1e-3, gamma=0.99, epsilon=0.8, epsilon_min=0.1, epsilon_decay=0.998,
                 batch_size=64, target_update_freq=1000):          # <-- изменено на 1000
        self.model_file = model_file
        self.buffer_file = buffer_file
        self.gamma = gamma
        self.epsilon = epsilon
        self.epsilon_min = epsilon_min
        self.epsilon_decay = epsilon_decay
        self.batch_size = batch_size
        self.target_update_freq = target_update_freq
        self.steps = 0
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

        self.q_network = DQN().to(self.device)
        self.target_network = DQN().to(self.device)
        self.target_network.load_state_dict(self.q_network.state_dict())
        self.target_network.eval()
        self.optimizer = optim.Adam(self.q_network.parameters(), lr=lr)

        self.memory = PrioritizedReplayBuffer(capacity=100000)
        self.memory.load(self.buffer_file)
        self.load_model()

    def act(self, state, possible_actions):
        if not possible_actions:
            return None, None
        if np.random.rand() < self.epsilon:
            idx = random.randrange(len(possible_actions))
            return idx, possible_actions[idx]
        state_t = torch.FloatTensor(state).unsqueeze(0).to(self.device)
        with torch.no_grad():
            q_vals = self.q_network(state_t).cpu().numpy()[0][:len(possible_actions)]
        idx = int(np.argmax(q_vals))
        return idx, possible_actions[idx]

    def remember_and_train(self, state, action_idx, reward, next_state, done):
        self.memory.push(state, action_idx, reward, next_state, done)
        self.steps += 1
        if self.steps % self.target_update_freq == 0:
            self.target_network.load_state_dict(self.q_network.state_dict())
        self._train()

    def _train(self):
        if self.memory.size < self.batch_size:
            return
        indices, samples, weights = self.memory.sample(self.batch_size)
        states, actions, rewards, next_states, dones = zip(*samples)

        states = torch.FloatTensor(np.array(states)).to(self.device)
        actions = torch.LongTensor(actions).to(self.device)
        rewards = torch.FloatTensor(rewards).to(self.device)
        next_states = torch.FloatTensor(np.array(next_states)).to(self.device)
        dones = torch.FloatTensor(dones).to(self.device)
        weights = torch.FloatTensor(weights).to(self.device)

        #выбор действия основной сетью, оценка целевой
        with torch.no_grad():
            next_actions = self.q_network(next_states).argmax(1, keepdim=True)
            next_q = self.target_network(next_states).gather(1, next_actions).squeeze(1)
            target = rewards + (1 - dones) * self.gamma * next_q

        current_q = self.q_network(states).gather(1, actions.unsqueeze(1)).squeeze(1)
        loss = (weights * (current_q - target).pow(2)).mean()

        self.optimizer.zero_grad()
        loss.backward()
        self.optimizer.step()

        td_errors = (current_q - target).abs().detach().cpu().numpy()
        self.memory.update_priorities(indices, td_errors + 1e-6)

        self.epsilon = max(self.epsilon_min, self.epsilon * self.epsilon_decay)

    def save_model(self):
        torch.save(self.q_network.state_dict(), self.model_file)
        self.memory.save(self.buffer_file)
        print(f"[Agent] Модель и буфер опыта сохранены.")

    def load_model(self):
        if os.path.exists(self.model_file):
            self.q_network.load_state_dict(torch.load(self.model_file, map_location=self.device))
            self.target_network.load_state_dict(self.q_network.state_dict())
            print(f"[Agent] Модель загружена из {self.model_file}")

#Минимакс для белых для самоигры
class MinimaxWhite:
    def __init__(self, depth=4):
        self.depth = depth

    def get_best_move(self, board):
        moves = self._get_all_moves(board, 'white')
        if not moves:
            return None
        # Сортировка: лучшие ходы — с максимальным продвижением вправо
        moves.sort(key=lambda m: m[1][1] - m[0][1], reverse=True)
        best_value = -math.inf
        best_move = None
        alpha = -math.inf
        beta = math.inf
        for start, end in moves:
            new_board = board.copy()
            new_board.move_piece(start, end)
            value = self._minimax(new_board, self.depth - 1, alpha, beta, False)
            if value > best_value:
                best_value = value
                best_move = (start, end)
            alpha = max(alpha, value)
            if alpha >= beta:
                break
        return best_move

    def _get_all_moves(self, board, color):
        moves = []
        for r in range(6):
            for c in range(6):
                if color == 'white' and board.grid[r][c] == 'ww':
                    for move in board.get_valid_moves(r, c, 'white'):
                        moves.append(((r, c), move))
                elif color == 'black' and board.grid[r][c] == 'bb':
                    for move in board.get_valid_moves(r, c, 'black'):
                        moves.append(((r, c), move))
        return moves

    def _minimax(self, board, depth, alpha, beta, maximizing):
        winner = board.check_win()
        if winner == 'white':
            return 1000000 + depth
        if winner == 'black':
            return -1000000 - depth
        if depth == 0:
            return self._evaluate(board)

        if maximizing:
            max_eval = -math.inf
            moves = self._get_all_moves(board, 'white')
            moves.sort(key=lambda m: m[1][1] - m[0][1], reverse=True)
            for start, end in moves:
                new_board = board.copy()
                new_board.move_piece(start, end)
                eval = self._minimax(new_board, depth - 1, alpha, beta, False)
                max_eval = max(max_eval, eval)
                alpha = max(alpha, eval)
                if beta <= alpha:
                    break
            return max_eval
        else:
            min_eval = math.inf
            moves = self._get_all_moves(board, 'black')
            moves.sort(key=lambda m: m[0][0] - m[1][0], reverse=True)
            for start, end in moves:
                new_board = board.copy()
                new_board.move_piece(start, end)
                eval = self._minimax(new_board, depth - 1, alpha, beta, True)
                min_eval = min(min_eval, eval)
                beta = min(beta, eval)
                if beta <= alpha:
                    break
            return min_eval

    def _evaluate(self, board):
        """Усиленная оценочная функция: позиция, угрозы, подвижность."""
        score = 0

        # Для каждой белой фишки
        for r in range(6):
            for c in range(6):
                if board.grid[r][c] == 'ww':
                    # Базовый прогресс (0..5) → вес 20
                    score += c * 20

                    # Бонус за близость к победе
                    if c == 4:
                        score += 80
                        if board.grid[r][5] == '--':
                            score += 300   # прямой победный ход
                    elif c == 5:
                        score += 5000      # уже победа (check_win сработает раньше)

                    # Штраф за то, что фишка заперта
                    if not board.get_valid_moves(r, c, 'white'):
                        score -= 50

                elif board.grid[r][c] == 'bb':
                    # Прогресс чёрных (5 - r) — чем выше, тем хуже для белых
                    progress = 5 - r
                    score -= progress * 20

                    if r == 1:
                        score -= 100
                        if board.grid[0][c] == '--':
                            score -= 400   # прямая угроза победы чёрных
                    elif r == 0:
                        score -= 5000

                    if not board.get_valid_moves(r, c, 'black'):
                        score += 30   # запертая чёрная фишка — хорошо для белых

        # Подвижность: разница в количестве ходов
        white_moves = len(self._get_all_moves(board, 'white'))
        black_moves = len(self._get_all_moves(board, 'black'))
        score += (white_moves - black_moves) * 10

        return score
