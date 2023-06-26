from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder


def get_start_kb() -> ReplyKeyboardMarkup:
    kb = ReplyKeyboardBuilder()
    btn1 = KeyboardButton(text='Мой профиль⬆️')
    btn2 = KeyboardButton(text='Добавить помощника👨👨🏻‍💻')
    btn3 = KeyboardButton(text='Меню запуска ботов')
    kb.add(btn1, btn2, btn3)
    kb.adjust(2)
    return kb.as_markup(resize_keyboard=True)


class MyProfileNavigation:

    @staticmethod
    def get_options_profile() -> ReplyKeyboardMarkup:
        kb = ReplyKeyboardBuilder()
        btn1 = KeyboardButton(text='Настройки⚙️')
        btn2 = KeyboardButton(text='Мои помощники🧑🏽‍🤝‍🧑🏿')
        return kb.add(btn1, btn2).as_markup(resize_keyboard=True)

