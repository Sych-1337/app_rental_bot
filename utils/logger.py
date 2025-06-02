import logging
from datetime import datetime
import os

# Создаем директорию для логов, если она не существует
log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs')
os.makedirs(log_dir, exist_ok=True)

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(log_dir, f'bot_{datetime.now().strftime("%Y-%m-%d")}.log')),
        logging.StreamHandler()
    ]
)

# Создаем логгер для бота
logger = logging.getLogger('app_rental_bot')

# Декоратор для логирования ошибок
import functools

def log_errors(func):
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            logger.error(f"Error in {func.__name__}: {str(e)}", exc_info=True)
            raise
    return wrapper
