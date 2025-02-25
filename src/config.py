INDEX_SETTINGS = {
    'mappings': {
        'properties': {
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
                    'directions': {
                        'type': 'nested',
                        'properties': {
                            'caption': {'type': 'text'},
                            'alias': {'type': 'keyword'},
                        },
                    },
                }
            },
            'industry': {
                'properties': {
                    'name': {'type': 'text'},
                    'uuid': {'type': 'keyword'},
                }
            },
        }
    }
}
