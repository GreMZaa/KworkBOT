import re
import logging
import aiohttp
import config

logger = logging.getLogger(__name__)


async def evaluate_relevance(order_title: str, order_description: str) -> int:
    """
    Оценивает релевантность заказа навыкам пользователя с помощью Cohere API.

    :param order_title: Название заказа
    :param order_description: Описание заказа
    :return: Процент релевантности (0–100)
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
                    # В Cohere API v2 ответ содержится в message.content[0].text
                    content = ""
                    if "message" in data and "content" in data["message"]:
                        for block in data["message"]["content"]:
                            if block.get("type") == "text":
                                content += block.get("text", "")
                    elif "text" in data:
                        content = data["text"]

                    # Извлекаем число от 0 до 100 из ответа
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
