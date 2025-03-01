from __future__ import annotations

import logging
from typing import Any

import aiohttp

from src.constants import INTERNSHIP_LIST_PATH


class InternshipsParser:
    def __init__(self) -> None:
        self.__session: aiohttp.ClientSession | None = None

    async def __aenter__(self) -> InternshipsParser:
        connector = aiohttp.TCPConnector(ssl=False)
        self.__session = aiohttp.ClientSession(
            base_url='https://fut.ru/api/cms/api/',
            connector=connector,
        )
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        if self.__session:
            await self.__session.close()

    async def get_total_data(self) -> dict[str, Any]:
        unique_uuids = set()
        total_data = []

        page = 1
        while True:
            response = await self.get_data_by_page(page)
            data = response['data']

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

    async def get_data_by_page(self, page: int) -> dict[str, Any]:
        if not self.__session:
            raise RuntimeError(
                'Session is not initialized. '
                "Use 'async with' to manage the session."
            )

        async with self.__session.get(
            f'{INTERNSHIP_LIST_PATH}?page={page}'
        ) as response:
            if response.status == 200:
                return await response.json()
            raise Exception(f'Failed to fetch data: {response.status}')
