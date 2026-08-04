# Roadmap разработки: Telegram-бот мониторинга фриланс-бирж

Пошаговый план реализации проекта на основе документа [PRD.md](file:///e:/KworkBOT/.doc/PRD.md).

---

## 🚀 Этап 1: Настройка проекта и конфигурации

- [x] **1.1. Зависимости проекта (`requirements.txt`)**
  - [x] Создать файл `requirements.txt`
  - [x] Добавить `aiogram>=3.0` (для работы с Telegram Bot API)
  - [x] Добавить `aiohttp` (для асинхронных HTTP-запросов к биржам и API)
  - [x] Добавить `aiosqlite` (для асинхронной работы с SQLite)
  - [x] Добавить `python-dotenv` (для загрузки переменных из `.env`)
  - [x] Добавить `pydantic` (для валидации конфигурации)
  - [x] Добавить `cohere` (SDK для работы с Cohere API)

- [x] **1.2. Шаблон переменных окружения (`.env.example`)**
  - [x] Создать файл `.env.example`
  - [x] Добавить переменные: `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`
  - [x] Добавить переменные LLM: `COHERE_API_KEY`, `COHERE_MODEL`
  - [x] Добавить параметры фильтрации: `MY_SKILLS`, `RELEVANCE_THRESHOLD`, `POLL_INTERVAL_SECONDS`
  - [x] Добавить куки авторизации: `KWORK_COOKIES`, `YANDEX_COOKIES`

- [x] **1.3. Модуль конфигурации (`config.py`)**
  - [x] Создать файл `config.py`
  - [x] Реализовать чтение переменных окружения с помощью `python-dotenv`
  - [x] Добавить валидацию и типы данных для всех переменных (`COHERE_API_KEY`, `COHERE_MODEL` и др.)
  - [x] Добавить реестр активных бирж `EXCHANGES`

---

## 🗄️ Этап 2: База данных и модели данных

- [x] **2.1. Базовые структуры данных (`exchanges/base.py`)**
  - [x] Создать директорию `exchanges/` и файл `exchanges/__init__.py`
  - [x] Реализовать Python `@dataclass Order` с полями:
    - [x] `title: str`
    - [x] `description: str`
    - [x] `price: str`
    - [x] `deadline: str`
    - [x] `client: str`
    - [x] `source: str`
    - [x] `url: str`
  - [x] Создать абстрактный базовый класс `Exchange(ABC)` с асинхронным методом `fetch_orders(self, session: aiohttp.ClientSession) -> list[Order]`

- [x] **2.2. Модуль базы данных SQLite (`db.py`)**
  - [x] Создать файл `db.py`
  - [x] Реализовать функцию асинхронной инициализации БД `init_db()`
  - [x] Создать таблицу `orders` со структурой:
    - [x] `id INTEGER PRIMARY KEY AUTOINCREMENT`
    - [x] `title TEXT`, `description TEXT`, `price TEXT`, `deadline TEXT`, `client TEXT`, `source TEXT`
    - [x] `url TEXT UNIQUE` (уникальный индекс)
    - [x] `relevance INTEGER`
    - [x] `created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP`
  - [x] Реализовать функцию проверки существования заказа по `url`: `async def order_exists(url: str) -> bool`
  - [x] Реализовать функцию добавления нового заказа: `async def save_order(order: Order, relevance: int)`

---

## 🌐 Этап 3: Парсеры фриланс-бирж

- [x] **3.1. Парсер Kwork (`exchanges/kwork.py`)**
  - [x] Создать файл `exchanges/kwork.py`
  - [x] Наследовать класс `KworkExchange` от `Exchange`
  - [x] Реализовать передачу `KWORK_COOKIES` в заголовки запросов `aiohttp`
  - [x] Создать заглушку / логику получение списка заказов и маппинг в объекты `Order`

- [x] **3.2. Парсер Яндекс.Услуги (`exchanges/yandex_uslugi.py`)**
  - [x] Создать файл `exchanges/yandex_uslugi.py`
  - [x] Наследовать класс `YandexUslugiExchange` от `Exchange`
  - [x] Реализовать передачу `YANDEX_COOKIES` в заголовки запросов `aiohttp`
  - [x] Создать заглушку / логику получения списка заказов и маппинг в объекты `Order`

- [x] **3.3. Регистрация парсеров в `config.py`**
  - [x] Зарегистрировать экземпляры `KworkExchange` и `YandexUslugiExchange` в глобальном списке `EXCHANGES`

---

## 🤖 Этап 4: Интеграция с LLM (Cohere API)

- [x] **4.1. Сервис оценки релевантности (`llm.py`)**
  - [x] Создать файл `llm.py`
  - [x] Реализовать асинхронную функцию `async def evaluate_relevance(order_title: str, order_description: str) -> int`
  - [x] Сформировать системный промпт с передачей `MY_SKILLS`
  - [x] Настроить вызов Cohere API (`cohere.AsyncClient` или HTTP-запрос с моделью `COHERE_MODEL`)
  - [x] Реализовать парсинг ответа LLM и извлечение числового процента совпадения (0–100)
  - [x] Добавить обработку ошибок API и фоллбэк (возврат 0 при сбое)

---

## 📢 Этап 5: Сервис Telegram-уведомлений

- [x] **5.1. Модуль отправки сообщений (`notifier.py`)**
  - [x] Создать файл `notifier.py`
  - [x] Инициализировать экземпляр бота `Bot(token=TELEGRAM_BOT_TOKEN)` из `aiogram`
  - [x] Реализовать функцию форматирования HTML/Markdown-сообщения для заказа:
    - [x] Источник (биржа)
    - [x] Название заказа и ссылка
    - [x] Описание, цена и срок
    - [x] Заказчик
    - [x] Процент релевантности от LLM Cohere API
  - [x] Реализовать асинхронную функцию `async def send_order_notification(order: Order, relevance: int)`

---

## 🔄 Этап 6: Фоновый планировщик и Точка входа

- [x] **6.1. Фоновый планировщик (`scheduler.py`)**
  - [x] Создать файл `scheduler.py`
  - [x] Реализовать основной бесконечный цикл `async def start_scheduler()`
  - [x] Настроить таймер на основе `POLL_INTERVAL_SECONDS` (по умолчанию 60 сек)
  - [x] Реализовать пошаговый алгоритм:
    - [x] 1. Опрос всех зарегистрированных бирж через `fetch_orders()`
    - [x] 2. Проверка заказов на дубликаты через `db.order_exists(order.url)`
    - [x] 3. Сохранение новых заказов и запрос оценки релевантности через `llm.evaluate_relevance()`
    - [x] 4. Запись `relevance` в БД
    - [x] 5. Отправка уведомления через `notifier.send_order_notification()`, если `relevance >= RELEVANCE_THRESHOLD`
  - [x] Добавить обработку исключений внутри цикла опроса для непрерывной работы бота

- [x] **6.2. Точка входа в приложение (`main.py`)**
  - [x] Создать файл `main.py`
  - [x] Реализовать асинхронную функцию `main()`
  - [x] Выполнить инициализацию базы данных `init_db()`
  - [x] Запустить фоновую задачу планировщика `asyncio.create_task(start_scheduler())`
  - [x] Запустить `dp.start_polling(bot)` для обработки команд Telegram-бота
  - [x] Добавить грациозное завершение (graceful shutdown)

---

## 🧪 Этап 7: Тестирование и верификация

- [x] **7.1. Проверка окружения**
  - [x] Создать локальный файл `.env` на основе `.env.example`
  - [x] Заполнить реальными токенами: `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`, `COHERE_API_KEY`
  - [x] Выполнить установку зависимостей: `pip install -r requirements.txt`

- [x] **7.2. Функциональное тестирование**
  - [x] Запустить проект командой `python main.py`
  - [x] Проверить успешный запуск бота и отсутствие ошибок в логах
  - [x] Убедиться в автоматическом создании файла базы данных `orders.db`
  - [x] Проверить регулярный запуск планировщика раз в 60 секунд

- [x] **7.3. Интеграционное тестирование**
  - [x] Вручную вставить тестовый заказ через заглушку биржи
  - [x] Проверить запись заказа в таблицу `orders` в `orders.db`
  - [x] Убедиться в отправке запроса в Cohere API и корректности оценки релевантности
  - [x] Проверить получение форматированного уведомления в Telegram при совпадении >= 70%

---

## 📦 Этап 8: Публикация в Git и деплой на Vercel

- [x] **8.1. Загрузка в Git (GitHub / GitLab)**
  - [x] Создать файл `.gitignore` (исключить `.env`, `orders.db`, `__pycache__/`, `.venv/`, `.doc/`)
  - [x] Инициализировать Git-репозиторий (`git init`)
  - [x] Добавить файлы в индекс (`git add .`)
  - [x] Создать первый коммит (`git commit -m "Initial commit"`)
  - [x] Создать удаленный репозиторий на GitHub / GitLab
  - [x] Связать локальный репозиторий с удаленным (`git remote add origin ...`)
  - [x] Отправить изменения в ветку main (`git push -u origin main`)

- [x] **8.2. Подготовка к деплою на Vercel**
  - [x] Создать файл конфигурации `vercel.json` для поддержки Serverless Python / Cron Tasks
  - [x] Адаптировать точку входа под Vercel Serverless Functions (`api/cron.py`)
  - [x] Подключить удаленную базу данных (Turso / Supabase / Neon / Vercel Postgres) для сохранения историй заказов на Serverless

- [x] **8.3. Деплой на Vercel**
  - [x] Авторизоваться в Vercel CLI или импортировать Git-репозиторий в панели Vercel
  - [x] Добавить переменные окружения (Environment Variables) в панели управления Vercel:
    - [x] `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`
    - [x] `COHERE_API_KEY`, `COHERE_MODEL`
    - [x] `MY_SKILLS`, `RELEVANCE_THRESHOLD`
    - [x] `KWORK_COOKIES`, `YANDEX_COOKIES`
  - [x] Выполнить деплой (`vercel --prod` или через автодеплой по push в GitHub)
  - [x] Проверить логи выполнения функций и работоспособность Cron-триггера в панели Vercel

---

## 🔮 Этап 9: Реальный парсинг заказов и автоматизация 24/7

- [x] **9.1. Реальный парсинг Kwork (`exchanges/kwork.py`)**
  - [x] Реализовать HTTP-запрос к ленте проектов Kwork (`/projects`) через `aiohttp` с `KWORK_COOKIES`
  - [x] Настроить извлечение заголовка, описания, бюджета, срока, автора и ссылки на проект через `BeautifulSoup`

- [x] **9.2. Реальный парсинг Яндекс.Услуг (`exchanges/yandex_uslugi.py`)**
  - [x] Реализовать HTTP-запрос к заказам Яндекс.Услуг с `YANDEX_COOKIES`
  - [x] Настроить парсинг данных заказа и маппинг в объекты `Order`

- [x] **9.3. Автоматизация опроса 24/7 через `cron-job.org`**
  - [x] Зарегистрировать Cron-задание на `cron-job.org` с вызовом `https://kworkbot-mu.vercel.app/`
  - [x] Установить периодичность выполнения каждые 1–5 минут

- [x] **9.4. Тонкая настройка фильтрации и навыков**
  - [x] Настроить детальный список `MY_SKILLS` в `.env` и Vercel
  - [x] Оптимизировать промпт оценки Cohere AI для исключения ложных срабатываний (использование актуальной модели `command-r-08-2024`)

- [x] **9.5. Масштабирование (Подключение дополнительных бирж)**
  - [x] Разработать модуль парсинга FL.ru (`exchanges/fl_ru.py`)
  - [x] Зарегистрировать новые биржи в `EXCHANGES` в `config.py`

---

## 🍪 Этап 10: Сессионные куки авторизации для доступа к закрытым заказам

- [x] **10.1. Настройка куков Kwork (`KWORK_COOKIES`)**
  - [x] Извлечь Cookie-строку авторизованной сессии из браузера на kwork.ru
  - [x] Записать значение в `.env` и в переменные окружения Vercel Production

- [ ] **10.2. Настройка куков Яндекс.Услуги (`YANDEX_COOKIES`)**
  - [ ] Извлечь Cookie-строку авторизованной сессии из браузера на uslugi.yandex.ru
  - [ ] Записать значение в `.env` и в переменные окружения Vercel Production

---

## 🤖 Этап 11: Улучшение UX уведомлений и ИИ сопроводительные письма (Cover Letters)

- [x] **11.1. Генерация авто-откликов через ИИ (`llm.py`)**
  - [x] Добавить асинхронную функцию `async def generate_cover_letter(order_title: str, order_description: str) -> str`
  - [x] Сформировать промпт Cohere AI для создания короткого, продающего и убедительного сопроводительного письма на основе `MY_SKILLS`
  - [x] Прикреплять сгенерированное сопроводительное письмо прямо в Telegram-сообщение для копирования в 1 клик (`<code>` формат)

- [x] **11.2. Inline-кнопки быстрого отклика в Telegram (`notifier.py`)**
  - [x] Добавить `InlineKeyboardMarkup` и `InlineKeyboardButton` под каждым отправленным заказом
  - [x] Настроить кнопку `[ 🚀 Откликнуться на {source} ]` с прямой URL-ссылкой на заказ



