import os
import tempfile
from pathlib import Path
from dotenv import load_dotenv

# Загрузка переменных окружения из .env файла
BASE_DIR = Path(__file__).resolve().parent
env_path = BASE_DIR / ".env"
load_dotenv(dotenv_path=env_path)

# Telegram Настройки
TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
TELEGRAM_CHAT_ID: str = os.getenv("TELEGRAM_CHAT_ID", "").strip()

# LLM Настройки (Cohere API)
COHERE_API_KEY: str = os.getenv("COHERE_API_KEY", "").strip()
COHERE_MODEL: str = os.getenv("COHERE_MODEL", "command-r-plus").strip()

# Фильтрация и планировщик
MY_SKILLS: str = os.getenv("MY_SKILLS", "Python, веб-разработка").strip()
RELEVANCE_THRESHOLD: int = int(os.getenv("RELEVANCE_THRESHOLD", "70"))
POLL_INTERVAL_SECONDS: int = int(os.getenv("POLL_INTERVAL_SECONDS", "60"))

# Авторизационные куки бирж
KWORK_COOKIES: str = os.getenv("KWORK_COOKIES", "").strip()
YANDEX_COOKIES: str = os.getenv("YANDEX_COOKIES", "").strip()

# Путь к БД SQLite (на Vercel используем временную папку /tmp)
IS_VERCEL: bool = os.getenv("VERCEL") == "1" or os.getenv("VERCEL_ENV") is not None
if IS_VERCEL:
    DB_PATH: Path = Path(tempfile.gettempdir()) / "orders.db"
else:
    DB_PATH: Path = BASE_DIR / "orders.db"

# Реестр активных бирж
EXCHANGES: list = []

try:
    from exchanges.kwork import KworkExchange
    from exchanges.yandex_uslugi import YandexUslugiExchange

    EXCHANGES = [
        KworkExchange(),
        YandexUslugiExchange(),
    ]
except Exception:
    pass
