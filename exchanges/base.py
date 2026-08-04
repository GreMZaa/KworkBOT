from abc import ABC, abstractmethod
from dataclasses import dataclass
import aiohttp


@dataclass
class Order:
    """Модель данных заказа с фриланс-биржи."""
    title: str          # Заголовок / название заказа
    description: str    # Полное описание задания
    price: str          # Бюджет / стоимость
    deadline: str       # Срок выполнения
    client: str         # Имя / профиль заказчика
    source: str         # Источник ("Kwork" / "Яндекс.Услуги" и др.)
    url: str            # Уникальная ссылка на заказ (служит уникальным идентификатором)


class Exchange(ABC):
    """Абстрактный базовый класс для интеграций с фриланс-биржами."""
    name: str

    @abstractmethod
    async def fetch_orders(self, session: aiohttp.ClientSession) -> list[Order]:
        """
        Получает список свежих заказов с биржи.

        :param session: Активная сессия aiohttp.ClientSession
        :return: Список объектов Order
        """
        pass
