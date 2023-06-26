from abc import ABC
from typing import Callable, Dict, Any, Awaitable

from aiogram import Bot, Dispatcher, BaseMiddleware

from aiogram.types import Message, CallbackQuery


class UtilsMiddleware(BaseMiddleware, ABC):

    def __init__(self, bot: Bot, dp: Dispatcher):
        super().__init__()
        self.bot = bot
        self.dp = dp

    async def on_pre_process_message(self, message: Message, data: dict):
        data["bot"] = self.bot
        data['dp'] = self.dp

    async def __call__(
            self,
            handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
            event: Message,
            data: Dict[str, Any]
    ):
        data['dp'] = self.dp
        return await handler(event, data)


class WorkersCallbackMiddleware(BaseMiddleware, ABC):

    async def __call__(
            self,
            handler: Callable[[CallbackQuery, Dict[str, Any]], Awaitable[Any]],
            event: CallbackQuery,
            data: Dict[str, Any]
    ):
        data["worker_id"] = event.data.split('_')[-1]
        return await handler(event, data)
