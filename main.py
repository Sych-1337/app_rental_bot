import json
from aiogram import Bot, Dispatcher, executor, types
from bot.config import BOT_TOKEN
import datetime
import os

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)

# Путь к JSON-файлу
DATA_FILE = os.path.join(os.path.dirname(__file__), "data.json")

# Загрузка данных из JSON
with open(DATA_FILE, "r", encoding="utf-8") as f:
    data = json.load(f)

tokens = data["tokens"]
apps = data["apps"]

# Авторизация пользователей
active_users = {}

@dp.message_handler(commands=["start"])
async def start(message: types.Message):
    await message.answer("Добро пожаловать! Введите /login {token} для входа.")

@dp.message_handler(commands=["login"])
async def login(message: types.Message):
    parts = message.text.strip().split()
    if len(parts) != 2:
        await message.reply("Используй формат: /login {token}")
        return

    token_value = parts[1]
    if token_value not in tokens:
        await message.reply("Неверный токен.")
        return

    telegram_id = str(message.from_user.id)
    active_users[telegram_id] = True

    # Показ приложений
    keyboard = types.InlineKeyboardMarkup()
    for app in apps:
        keyboard.add(types.InlineKeyboardButton(f"{app['emoji']} {app['name']}", callback_data=f"app_{app['id']}"))
    await message.answer("Список приложений:", reply_markup=keyboard)

@dp.callback_query_handler(lambda c: c.data.startswith("app_"))
async def show_app(call: types.CallbackQuery):
    telegram_id = str(call.from_user.id)
    if telegram_id not in active_users:
        await call.message.answer("Сначала авторизуйтесь через /login.")
        return

    app_id = int(call.data.split("_")[1])
    app = next((a for a in apps if a["id"] == app_id), None)
    if not app:
        await call.message.answer("Приложение не найдено.")
        return

    keyboard = types.InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        types.InlineKeyboardButton("🔙 Назад", callback_data="back"),
        types.InlineKeyboardButton("🧪 Протестировать нейминг", callback_data="test_name"),
        types.InlineKeyboardButton("➕ Добавить кабинет", callback_data="add_account"),
        types.InlineKeyboardButton("📋 Просмотреть кабинеты", callback_data="view_accounts")
    )
    await call.message.answer_photo(photo=app["image"], caption=f"<b>Приложение {app['emoji']} <a href='{app['link']}'>{app['name']}</a>:</b>",
                                    parse_mode="HTML", reply_markup=keyboard)

@dp.callback_query_handler(lambda c: c.data == "back")
async def go_back(call: types.CallbackQuery):
    telegram_id = str(call.from_user.id)
    keyboard = types.InlineKeyboardMarkup()
    for app in apps:
        keyboard.add(types.InlineKeyboardButton(f"{app['emoji']} {app['name']}", callback_data=f"app_{app['id']}"))
    await call.message.answer("Список приложений:", reply_markup=keyboard)

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
