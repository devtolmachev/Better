from typing import Iterable

from aiogram.types import (InlineKeyboardButton, InlineKeyboardMarkup)
from aiogram.utils.keyboard import InlineKeyboardBuilder

buttons = []


class Pagination:
    buttons: list[list[InlineKeyboardButton]] = []

    @classmethod
    def create_pagination(
            cls,
            callback_data: str,
            data: Iterable = range(81),
            type_pagination: str = 'value_counter',
            sep: str = '_',
    ) -> InlineKeyboardBuilder:

        kb = InlineKeyboardBuilder()

        conf = []
        for i in data:
            cd = callback_data.split(sep)
            cd.insert(-2, f"${type_pagination}_{i}$")
            data = {
                "text": i,
                "callback_data": sep.join(cd)
            }
            conf.append(data)

        [
            kb.add(InlineKeyboardButton(**d))
            for d in conf
        ]

        builder = kb.copy()
        cls.buttons = builder.as_markup().inline_keyboard
        reply_markup = builder.as_markup().inline_keyboard.copy()

        conf_for_last_buttons = [
            {
                "callback_data": (f"{v}_liga:%s_%s" % (
                    callback_data.split('_')[-2], callback_data.split('_')[-1]
                )),
                "text": n
            }

            for v, n in [("force next", "В конец »"),
                         ("on_page_num",
                          f"1 / {len(reply_markup)}"),
                         ("next", "Вперед »")]
        ]

        btns = [
            InlineKeyboardButton(**d)
            for d in conf_for_last_buttons
        ]

        kbn = InlineKeyboardBuilder(markup=[reply_markup[0]])
        kbn.adjust(2)
        kbn.row(*btns)

        return kbn

    @classmethod
    def change_step(cls,
                    action: str,
                    btns: InlineKeyboardMarkup,
                    callback_data: str) -> InlineKeyboardMarkup:

        all_buttons = cls.buttons.copy()
        reply_markup = btns.inline_keyboard.copy()
        num = [
            reply_markup[-2].index(x)
            for x in reply_markup[-2]
            if x.text.split(' /')[0].isdigit()
        ][0]

        page_num = int(reply_markup[-2][num].text.split(' /')[0])
        page_max = int(reply_markup[-2][num].text.split(' /')[-1])

        if action.count("force"):

            if action.count("back"):
                conf = [
                    {
                        "callback_data": (f"{v}_liga:%s_%s" % (
                            callback_data.split('_')[-2],
                            callback_data.split('_')[-1]
                        )),
                        "text": n
                    }
                    for v, n in [("force next", "В конец »"),
                                 ("on_page_num",
                                  f"{1} / {len(all_buttons)}"),
                                 ("next", "Вперед »")]
                ]

                if page_num - 1 == 1:
                    [
                        conf.remove(conf[conf.index(d)])
                        for d in conf
                        for action in [d["text"]]
                        if action.lower().count('в конец')
                    ]

                kb = InlineKeyboardBuilder(markup=[all_buttons[0]])

            elif action.count('next'):
                conf = [
                    {
                        "callback_data": (f"{v}_liga:%s_%s" % (
                            callback_data.split('_')[-2],
                            callback_data.split('_')[-1]
                        )),
                        "text": n
                    }
                    for v, n in [("back", "« Назад"),
                                 ("on_page_num",
                                  f"{len(all_buttons)} / {len(all_buttons)}"),
                                 ("force back", "« В начало")]
                ]

                kb = InlineKeyboardBuilder(markup=[all_buttons[-1]])

        elif action.count("next"):
            conf = [
                {
                    "callback_data": (f"{v}_liga:%s_%s" % (
                        callback_data.split('_')[-2],
                        callback_data.split('_')[-1]
                    )),
                    "text": n
                }
                for v, n in [("back", "« Назад"),
                             ("on_page_num",
                              f"{page_num + 1} / {len(all_buttons)}"),
                             ("next", "Вперед »")]
            ]

            kb = InlineKeyboardBuilder(markup=[all_buttons[page_num]])

            if page_num + 1 >= page_max:
                index_row = [
                    conf.index(d)
                    for d in conf
                    for action in [d["text"]]
                    if action.count('Вперед')
                ][0]
                conf.remove(conf[index_row])
                conf.insert(index_row, {
                    "callback_data": (f"force back_liga:%s_%s" % (
                        callback_data.split('_')[-2],
                        callback_data.split('_')[-1]
                    )),
                    "text": "« В начало"
                })

        elif action.count('back'):
            conf = [
                {
                    "callback_data": (f"{v}_liga:%s_%s" % (
                        callback_data.split('_')[-2],
                        callback_data.split('_')[-1]
                    )),
                    "text": n
                }
                for v, n in [("back", "« Назад"),
                             ("on_page_num",
                              f"{page_num - 1} / {len(all_buttons)}"),
                             ("next", "Вперед »")]
            ]

            kb = InlineKeyboardBuilder(markup=[all_buttons[page_num - 2]])

            if page_num - 1 <= 1:
                index_row = [
                    conf.index(d)
                    for d in conf
                    for act in [d["text"]]
                    if act.lower().count('назад')
                ][0]
                conf.remove(conf[index_row])
                conf.insert(index_row, {
                    "callback_data": (f"force next_liga:%s_%s" % (
                        callback_data.split('_')[-2],
                        callback_data.split('_')[-1]
                    )),
                    "text": "В конец »"
                })

        else:
            raise NotImplementedError

        btns = [
            InlineKeyboardButton(**d)
            for d in conf
        ]

        kb.adjust(2)
        kb.row(*btns)

        return kb.as_markup()
