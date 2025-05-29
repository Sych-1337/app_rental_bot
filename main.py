from aiogram import Bot, Dispatcher, executor, types
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from bot.config import BOT_TOKEN, DATABASE_URL
from bot.models import Base, App, Token, User
import datetime

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)

engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
session = Session()

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
    token = session.query(Token).filter_by(token=token_value).first()

    if not token:
        await message.reply("Неверный токен.")
        return

    telegram_id = str(message.from_user.id)
    user = session.query(User).filter_by(telegram_id=telegram_id).first()

    if not user:
        user = User(telegram_id=telegram_id, login_time=datetime.datetime.utcnow())
        session.add(user)
        session.commit()

    active_users[telegram_id] = True

    # Показ приложений
    apps = session.query(App).all()
    keyboard = types.InlineKeyboardMarkup()
    for app in apps:
        keyboard.add(types.InlineKeyboardButton(f"{app.emoji} {app.name}", callback_data=f"app_{app.id}"))
    await message.answer("Список приложений:", reply_markup=keyboard)

@dp.callback_query_handler(lambda c: c.data.startswith("app_"))
async def show_app(call: types.CallbackQuery):
    telegram_id = str(call.from_user.id)
    if telegram_id not in active_users:
        await call.message.answer("Сначала авторизуйтесь через /login.")
        return

    app_id = int(call.data.split("_")[1])
    app = session.query(App).filter_by(id=app_id).first()
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
    await call.message.answer_photo(photo=app.image, caption=f"<b>Приложение {app.emoji} <a href='{app.link}'>{app.name}</a>:</b>",
                                    parse_mode="HTML", reply_markup=keyboard)

@dp.callback_query_handler(lambda c: c.data == "back")
async def go_back(call: types.CallbackQuery):
    telegram_id = str(call.from_user.id)
    apps = session.query(App).all()
    keyboard = types.InlineKeyboardMarkup()
    for app in apps:
        keyboard.add(types.InlineKeyboardButton(f"{app.emoji} {app.name}", callback_data=f"app_{app.id}"))
    await call.message.answer("Список приложений:", reply_markup=keyboard)

if __name__ == "__main__":
    Base.metadata.create_all(engine)
    executor.start_polling(dp, skip_updates=True)