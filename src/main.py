import logging
from asyncio import run

from constants import BAD_WORDS, INDEX_NAME
from elastic_search import create_index, index_internships, search_internships
from src.parser import InternshipsParser
from utils import remove_bad_words, save_json


async def start_parsing() -> dict:
    async with InternshipsParser() as parser:  # noqa: F821
        parser_result = await parser.get_total_data()

    parser_result = remove_bad_words(parser_result, BAD_WORDS)
    save_json('parser_result.json', parser_result)

    return parser_result


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
                company_data = result["_source"]["company"]
                print(
                    f'- {result["_source"]["title"]} '
                    f'в компании {company_data["caption"]}.'
                    f'\nURL: https://fut.ru/internship/{company_data["alias"]}/{result["_source"]["alias"]}'
                    '\n',
                )
        else:
            logging.info('Результаты не найдены.')


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    logging.getLogger('elastic_transport.transport').setLevel(logging.WARNING)
    main()
