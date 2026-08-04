import re
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

    :param order_title: Название заказа
    :param order_description: Описание заказа
    :return: Кортеж (is_scam: bool, reason: str)
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


async def generate_cover_letter(order_title: str, order_description: str) -> str:
    """
    Генерирует продающее сопроводительное письмо (Cover Letter) для заказа на основе навыков фрилансера.
    """
    if not config.COHERE_API_KEY:
        return "Здравствуйте! Готов качественно и в срок выполнить ваш заказ. Занимаюсь разработкой на Python, веб-сервисов и ботов. Обращайтесь!"

    skills = config.MY_SKILLS
    prompt = f"""Ты — профессиональный фрилансер. Напиши короткий, убедительный и вежливый отклик (сопроводительное письмо) заказчику на проект.

Мои навыки: {skills}

Заказ:
Заголовок: {order_title}
Описание: {order_description}

Требования к отклику:
1. Максимально емкий (2-4 предложения).
2. Покажи понимание задачи и подчеркни релевантный опыт.
3. Без воды, клише и здоровайся уважительно.
4. Напиши отклик на русском языке."""

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

                    return content.strip()
                else:
                    return "Здравствуйте! Ознакомился с вашим заданием. Имею большой опыт разработки на Python и готов выполнить проект в сжатые сроки."
    except Exception as e:
        logger.error(f"Ошибка при генерации отклика: {e}")
        return "Здравствуйте! Готов взяться за реализацию вашего проекта. Опыт в разработке аналогичных решений имеется. Давайте обсудим детали!"
