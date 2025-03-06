INDEX_SETTINGS = {
    'settings': {
        'analysis': {
            'tokenizer': {
                'standard': {
                    'type': 'standard',
                },
            },
            'filter': {
                'synonym_filter': {
                    'type': 'synonym',
                    'synonyms_path': 'synonyms.txt',
                },
            },
            'analyzer': {
                'synonym_analyzer': {
                    'type': 'custom',
                    'tokenizer': 'standard',
                    'filter': ['synonym_filter', 'lowercase', 'stop'],
                },
            },
        },
    },
    'mappings': {
        'properties': {
            'title': {'type': 'text'},
            'description': {'type': 'text'},
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
                    'caption': {'type': 'text'},
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
                }
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
                    # 'uuid': {'type': 'keyword'},
                    'name': {'type': 'text'},
                    # 'published_at': {'type': 'date'},
                    # 'unpublished_at': {'type': 'date'},
                    'description': {
                        'properties': {
                            # 'time': {'type': 'long'},
                            'blocks': {
                                'type': 'nested',
                                'properties': {
                                    'type': {'type': 'keyword'},
                                    'data': {
                                        'properties': {
                                            'text': {'type': 'text'},
                                            'items': {'type': 'text'},
                                        },
                                    },
                                },
                            },
                            # 'version': {'type': 'keyword'},
                        },
                    },
                    'status': {'type': 'keyword'},
                    'status_after': {'type': 'keyword'},
                    'field_mode': {'type': 'keyword'},
                    'cities': {
                        'type': 'nested',
                        'properties': {
                            # 'uuid': {'type': 'keyword'},
                            'caption': {'type': 'text'},
                            # 'alias': {'type': 'keyword'},
                            # 'is_custom': {'type': 'boolean'},
                            # 'updated_at': {'type': 'date'},
                            # 'created_at': {'type': 'date'},
                        },
                    },
                    'spheres': {
                        'type': 'nested',
                        'properties': {
                            'caption': {'type': 'text'},
                        },
                    },
                    'accepted_registrations_number': {'type': 'integer'},
                    # 'blocks': {'type': 'nested'},  # Пустой массив в примере
                    'group': {'type': 'keyword'},
                    'external_link': {'type': 'keyword'},
                    # 'tag_from_cms': {
                    #     'type': 'nested',
                    #     'properties': {
                    #         'uuid': {'type': 'keyword'},
                    #         'tag_cms_uuid': {'type': 'keyword'},
                    #     },
                    # },
                },
            },
        },
    },
}


def get_search_body(query: str) -> dict:
    """Генерация тела запроса для поиска с динамическим query"""
    return {
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
                        },
                    },
                ],
                'minimum_should_match': 1,
                # 'filter': [
                #     {
                #         'term': {'status': 'published'}  # ? фильтр по статусу
                #     }
                # ],
            },
        },
        'sort': [
            {
                'last_position_end_date': {
                    'order': 'asc',
                    'unmapped_type': 'date',
                },
            },
        ],
    }


# ELASTIC_SEARCH_BODY = {
#         'query': {
#             'bool': {
#                 'should': [
#                     {
#                         'multi_match': {
#                             'query': query,
#                             'fields': [
#                                 'title^3',
#                                 'description^2',
#                                 'seo_description',
#                                 'status',
#                                 'publication_status',
#                             ],
#                         }
#                     },
#                     {
#                         'nested': {
#                             'path': 'tags',
#                             'query': {
#                                 'multi_match': {
#                                     'query': query,
#                                     'fields': [
#                                         'tags.caption^2',
#                                         'tags.seo_description',
#                                         'tags.seo_title',
#                                         'tags.seo_uri',
#                                     ],
#                                 }
#                             },
#                         }
#                     },
#                     {
#                         'nested': {
#                             'path': 'company.directions',
#                             'query': {
#                                 'multi_match': {
#                                     'query': query,
#                                     'fields': [
#                                         'company.directions.caption',
#                                         'company.directions.alias',
#                                     ],
#                                 }
#                             },
#                         }
#                     },
#                     {
#                         'multi_match': {
#                             'query': query,
#                             'fields': [
#                                 'company.caption^2',
#                                 'company.seo_description',
#                                 'company.seo_title',
#                             ],
#                         }
#                     },
#                     {
#                         'multi_match': {
#                             'query': query,
#                             'fields': ['industry.name^2', 'industry.uuid'],
#                         }
#                     },
#                 ],
#                 'filter': [
#                     {
#                         'term': {'status': 'published'}  # ? фильтр по статусу
#                     }
#                 ],
#             }
#         }
#     }
