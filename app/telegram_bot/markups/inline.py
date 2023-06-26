from aiogram.types import (InlineKeyboardMarkup,
                           InlineKeyboardButton,
                           CallbackQuery)
from aiogram.utils.keyboard import InlineKeyboardBuilder


def check_button(match_id: str) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    btn = InlineKeyboardButton(text='ℹ️', callback_data=f"info_{match_id}")
    kb.add(btn)
    kb.adjust(2)
    return kb.as_markup()


class Navigation:

    @staticmethod
    def back_button(
            to: str = 'worker', call: CallbackQuery = None,
            **kwargs
    ) -> InlineKeyboardButton:
        position = kwargs["position"] if kwargs.get('position') else 0
        direction = kwargs["direction"] if kwargs.get('direction') else 'right'
        element = kwargs["element"] if kwargs.get('element') else '«'
        call = kwargs["call_"] if kwargs.get("call_") else call

        if to.lower().count('worker'):
            text = 'Назад к боту'
            text = text.split()
            text.append(element) if position == -1 \
                else text.insert(position, element)
            text = ' '.join(text)

            btn = InlineKeyboardButton(
                text=text,
                callback_data=f'back_to_worker_{call.data.split("_")[-1]}'
            )

        elif to.lower().count('list'):
            text = 'Назад к списку ботов'
            text = text.split()
            text.append(element) if position == -1 \
                else text.insert(position, element)
            text = ' '.join(text)

            btn = InlineKeyboardButton(text=text,
                                       callback_data=f'list_workers'),

        else:
            text = 'Назад'
            if kwargs.get("text"):
                text = kwargs["text"]
            text = text.split()
            text.append(element) if position == -1 \
                else text.insert(position, element)
            text = ' '.join(text)

            btn = InlineKeyboardButton(
                text=text,
                callback_data=(
                    call.data if isinstance(call, CallbackQuery) else call
                )
            ),

        return btn

    @staticmethod
    def apply_button(apply: str, call: CallbackQuery) -> InlineKeyboardButton:
        if apply not in ['strategy', 'token', 'bookmaker']:
            raise NotImplementedError('Применить настройки для объекта '
                                      f'{apply} невозможно!!!')

        if apply.count('strategy'):
            id = call.data.split('_')[-1]
            btn = InlineKeyboardButton(
                text='Применить ✅',
                callback_data=f'apply_changes_{apply}_{id}'
            )

        return btn

    @staticmethod
    def edit_success_btn(
            btns: list[InlineKeyboardButton],
            call: CallbackQuery
    ) -> InlineKeyboardBuilder:
        kb = InlineKeyboardBuilder()
        for btn in btns:

            if btn.text.count('✅') and btn.callback_data == call.data:
                btn.text = btn.text.split('✅ (')[1].split(')')[0]

            elif btn.callback_data == call.data and all(
                    [not x.text.count("✅") for x in btns]
            ):
                btn.text = f"✅ ({btn.text})"

            elif btn.callback_data == call.data and not all(
                    [not x.text.count('✅') for x in btns]
            ):
                for x in btns:
                    try:
                        x.text = x.text.split('✅ (')[1].split(')')[0]
                    except IndexError:
                        pass

                btn.text = f"✅ ({btn.text})"

            kb.add(btn)

        return kb
