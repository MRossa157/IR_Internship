import logging
import os
from asyncio import run
from parser import start_parsing

from constants import INDEX_NAME, PARSER_RESULT_FILENAME
from elastic_search import create_index, index_internships, search_internships
from utils import load_json, print_search_result


def main() -> None:
    if os.path.exists(PARSER_RESULT_FILENAME):
        logging.info('Берем сохраненные данные по стажировкам')
        internships_data = load_json(PARSER_RESULT_FILENAME)
    else:
        logging.info('Собираем данные по стажировкам...')
        internships_data = run(start_parsing())

    create_index(INDEX_NAME)
    index_internships(internships_data, INDEX_NAME)

    if input('Хотите использовать BERT для поиска? (y/n): ').lower() == 'y':
        logging.info('Загружаем BERT...')
        from bert.model import BERTSearchEngine

        checkpoint_path = input('Укажите путь до веса модели: ')
        bert_wrapper = BERTSearchEngine(
            model=BERTSearchEngine.serialize_model_from_checkpoint(
                checkpoint_path=checkpoint_path,
            ),
        )
        search_engine = bert_wrapper.find_internships
    else:
        search_engine = search_internships

    while True:
        query = input('\nВведите поисковой запрос (или "exit" для выхода): ')

        if query.lower() == 'exit':
            break

        results = search_engine(query, INDEX_NAME)

        if results:
            logging.info(f'Найдено {len(results)} результатов:')
            for idx, result in enumerate(results):
                print(f'{idx}. ', end='')
                print_search_result(result)
        else:
            logging.info('Результаты не найдены.')


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    logging.getLogger('elastic_transport.transport').setLevel(logging.WARNING)
    main()
