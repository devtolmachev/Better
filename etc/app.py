from aiogram import Bot, Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage


bot = Bot('6190384741:AAF3QiDU4tpbeJ-Qoy5W-yEin17zs3yBrjg', parse_mode='HTML')
dp = Dispatcher(bot, storage=MemoryStorage())

