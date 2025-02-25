import logging

from elasticsearch import Elasticsearch

from config import INDEX_SETTINGS

es = Elasticsearch('http://localhost:9200')


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
        es.index(index=index_name, id=idx, document=internship)
    logging.info(f'{len(json_data)} документов проиндексировано.')


def search_internships(query, index_name: str):
    """Поиск стажировок по запросу, учитывая вложенные поля"""
    body = {
        'query': {
            'bool': {
                'should': [
                    {
                        'multi_match': {
                            'query': query,
                            'fields': [
                                'title^3',
                                'description^2',
                                'seo_description',
                                'status',
                                'publication_status',
                            ],
                        }
                    },
                    {
                        'nested': {
                            'path': 'tags',
                            'query': {
                                'multi_match': {
                                    'query': query,
                                    'fields': [
                                        'tags.caption^2',
                                        'tags.seo_description',
                                        'tags.seo_title',
                                        'tags.seo_uri',
                                    ],
                                }
                            },
                        }
                    },
                    {
                        'nested': {
                            'path': 'company.directions',
                            'query': {
                                'multi_match': {
                                    'query': query,
                                    'fields': [
                                        'company.directions.caption',
                                        'company.directions.alias',
                                    ],
                                }
                            },
                        }
                    },
                    {
                        'multi_match': {
                            'query': query,
                            'fields': [
                                'company.caption^2',
                                'company.seo_description',
                                'company.seo_title',
                            ],
                        }
                    },
                    {
                        'multi_match': {
                            'query': query,
                            'fields': ['industry.name^2', 'industry.uuid'],
                        }
                    },
                ],
                'filter': [
                    {
                        'term': {'status': 'published'}  # ? фильтр по статусу
                    }
                ],
            }
        }
    }

    response = es.search(index=index_name, body=body)
    return response['hits']['hits']
