from aiogram import Bot, Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage

bot = Bot('5850270789:AAHKM0JydPisdobNE79cLQ1J41SOh_Pyn8Q', parse_mode='HTML')
dp = Dispatcher(bot, storage=MemoryStorage())
