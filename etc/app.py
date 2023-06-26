from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram_dialog.manager.setup import DialogRegistry

from aiohttp import web

bot = Bot('6190384741:AAF3QiDU4tpbeJ-Qoy5W-yEin17zs3yBrjg', parse_mode='HTML')
dp = Dispatcher(storage=MemoryStorage())
registry = DialogRegistry(dp)
CHAT_ID = -942872631
app = web.Application()
webhook_url = (
    'https://b699-2a00-1370-8182-ff9-dfe5-1765-afe0-bf8b.ngrok-free.app'
)
