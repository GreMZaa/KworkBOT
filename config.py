import os
from pathlib import Path
from dotenv import load_dotenv

# Загрузка переменных окружения из .env файла
BASE_DIR = Path(__file__).resolve().parent
env_path = BASE_DIR / ".env"
load_dotenv(dotenv_path=env_path)

# Telegram Настройки
TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID: str = os.getenv("TELEGRAM_CHAT_ID", "")

# LLM Настройки (Cohere API)
COHERE_API_KEY: str = os.getenv("COHERE_API_KEY", "")
COHERE_MODEL: str = os.getenv("COHERE_MODEL", "command-r-plus")

# Фильтрация и планировщик
MY_SKILLS: str = os.getenv("MY_SKILLS", "Python, веб-разработка")
RELEVANCE_THRESHOLD: int = int(os.getenv("RELEVANCE_THRESHOLD", "70"))
POLL_INTERVAL_SECONDS: int = int(os.getenv("POLL_INTERVAL_SECONDS", "60"))

# Авторизационные куки бирж
KWORK_COOKIES: str = os.getenv("KWORK_COOKIES", "")
YANDEX_COOKIES: str = os.getenv("YANDEX_COOKIES", "")

# Пути к файлам
DB_PATH: Path = BASE_DIR / "orders.db"

# Импорт и регистрация активных фриланс-бирж
from exchanges.kwork import KworkExchange
from exchanges.yandex_uslugi import YandexUslugiExchange

EXCHANGES: list = [
    KworkExchange(),
    YandexUslugiExchange(),
]
