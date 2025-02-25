import logging
from asyncio import run

from constants import INDEX_NAME
from elastic_search import create_index, index_internships, search_internships
from src.parser import InternshipsParser


async def start_parsing() -> dict:
    async with InternshipsParser() as parser:  # noqa: F821
        return await parser.get_total_data()


def main() -> None:
    # Загрузка данных
    logging.info('Собираем данные по стажировкам...')
    internships_data = run(start_parsing())

    create_index(INDEX_NAME)
    index_internships(internships_data, INDEX_NAME)

    while True:
        query = input('Введите поисковой запрос: ')
        results = search_internships(query, INDEX_NAME)
        if results:
            logging.info(f'Найдено {len(results)} результатов:')
            for result in results:
                logging.info(
                    f'- {result["_source"]["title"]} '
                    f'в компании {result["_source"]["company"]["caption"]}.'
                )
        else:
            logging.info('Результаты не найдены.')


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    main()
