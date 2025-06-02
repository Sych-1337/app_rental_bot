import json
from aiogram import Bot, Dispatcher, executor, types
from bot.config import BOT_TOKEN
import datetime
import os
from utils.logger import logger, log_errors
from utils.app_manager import AppManager

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)

# Инициализация менеджера приложений
app_manager = AppManager(os.path.join(os.path.dirname(__file__), "apps_data"))

# Загрузка токенов
tokens = {
    "abc123": "user1",
    "def456": "user2"
}

# Авторизация пользователей
active_users = {}

@dp.message_handler(commands=["start"])
@log_errors
async def start(message: types.Message):
    logger.info(f"User {message.from_user.id} started the bot")
    await message.answer("Добро пожаловать! Введите /login {token} для входа.")

@dp.message_handler(commands=["login"])
@log_errors
async def login(message: types.Message):
    logger.info(f"User {message.from_user.id} attempting to login")
    parts = message.text.strip().split()
    
    if len(parts) != 2:
        logger.warning(f"User {message.from_user.id} used incorrect login format")
        await message.reply("Используй формат: /login {token}")
        return

    token_value = parts[1]
    if token_value not in tokens:
        logger.warning(f"User {message.from_user.id} tried invalid token")
        await message.reply("Неверный токен.")
        return

    telegram_id = str(message.from_user.id)
    active_users[telegram_id] = True
    logger.info(f"User {message.from_user.id} successfully logged in")

    # Показ приложений
    keyboard = types.InlineKeyboardMarkup()
    user_role = tokens[token_value]
    user_apps = app_manager.get_apps_for_user(user_role)
    
    for app in user_apps:
        keyboard.add(types.InlineKeyboardButton(f"{app['name']}", callback_data=f"app_{app['id']}"))
    await message.answer("Список приложений:", reply_markup=keyboard)

@dp.callback_query_handler(lambda c: c.data.startswith("app_"))
@log_errors
async def show_app(call: types.CallbackQuery):
    telegram_id = str(call.from_user.id)
    if telegram_id not in active_users:
        logger.warning(f"User {telegram_id} tried to access app without login")
        await call.message.answer("Сначала авторизуйтесь через /login.")
        return

    try:
        app_id = call.data.split("_")[1]
        user_role = tokens[active_users[telegram_id]]
    except (ValueError, IndexError):
        logger.error(f"Invalid app callback data: {call.data}")
        await call.message.answer("Ошибка при обработке приложения.")
        return

    # Получаем приложение из менеджера
    app = app_manager.get_app(app_id)
    if not app:
        logger.warning(f"User {telegram_id} tried to access non-existent app {app_id}")
        await call.message.answer("Приложение не найдено.")
        return

    # Создаем клавиатуру с кнопками Google Play и Аренды
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        types.InlineKeyboardButton("Google Play", url=app['package_url']),
        types.InlineKeyboardButton("Аренда", callback_data=f"rent_{app_id}"),
        types.InlineKeyboardButton("🔙 Назад", callback_data="back")
    )

    # Формируем сообщение с информацией о приложении
    features = "\n• ".join(app.get("features", []))
    message = f"<b>{app['name']}</b>\n\n"
    message += f"<i>{app['description']}</i>\n\n"
    message += f"<b>Функции:</b>\n• {features}"

    logger.info(f"User {telegram_id} viewing app {app['name']}")
    await call.message.answer_photo(
        photo=app['icon_url'],
        caption=message,
        parse_mode="HTML",
        reply_markup=keyboard
    )

@dp.callback_query_handler(lambda c: c.data.startswith("rent_"))
@log_errors
async def handle_rent(call: types.CallbackQuery):
    telegram_id = str(call.from_user.id)
    app_id = call.data.split("_")[1]
    app = app_manager.get_app(app_id)
    
    if app:
        await call.message.answer(
            "Для аренды приложения пишите @kotlincaptain"
        )
    else:
        logger.warning(f"User {telegram_id} tried to rent non-existent app {app_id}")
        await call.message.answer("Приложение не найдено.")

@dp.message_handler(commands=["apps"])
async def apps(message: types.Message):
    user = active_users.get(message.from_user.id)
    if not user:
        await message.reply("Сначала авторизуйтесь через /login.")
        return

    apps = DATA["apps"].get(user, [])
    if not apps:
        await message.reply("Нет доступных приложений.")
        return

    for app in apps:
        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton("Mini App 🌐", url=app["mini_app"]))
        kb.add(types.InlineKeyboardButton("Конфиг 📄", url=app["url"]))
        await message.reply(f"📱 <b>{app['name']}</b>", reply_markup=kb, parse_mode="HTML")

@dp.callback_query_handler(lambda c: c.data == "back")
async def go_back(call: types.CallbackQuery):
    telegram_id = str(call.from_user.id)
    keyboard = types.InlineKeyboardMarkup()
    for app in apps:
        keyboard.add(types.InlineKeyboardButton(f"{app['emoji']} {app['name']}", callback_data=f"app_{app['id']}"))
    await call.message.answer("Список приложений:", reply_markup=keyboard)

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
