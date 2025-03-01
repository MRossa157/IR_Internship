import logging
import os

from elasticsearch import Elasticsearch

from config import INDEX_SETTINGS

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
        es.index(index=index_name, id=idx, document=internship)
    logging.info(f'{len(json_data)} документов проиндексировано.')


def search_internships(query, index_name: str):
    """Расширенный поиск стажировок с учетом множества полей и вложенных объектов"""
    body = {
        'query': {
            'bool': {
                'should': [
                    # Поиск по основным полям документа
                    {
                        'multi_match': {
                            'query': query,
                            'fields': [
                                'title^5',
                                'description^3',
                                'seo_title^3',
                                'seo_description^2',
                                'seo_tags',
                                'alias',
                                'publication_status',
                                'slogan',
                            ],
                            'fuzziness': 'AUTO',
                        }
                    },
                    # Поиск по вложенному полю tags
                    {
                        'nested': {
                            'path': 'tags',
                            'query': {
                                'multi_match': {
                                    'query': query,
                                    'fields': [
                                        'tags.caption^4',
                                        'tags.seo_description^2',
                                        'tags.seo_title',
                                        'tags.seo_uri',
                                    ],
                                    'fuzziness': 'AUTO',
                                }
                            },
                        }
                    },
                    # Поиск по вложенным полям company.directions
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
                                    'fuzziness': 'AUTO',
                                }
                            },
                        }
                    },
                    # Поиск по вложенным полям company.industries
                    {
                        'nested': {
                            'path': 'company.industries',
                            'query': {
                                'multi_match': {
                                    'query': query,
                                    'fields': [
                                        'company.industries.name^3',
                                    ],
                                    'fuzziness': 'AUTO',
                                }
                            },
                        }
                    },
                    # Поиск по основным полям компании
                    {
                        'multi_match': {
                            'query': query,
                            'fields': [
                                'company.caption^4',
                                'company.seo_description',
                                'company.seo_title',
                                'company.alias',
                            ],
                            'fuzziness': 'AUTO',
                        }
                    },
                    # Поиск по типу публикации
                    {
                        'multi_match': {
                            'query': query,
                            'fields': [
                                'publication_type.name^2',
                                'publication_type.alias',
                            ],
                            'fuzziness': 'AUTO',
                        }
                    },
                    # Поиск по полям направления
                    {
                        'multi_match': {
                            'query': query,
                            'fields': ['direction.caption', 'direction.alias'],
                            'fuzziness': 'AUTO',
                        }
                    },
                ],
                'minimum_should_match': 1,
            }
        }
    }

    response = es.search(index=index_name, body=body)
    return response['hits']['hits']
