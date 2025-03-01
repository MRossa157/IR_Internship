INDEX_SETTINGS = {
    'mappings': {
        'properties': {
            'title': {'type': 'text'},
            'description': {'type': 'text'},
            'seo_title': {'type': 'text'},
            'seo_description': {'type': 'text'},
            'seo_tags': {'type': 'keyword'},
            'alias': {'type': 'keyword'},
            'publication_status': {'type': 'keyword'},
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
                    # 'description': {'type': 'text'},
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
                }
            },
        }
    }
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
