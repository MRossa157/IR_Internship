from __future__ import annotations

import asyncio
import logging
from typing import Any

import aiohttp

from src.constants import EVENTS_LIST_PATH, INTERNSHIP_LIST_PATH


class InternshipsParser:
    def __init__(self) -> None:
        self.__session: aiohttp.ClientSession | None = None

    async def get_total_data(self) -> dict[str, Any]:
        unique_uuids = set()
        total_data = []

        page = 1
        while True:
            data = await self.get_data_by_page(page)
            current_page_uuids: set = {row['uuid'] for row in data}
            new_uuids = current_page_uuids - unique_uuids
            if not new_uuids:
                break
            unique_uuids.update(current_page_uuids)

            logging.info(
                f'Новые найденные стажировки, на странице {page}: '
                f'{len(new_uuids)} (всего {len(unique_uuids)})',
            )
            total_data.extend(data)
            page += 1

        return total_data

    async def get_data_by_page(self, page: int) -> list[dict[str, Any]]:
        result = await self.__send_request(
            f'{INTERNSHIP_LIST_PATH}?page={page}',
        )
        result = result['data']

        if not result:
            return result

        tasks = []
        for item in result:
            task = asyncio.create_task(self.__get_positions_data(item))
            tasks.append(task)

        await asyncio.gather(*tasks, return_exceptions=True)

        return result

    async def __get_positions_data(self, item: dict[str, Any]) -> None:
        """Приватный метод для получения данных о событии и добавления их в исходный элемент"""
        try:
            event_data = await self.__send_request(
                f'{EVENTS_LIST_PATH}/{item["event"]}',
            )
            item['positions'] = event_data['data']['positions']
        except Exception as e:
            item['positions'] = None

    async def __aenter__(self) -> InternshipsParser:
        connector = aiohttp.TCPConnector(ssl=False)
        self.__session = aiohttp.ClientSession(
            connector=connector,
        )
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        if self.__session:
            await self.__session.close()

    async def __send_request(self, uri: str) -> dict[str, Any]:
        """
        Приватный метод для отправки запросов

        Args:
            uri: URI для запроса

        Returns:
            dict[str, Any]: Ответ в формате JSON

        Raises:
            RuntimeError: Если сессия не инициализирована
            Exception: Если запрос не удался
        """
        if not self.__session:
            raise RuntimeError(
                'Session is not initialized. '
                "Use 'async with' to manage the session."
            )

        async with self.__session.get(uri) as response:
            if response.status == 200:
                return await response.json()
            raise Exception(f'Failed to fetch data: {response.status}')