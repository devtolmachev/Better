from aiogram.utils.keyboard import ReplyKeyboardBuilder, KeyboardButton


def get_worker_markup():
    kb = ReplyKeyboardBuilder()
    btn1 = KeyboardButton(text='Что делаешь? ℹ️')
    btn2 = KeyboardButton(text='Сессия 👨🏻‍💻')
    kb.add(btn1, btn2)
    kb.adjust(2)
    return kb
