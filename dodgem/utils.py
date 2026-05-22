from constants import USERS_FILE
import json
import os

def caesar_encrypt(text, shift=3):
    """Шифрование шифром Цезаря"""
    result = ""
    for char in text:
        if char.isalpha():
            base = 'a' if char.islower() else 'A'
            result += chr((ord(char) - ord(base) + shift) % 26 + ord(base))
        else:
            result += char
    return result

def caesar_decrypt(text, shift=3):
    return caesar_encrypt(text, -shift)

def load_users():
    """Загружает пользователей из файла, расшифровывая пароли"""
    if os.path.exists(USERS_FILE):
        try:
            with open(USERS_FILE, 'r') as f:
                users = json.load(f)
                for username, data in users.items():
                    data['password'] = caesar_decrypt(data['password'])
                return users
        except:
            return {}
    return {}

def save_users(users):
    """Сохраняет пользователей в файл, шифруя пароли"""
    encrypted_users = {}
    for username, data in users.items():
        encrypted_users[username] = {
            'password': caesar_encrypt(data['password'])
        }
    with open(USERS_FILE, 'w') as f:
        json.dump(encrypted_users, f)