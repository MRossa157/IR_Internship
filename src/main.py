import argparse
import logging

from constants import INDEX_NAME
from elastic_search import create_index, index_internships, search_internships
from src.parser import InternshipsParser
from utils import load_json, save_json


async def start_parsing() -> dict:
    async with InternshipsParser() as parser:  # noqa: F821
        return await parser.get_total_data()


def main() -> None:
    parser = argparse.ArgumentParser(
        description='Поиск стажировок в Elasticsearch.'
    )
    parser.add_argument(
        '--index', action='store_true', help='Индексировать данные из файла.'
    )
    parser.add_argument(
        '--search', type=str, help='Поиск стажировок по запросу.'
    )
    parser.add_argument(
        '--file',
        type=str,
        required=True,
        help='Путь к файлу с данными о стажировках (JSON).',
    )

    args = parser.parse_args()

    # Загрузка данных
    if args.file:
        try:
            internships_data = load_json(args.file)
        except FileNotFoundError:
            logging.error(  # noqa: TRY400
                f'Файл {args.file} не найден. '
                'Если у вас нет файла, то запуститесь без флага "--file".'
            )
            raise
    else:
        from asyncio import run
        internships_data = run(start_parsing())
        save_json('parser_results.json', data=internships_data)

    if args.index:
        create_index(INDEX_NAME)
        index_internships(internships_data, INDEX_NAME)

    if args.search:
        results = search_internships(args.search, INDEX_NAME)
        if results:
            print(f'Найдено {len(results)} результатов:')
            for result in results:
                print(
                    f'- {result["_source"]["title"]} в компании {result["_source"]["company"]}'
                )
        else:
            print('Результаты не найдены.')


if __name__ == '__main__':
    main()
