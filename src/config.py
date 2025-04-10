from src.eval.tech_categories import COMMON_TERMS
from src.utils import detect_tech_category

INDEX_SETTINGS = {
    'settings': {
        'analysis': {
            'tokenizer': {
                'standard': {
                    'type': 'standard',
                },
                'ngram_tokenizer': {
                    'type': 'ngram',
                    'min_gram': 3,
                    'max_gram': 4,
                    'token_chars': ['letter', 'digit'],
                },
            },
            'filter': {
                'synonym_filter': {
                    'type': 'synonym',
                    'synonyms_path': 'synonyms.txt',
                },
                'shingle_filter': {
                    'type': 'shingle',
                    'min_shingle_size': 2,
                    'max_shingle_size': 3,
                },
                'russian_stemmer': {'type': 'stemmer', 'language': 'russian'},
                'english_stemmer': {'type': 'stemmer', 'language': 'english'},
            },
            'analyzer': {
                'synonym_analyzer': {
                    'type': 'custom',
                    'tokenizer': 'standard',
                    'filter': [
                        'synonym_filter',
                        'lowercase',
                        'stop',
                        'russian_stemmer',
                        'english_stemmer',
                    ],
                },
                # Анализатор для поиска по частичным совпадениям
                'ngram_analyzer': {
                    'type': 'custom',
                    'tokenizer': 'ngram_tokenizer',
                    'filter': ['lowercase'],
                },
                'shingle_analyzer': {
                    'type': 'custom',
                    'tokenizer': 'standard',
                    'filter': [
                        'lowercase',
                        'shingle_filter',
                        'russian_stemmer',
                        'english_stemmer',
                    ],
                },
            },
        },
        'index': {'max_ngram_diff': 2},
    },
    'mappings': {
        'properties': {
            'title': {
                'type': 'text',
                'analyzer': 'synonym_analyzer',
                'fields': {
                    'ngram': {'type': 'text', 'analyzer': 'ngram_analyzer'},
                    'shingle': {'type': 'text', 'analyzer': 'shingle_analyzer'},
                },
            },
            'description': {
                'type': 'text',
                'analyzer': 'synonym_analyzer',
            },
            'seo_title': {'type': 'text'},
            'seo_description': {'type': 'text'},
            'seo_tags': {'type': 'keyword'},
            'alias': {'type': 'keyword'},
            'publication_status': {'type': 'keyword'},
            'status': {'type': 'keyword'},
            'visibility': {'type': 'keyword'},
            'slogan': {'type': 'text'},
            'tags': {
                'type': 'nested',
                'properties': {
                    'caption': {'type': 'text', 'analyzer': 'synonym_analyzer'},
                    'seo_description': {'type': 'text'},
                    'seo_title': {'type': 'text'},
                    'seo_uri': {'type': 'keyword'},
                },
            },
            'company': {
                'properties': {
                    'caption': {'type': 'text'},
                    'alias': {'type': 'keyword'},
                    'rating': {'type': 'integer'},
                    'description': {
                        'type': 'nested',
                        'properties': {
                            'blocks': {
                                'type': 'nested',
                                'properties': {
                                    'data': {
                                        'type': 'nested',
                                        'properties': {
                                            'text': {
                                                'type': 'text',
                                                'analyzer': 'synonym_analyzer',
                                            },
                                        },
                                    },
                                },
                            },
                        },
                    },
                    'percentages': {'type': 'float'},
                    'directions': {
                        'type': 'nested',
                        'properties': {
                            'caption': {'type': 'text'},
                            'alias': {'type': 'keyword'},
                        },
                    },
                    'industries': {
                        'type': 'nested',
                        'properties': {
                            'name': {
                                'type': 'text',
                            },
                        },
                    },
                },
            },
            'publication_type': {
                'properties': {
                    'name': {'type': 'text'},
                    'alias': {'type': 'keyword'},
                },
            },
            'last_position_end_date': {'type': 'date'},
            'positions': {
                'type': 'nested',
                'properties': {
                    'name': {
                        'type': 'text',
                        'analyzer': 'synonym_analyzer',
                        'fields': {
                            'ngram': {
                                'type': 'text',
                                'analyzer': 'ngram_analyzer',
                            },
                            'shingle': {
                                'type': 'text',
                                'analyzer': 'shingle_analyzer',
                            },
                            'keyword': {'type': 'keyword'},
                        },
                    },
                    'description': {
                        'properties': {
                            'blocks': {
                                'type': 'nested',
                                'properties': {
                                    'type': {'type': 'keyword'},
                                    'data': {
                                        'properties': {
                                            'text': {
                                                'type': 'text',
                                                'analyzer': 'synonym_analyzer',
                                            },
                                            'items': {
                                                'type': 'text',
                                                'analyzer': 'synonym_analyzer',
                                            },
                                        },
                                    },
                                },
                            },
                        },
                    },
                    'status': {'type': 'keyword'},
                    'status_after': {'type': 'keyword'},
                    'field_mode': {'type': 'keyword'},
                    'cities': {
                        'type': 'nested',
                        'properties': {
                            'caption': {'type': 'text'},
                        },
                    },
                    'spheres': {
                        'type': 'nested',
                        'properties': {
                            'caption': {
                                'type': 'text',
                                'analyzer': 'synonym_analyzer',
                            },
                        },
                    },
                    'accepted_registrations_number': {'type': 'integer'},
                    'group': {'type': 'keyword'},
                    'external_link': {'type': 'keyword'},
                },
            },
        },
    },
}


def get_search_body(query: str) -> dict:
    """
    Улучшенная функция поиска с поддержкой различных типов запросов.

    Args:
        query: Поисковый запрос

    Returns:
        Тело запроса к Elasticsearch
    """
    search_body = {
        'query': {
            'function_score': {
                'query': {
                    'bool': {
                        'should': [
                            # Поиск по основным полям документа
                            {
                                'multi_match': {
                                    'query': query,
                                    'fields': [
                                        'title^5',
                                        'title.shingle^4',
                                        'description^3',
                                        'seo_title^3',
                                        'seo_description^2',
                                        'seo_tags',
                                        'alias',
                                        'publication_status',
                                        'slogan',
                                    ],
                                    'fuzziness': 'AUTO',
                                    'operator': 'OR',
                                    'type': 'best_fields',
                                    'tie_breaker': 0.3,
                                },
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
                                        },
                                    },
                                    'score_mode': 'max',
                                },
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
                                        },
                                    },
                                    'score_mode': 'max',
                                },
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
                                        },
                                    },
                                    'score_mode': 'max',
                                },
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
                                },
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
                                },
                            },
                            # Поиск по полям направления
                            {
                                'multi_match': {
                                    'query': query,
                                    'fields': [
                                        'direction.caption',
                                        'direction.alias',
                                    ],
                                    'fuzziness': 'AUTO',
                                },
                            },
                            # Улучшенный поиск по позициям
                            {
                                'nested': {
                                    'path': 'positions',
                                    'query': {
                                        'bool': {
                                            'should': [
                                                # Повышаем значимость названия позиции
                                                {
                                                    'match': {
                                                        'positions.name': {
                                                            'query': query,
                                                            'boost': 10,  # Высокий буст для точного совпадения в названии позиции
                                                            'fuzziness': 'AUTO',
                                                        },
                                                    },
                                                },
                                                # Поиск по n-граммам для частичных совпадений
                                                {
                                                    'match': {
                                                        'positions.name.ngram': {
                                                            'query': query,
                                                            'boost': 6,  # Высокий буст для частичных совпадений
                                                        },
                                                    },
                                                },
                                                # Поиск по шинглам для словосочетаний
                                                {
                                                    'match': {
                                                        'positions.name.shingle': {
                                                            'query': query,
                                                            'boost': 8,  # Высокий буст для словосочетаний
                                                        },
                                                    },
                                                },
                                                # Поиск в описании позиции
                                                {
                                                    'nested': {
                                                        'path': 'positions.description.blocks',
                                                        'query': {
                                                            'bool': {
                                                                'should': [
                                                                    {
                                                                        'match': {
                                                                            'positions.description.blocks.data.text': {
                                                                                'query': query,
                                                                                'boost': 5,
                                                                            },
                                                                        },
                                                                    },
                                                                    {
                                                                        'match': {
                                                                            'positions.description.blocks.data.items': {
                                                                                'query': query,
                                                                                'boost': 5,
                                                                            },
                                                                        },
                                                                    },
                                                                ],
                                                            },
                                                        },
                                                        'score_mode': 'max',
                                                    },
                                                },
                                                # Поиск в сферах позиции
                                                {
                                                    'nested': {
                                                        'path': 'positions.spheres',
                                                        'query': {
                                                            'match': {
                                                                'positions.spheres.caption': {
                                                                    'query': query,
                                                                    'boost': 6,
                                                                },
                                                            },
                                                        },
                                                        'score_mode': 'max',
                                                    },
                                                },
                                            ],
                                        },
                                    },
                                    'score_mode': 'max',
                                    'inner_hits': {},
                                },
                            },
                        ],
                        'minimum_should_match': 1,
                    },
                },
                'functions': [
                    # Бустим стажировки с недавними датами
                    {
                        'exp': {
                            'last_position_end_date': {
                                'scale': '60d',  # Масштаб затухания - 60 дней
                                'offset': '0d',
                                'decay': 0.7,
                            },
                        },
                    },
                ],
                'score_mode': 'multiply',  # Умножаем результаты всех функций
                'boost_mode': 'multiply',  # Умножаем на исходную оценку релевантности
            },
        },
        'sort': [
            '_score',  # Сначала сортируем по релевантности
            {
                'last_position_end_date': {
                    'order': 'asc',
                    'unmapped_type': 'date',
                },
            },
        ],
    }

    tech_categories = detect_tech_category(query)

    if tech_categories:
        query_terms = []
        fields_to_search = [
            'positions.name^10',
            'positions.description.blocks.data.text^5',
            'title^3',
            'description',
        ]

        for tech, terms in tech_categories.items():
            query_terms.append(tech)

            # Проверяем, является ли запрос техническим термином
            is_technical_term = True
            for common_term in COMMON_TERMS:
                if common_term in query.lower():
                    is_technical_term = False
                    break

            # Если запрос - технический термин,
            #   добавляем больше специфичных терминов
            # Если общий - добавляем больше общих категорий
            if is_technical_term:
                specific_terms = [
                    term for term in terms if term not in COMMON_TERMS
                ]
                query_terms.extend(specific_terms[:3])
            else:
                common_terms = [term for term in terms if term in COMMON_TERMS]
                query_terms.extend(common_terms)

        unique_terms = list(set(query_terms))

        search_body['query']['function_score']['functions'].append({
            'filter': {
                'multi_match': {
                    'query': ' '.join(unique_terms),
                    'fields': fields_to_search,
                    'type': 'best_fields',
                    'operator': 'OR',
                },
            },
            'weight': 2.0,
        })

        # Для узкоспециализированных запросов добавляем фильтрацию нерелевантных
        # результатов
        if len(query.split()) <= 2 and any(
            tech in query.lower() for tech in tech_categories.keys()
        ):
            search_body['min_score'] = 1.0

    return search_body
