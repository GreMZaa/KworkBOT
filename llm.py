import re
import json
import logging
import aiohttp
import config

logger = logging.getLogger(__name__)

# Ключевые фразы мошенников и подозрительных схем
SCAM_KEYWORDS = [
    "залоговый взнос",
    "страховой взнос",
    "оплата за материалы",
    "напишите в телеграм",
    "пишите в телеграм",
    "напишите в тг",
    "пишите в тг",
    "пишите в tg",
    "напишите в tg",
    "контакт в тг",
    "контакт в телеграм",
    "перевод за пределы биржи",
    "бесплатное тестовое на",
    "залог перед работой",
    "оплата страхового взноса"
]


def check_is_scam(order_title: str, order_description: str) -> tuple[bool, str]:
    """
    Проверяет заказ на признаки мошенничества (скама).
    """
    text_to_check = f"{order_title} {order_description}".lower()

    for kw in SCAM_KEYWORDS:
        if kw in text_to_check:
            logger.warning(f"Обнаружен подозрительный элемент мошенничества: '{kw}'")
            return True, f"Обнаружена подозрительная фраза: '{kw}'"

    return False, ""


async def evaluate_relevance(order_title: str, order_description: str) -> int:
    """
    Оценивает релевантность заказа навыкам пользователя с помощью Cohere API.
    """
    if not config.COHERE_API_KEY:
        logger.warning("COHERE_API_KEY не установлен в .env. Возвращается 0%.")
        return 0

    skills = config.MY_SKILLS
    prompt = f"""Ты — ИИ-ассистент, который оценивает релевантность заказа для фрилансера.

Навыки фрилансера: {skills}

Информация о заказе:
Заголовок: {order_title}
Описание: {order_description}

Задание:
Оцени от 0 до 100 насколько этот заказ подходит под навыки фрилансера.
В ответе выведи ТОЛЬКО одно число от 0 до 100 без скобок, текста или процентов."""

    url = "https://api.cohere.com/v2/chat"
    headers = {
        "Authorization": f"Bearer {config.COHERE_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": config.COHERE_MODEL,
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ]
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=payload, timeout=15) as response:
                if response.status == 200:
                    data = await response.json()
                    content = ""
                    if "message" in data and "content" in data["message"]:
                        for block in data["message"]["content"]:
                            if block.get("type") == "text":
                                content += block.get("text", "")
                    elif "text" in data:
                        content = data["text"]

                    match = re.search(r'\b(100|[1-9]?\d)\b', content.strip())
                    if match:
                        score = int(match.group(1))
                        logger.info(f"Cohere оценил заказ '{order_title}' на {score}%")
                        return score
                    else:
                        logger.warning(f"Не удалось распарсить число из ответа Cohere: {content}")
                        return 0
                else:
                    error_text = await response.text()
                    logger.error(f"Ошибка Cohere API ({response.status}): {error_text}")
                    return 0
    except Exception as e:
        logger.error(f"Исключение при вызове Cohere API: {e}")
        return 0


async def analyze_order_deep(order_title: str, order_description: str, client_price: str = "") -> dict:
    """
    Выполняет глубокий ИИ-анализ заказа:
    - Рыночная цена (не то что хочет клиент, а реальная стоимость разработки на рынке)
    - Оценка сложности (Легкая / Средняя / Высокая)
    - Ориентировочные часы работы
    - Стек технологий
    - ИИ-совет к отклику
    - Хештеги
    - Сопроводительное письмо
    """
    default_result = {
        "market_price": "3 000 — 5 000 руб.",
        "difficulty": "Средняя",
        "estimated_time": "2-4 часа",
        "tech_stack": "Python, Web Scraping, SQLite",
        "ai_tip": "Заказчик ищет быстрое решение. Подчеркните готовность сдать работу в сжатые сроки.",
        "hashtags": "#python #freelance #kwork #development",
        "cover_letter": "Здравствуйте! Готов качественно и в срок выполнить ваш заказ. Имею большой опыт разработки на Python и работы с API."
    }

    if not config.COHERE_API_KEY:
        return default_result

    skills = config.MY_SKILLS
    prompt = f"""Ты — Senior IT-консультант и фрилансер. Сделай глубокий экспертный анализ заказа на разработку.

Навыки фрилансера: {skills}
Заголовок заказа: {order_title}
Описание заказа: {order_description}
Бюджет заказчика: {client_price}

Сформируй ответ СТРОГО в формате валидного JSON-объекта без лишнего текста, без ```json:
{{
  "market_price": "РЕАЛЬНАЯ РЫНОЧНАЯ ЦЕНА на рынке фриланса (например: '3 000 — 5 000 руб.' или '15 000 — 25 000 руб.')",
  "difficulty": "Сложность (выбери из: Легкая / Средняя / Высокая)",
  "estimated_time": "Время разработки (например: '2-4 часа' или '1-2 дня')",
  "tech_stack": "Рекомендуемый стек (например: 'Python, Aiogram 3, SQLite')",
  "ai_tip": "1 короткий практический совет фрилансеру при отклике и обсуждении бюджета",
  "hashtags": "4-5 релевантных хештегов через пробел в формате #python #telegram_bot #parsing",
  "cover_letter": "Продающее сопроводительное письмо из 2-3 предложений"
}}"""

    url = "https://api.cohere.com/v2/chat"
    headers = {
        "Authorization": f"Bearer {config.COHERE_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": config.COHERE_MODEL,
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ]
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=payload, timeout=20) as response:
                if response.status == 200:
                    data = await response.json()
                    content = ""
                    if "message" in data and "content" in data["message"]:
                        for block in data["message"]["content"]:
                            if block.get("type") == "text":
                                content += block.get("text", "")
                    elif "text" in data:
                        content = data["text"]

                    clean_json = content.strip()
                    clean_json = re.sub(r'^```json\s*', '', clean_json)
                    clean_json = re.sub(r'\s*```$', '', clean_json)

                    parsed = json.loads(clean_json)
                    return {
                        "market_price": parsed.get("market_price", default_result["market_price"]),
                        "difficulty": parsed.get("difficulty", default_result["difficulty"]),
                        "estimated_time": parsed.get("estimated_time", default_result["estimated_time"]),
                        "tech_stack": parsed.get("tech_stack", default_result["tech_stack"]),
                        "ai_tip": parsed.get("ai_tip", default_result["ai_tip"]),
                        "hashtags": parsed.get("hashtags", default_result["hashtags"]),
                        "cover_letter": parsed.get("cover_letter", default_result["cover_letter"])
                    }
                else:
                    return default_result
    except Exception as e:
        logger.error(f"Ошибка при глубоком анализе Cohere: {e}")
        return default_result


async def generate_cover_letter(order_title: str, order_description: str) -> str:
    """Генерирует продающее сопроводительное письмо (совместимость со старым кодом)."""
    deep_data = await analyze_order_deep(order_title, order_description)
    return deep_data.get("cover_letter", "Здравствуйте! Готов качественно выпустить ваш проект.")
