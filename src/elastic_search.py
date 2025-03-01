import logging
import os

from elasticsearch import Elasticsearch

from config import INDEX_SETTINGS, get_search_body
from utils import convert_to_iso_format

es = Elasticsearch(os.getenv('ELASTICSEARCH_URL'))


def create_index(index_name: str) -> None:
    """Создание индекса в Elasticsearch"""
    if not es.indices.exists(index=index_name):
        es.indices.create(index=index_name, body=INDEX_SETTINGS)
        logging.info('Индекс создан.')
    else:
        logging.warning('Индекс уже существует.')


def index_internships(json_data: dict, index_name: str) -> None:
    """Индексирование данных о стажировках"""
    for idx, internship in enumerate(json_data):
        internship['last_position_end_date'] = convert_to_iso_format(
            internship['last_position_end_date'],
        )
        es.index(index=index_name, id=idx, document=internship)
    logging.info(f'{len(json_data)} документов проиндексировано.')


def search_internships(query, index_name: str):
    """
    Расширенный поиск стажировок с учетом множества полей и вложенных объектов
    """
    body = get_search_body(query)
    response = es.search(index=index_name, body=body)
    return response['hits']['hits']
