import json
from aiogram import Bot, Dispatcher, executor, types
from bot.config import BOT_TOKEN
import os
from utils.logger import logger, log_errors
import sys

# Проверка BOT_TOKEN
if not BOT_TOKEN or BOT_TOKEN.startswith('YOUR_') or BOT_TOKEN.strip() == '' or 'example' in BOT_TOKEN:
    logger.error(f"BOT_TOKEN не задан или некорректен: '{BOT_TOKEN}'")
    print(f"FATAL: BOT_TOKEN не задан или некорректен: '{BOT_TOKEN}'", file=sys.stderr)
    sys.exit(1)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)

# Проверка наличия файлов токенов и папки с приложениями
TOKENS_PATH = os.path.join(os.path.dirname(__file__), 'site', 'tokens.json')
APPS_DIR = os.path.join(os.path.dirname(__file__), 'site', 'apps')

if not os.path.isfile(TOKENS_PATH):
    logger.error(f"Файл токенов не найден: {TOKENS_PATH}")
    print(f"FATAL: Файл токенов не найден: {TOKENS_PATH}", file=sys.stderr)
    sys.exit(2)
if not os.path.isdir(APPS_DIR):
    logger.error(f"Папка с приложениями не найдена: {APPS_DIR}")
    print(f"FATAL: Папка с приложениями не найдена: {APPS_DIR}", file=sys.stderr)
    sys.exit(3)

# Загружаем токены из site/tokens.json

def load_tokens():
    with open(TOKENS_PATH, encoding='utf-8') as f:
        data = json.load(f)
    if not isinstance(data.get('tokens', []), list):
        logger.error(f"tokens.json: поле 'tokens' не является списком!")
        sys.exit(4)
    return set(data.get('tokens', []))

tokens_set = load_tokens()
active_users = set()

# Загружаем список приложений из site/apps/*.json

def load_apps():
    apps = []
    for fname in os.listdir(APPS_DIR):
        if fname.endswith('.json'):
            try:
                with open(os.path.join(APPS_DIR, fname), encoding='utf-8') as f:
                    app = json.load(f)
                    app['id'] = fname[:-5]
                    apps.append(app)
            except Exception as e:
                logger.error(f"Ошибка чтения {fname}: {e}")
    return apps

def get_support_url(app):
    # Если в app есть поле support_url — использовать его, иначе rent_url, иначе t.me/kotlincaptain
    return app.get('support_url') or app.get('rent_url') or 'https://t.me/kotlincaptain'

@dp.message_handler(commands=["start"])
@log_errors
async def start(message: types.Message):
    logger.info(f"User {message.from_user.id} started the bot")
    await message.answer(
        "Добро пожаловать!\n\nДля доступа к приложениям введите /login {токен}, где токен — это строка из списка, выданного вам администратором.\n\nПосле входа используйте команду /apps для просмотра доступных приложений."
    )

@dp.message_handler(commands=["login"])
@log_errors
async def login(message: types.Message, state=None):
    logger.info(f"User {message.from_user.id} attempting to login")
    parts = message.text.strip().split()
    if len(parts) != 2:
        await message.reply("Используй формат: /login {токен}")
        return
    token = parts[1]
    if token not in tokens_set:
        await message.reply("Неверный токен. Попробуйте ещё раз или обратитесь к администратору.")
        return
    active_users.add(message.from_user.id)
    await message.reply("Успешно! Теперь вы можете использовать /apps для просмотра приложений.")

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
@log_errors
async def apps(message: types.Message):
    if message.from_user.id not in active_users:
        await message.reply("Сначала авторизуйтесь через /login.")
        return
    # Путь к папке с json-файлами приложений
    APPS_DATA_DIR = os.path.join(os.path.dirname(__file__), 'apps_data')
    if not os.path.isdir(APPS_DATA_DIR):
        await message.reply("Папка с приложениями не найдена.")
        return
    apps = []
    for fname in os.listdir(APPS_DATA_DIR):
        if fname.endswith('.json'):
            try:
                with open(os.path.join(APPS_DATA_DIR, fname), encoding='utf-8') as f:
                    app = json.load(f)
                    apps.append(app)
            except Exception as e:
                logger.error(f"Ошибка чтения {fname}: {e}")
    if not apps:
        await message.reply("Нет доступных приложений.")
        return
    # Формируем общий текст для всех приложений
    msg = "<b>Доступные приложения:</b>\n\n"
    for app in apps:
        features = '\n'.join(f'- {f}' for f in app.get('features', []))
        msg += f"<b>{app.get('name', 'Без названия')}</b>\n"
        msg += f"<a href='{app.get('package_url', '#')}' target='_blank'>Ссылка на приложение</a>\n"
        msg += f"Версия: {app.get('version', '-') }\n"
        msg += f"Описание: {app.get('description', '-') }\n"
        if features:
            msg += f"<b>Функции:</b>\n{features}\n"
        msg += "\n"
    await message.reply(msg.strip(), parse_mode="HTML")

@dp.callback_query_handler(lambda c: c.data == "back")
async def go_back(call: types.CallbackQuery):
    telegram_id = str(call.from_user.id)
    keyboard = types.InlineKeyboardMarkup()
    for app in apps:
        keyboard.add(types.InlineKeyboardButton(f"{app['emoji']} {app['name']}", callback_data=f"app_{app['id']}"))
    await call.message.answer("Список приложений:", reply_markup=keyboard)

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
