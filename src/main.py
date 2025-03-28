import logging
import os
from asyncio import run

from constants import BAD_WORDS, INDEX_NAME, PARSER_RESULT_FILENAME
from elastic_search import create_index, index_internships, search_internships
from src.parser import InternshipsParser
from utils import load_json, print_search_result, remove_bad_words, save_json


async def start_parsing() -> dict:
    async with InternshipsParser() as parser:  # noqa: F821
        parser_result = await parser.get_total_data()

    parser_result = remove_bad_words(parser_result, BAD_WORDS)
    save_json(PARSER_RESULT_FILENAME, parser_result)

    return parser_result


def main() -> None:
    if os.path.exists(PARSER_RESULT_FILENAME):
        logging.info('Берем сохраненные данные по стажировкам')
        internships_data = load_json(PARSER_RESULT_FILENAME)
    else:
        logging.info('Собираем данные по стажировкам...')
        internships_data = run(start_parsing())

    create_index(INDEX_NAME)
    index_internships(internships_data, INDEX_NAME)

    while True:
        query = input('\nВведите поисковой запрос (или "exit" для выхода): ')

        if query.lower() == 'exit':
            break

        results = search_internships(query, INDEX_NAME)

        if results:
            logging.info(f'Найдено {len(results)} результатов:')
            for idx, result in enumerate(results):
                print(f"{idx}. ", end="")
                print_search_result(result)
        else:
            logging.info('Результаты не найдены.')


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    logging.getLogger('elastic_transport.transport').setLevel(logging.WARNING)
    main()
