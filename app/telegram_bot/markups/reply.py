from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


def get_online_scan_kb():
    kb = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    btn1 = KeyboardButton('Что ты делаешь❓')
    btn2 = KeyboardButton('Завершить сканирование ❌')
    kb.add(btn1, btn2)
    return kb


def get_start_kb():
    kb = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    btn1 = KeyboardButton('Рандомайзер')
    btn2 = KeyboardButton('Сценарии')
    kb.add(btn1, btn2)
    return kb
